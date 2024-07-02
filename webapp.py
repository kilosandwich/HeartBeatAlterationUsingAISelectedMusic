import os
import glob
import csv
import time
import webbrowser
from threading import Timer, Thread
import numpy as np
import torch
import librosa
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_bootstrap import Bootstrap
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from ModelDefinition import SimpleNN  # Ensure to import your model class

# Initialize Flask app and Bootstrap
app = Flask(__name__)
Bootstrap(app)

# Global variables and constants
script_dir = os.path.dirname(os.path.abspath(__file__))
music_dir = os.path.join(script_dir, "static/music")
csv_file = os.path.join(script_dir, "music_characteristics.csv")
TIMEOUT = 60
HR = 0  # Global variable that will store heart rate

if not os.path.exists(music_dir):
    os.makedirs(music_dir)

# Define the model
input_size = 9
hidden_size = 10
output_size = 1
learning_rate = 0.01
dropout_prob = 0.1

model_path = os.path.join(script_dir, "HBModel.pth")

# Load the model
model = SimpleNN(input_size, hidden_size, output_size, dropout_prob)
try:
    model.load_state_dict(torch.load(model_path))
    model.eval()
    print("Model loaded and set to evaluation mode.")
except Exception as e:
    print(f"Error loading model: {e}")

## HeartRateReader Class
#this is the heaert rate reader class as well as the updated routes
class HeartRateReader:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.HR = 0
        self.resting_heart_rate = None
        self.node = None
        self.device = None
        self.heart_rates = []
        self.thread = Thread(target=self.init_device)
        self.thread.start()

    def init_device(self):
        while True:
            try:
                self.node = Node()
                self.node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
                self.device = HeartRate(self.node, device_id=self.device_id)
                break
            except Exception as e:
                print("Failed to initialize node, trying again!")

        self.device.on_found = self.on_found
        self.device.on_device_data = self.on_device_data
        try:
            print(f"Starting {self.device}, press Ctrl-C to finish")
            self.node.start()
        except Exception as e:
            print("Closing ANT+ device...")
        finally:
            self.device.close_channel()
            self.node.stop()

    def on_found(self):
        print(f"Device {self.device} found and receiving")

    def on_device_data(self, page: int, page_name: str, data):
        if isinstance(data, HeartRateData):
            print(data.heart_rate)
            self.HR = data.heart_rate
            self.heart_rates.append(data.heart_rate)
            if len(self.heart_rates) > 1 and (max(self.heart_rates) - min(self.heart_rates)) <= 3:
                self.resting_heart_rate = int(np.mean(self.heart_rates))

    def get_heart_rate_int(self):
        return self.HR

    def get_resting_heart_rate(self, timeout=60):
        start_time = time.time()
        self.heart_rates = []
        self.resting_heart_rate = None

        while (time.time() - start_time) < timeout:
            if self.resting_heart_rate is not None:
                return self.resting_heart_rate
            time.sleep(1)  # Sleep to prevent tight loop

        return -1  

# Initialize the HeartRateReader class
#these are the new for the resting heart rate and current heart rate
HR = HeartRateReader()

@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = HR.get_resting_heart_rate()
    return jsonify({"hr": hr, "type": "resting"})

@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = HR.get_heart_rate_int()
    return jsonify({"hr": hr, "type": "current"})

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    targetHR = data['targetHR']

    # Get the current heart rate
    currentHR = HR.get_heart_rate_int()

    # Get the resting heart rate from feed
    restingHR = HR.get_resting_heart_rate()

    print(f"Received request: Target HR: {targetHR}, Current HR: {currentHR}, Resting HR: {restingHR}")

    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, currentHR, restingHR, csvLocation)

    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})


# Route for the main page
@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

# Function to get music files
def get_music_files():
    pattern = "*.mp3"
    files = glob.glob(os.path.join(music_dir, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': f'/music/{os.path.basename(file)}'} for file in files]

def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

def compute_tempo(audioInfo, samplingRate):
    try:
        tempo, _ = librosa.beat.beat_track(y=audioInfo, sr=samplingRate)
        return float(tempo)
    except Exception as e:
        print(f"Error computing tempo: {e}")
        return None

def compute_average_pitch(audioInfo, samplingRate):
    try:
        pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
        return float(np.mean(pitches[pitches > 0]))
    except Exception as e:
        print(f"Error computing pitch: {e}")
        return None

def get_characteristics(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: {filepath} is not a file.")
        return [None] * 7

    try:
        y, samplingRate = librosa.load(filepath)
        songLength = librosa.get_duration(y=y, sr=samplingRate)
        avgTempo = compute_tempo(y, samplingRate)
        first_30s_audio = load_audio_segment(y, samplingRate, 0, 30)
        last_30s_audio = load_audio_segment(y, samplingRate, max(0, songLength - 30), 30)
        tempo_first_30 = compute_tempo(first_30s_audio, samplingRate)
        tempo_last_30 = compute_tempo(last_30s_audio, samplingRate)
        avgPitch = compute_average_pitch(y, samplingRate)
        pitch_first_30 = compute_average_pitch(first_30s_audio, samplingRate)
        pitch_last_30 = compute_average_pitch(last_30s_audio, samplingRate)

        return [
            songLength,
            avgTempo,
            tempo_first_30,
            tempo_last_30,
            avgPitch,
            pitch_first_30,
            pitch_last_30
        ]
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return [None] * 7

def generate_csv(directory_path, csv_file):
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Song Length", "Average Tempo", "Tempo First 30s", "Tempo Last 30s", "Average Pitch", "Pitch First 30s", "Pitch Last 30s"])
        print("I am attempting to write to: ", csv_file)
        for audio_file in audio_files:
            print(f"Processing file: {audio_file}")
            characteristics = get_characteristics(audio_file)
            print("Here are the file characteristics")
            print(characteristics)
            musicFilePath = str(os.path.basename(audio_file))
            rowToWrite = characteristics.copy()
            rowToWrite.insert(0, musicFilePath)
            print("This is the row we are attempting to write: ", rowToWrite)
            writer.writerow(rowToWrite)
            print(f"Characteristics for {audio_file}: {characteristics}")

def selectMusic(targetHR, heartRate, restingHR, csvLocation):
    targetHR = int(targetHR)
    heartRate = int(heartRate)
    restingHR = int(restingHR)

    goalHRChange = targetHR - heartRate

    with open(csvLocation, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    del rows[0]  # Remove the header row

    currentSong = [rows[0][0], 0]  # Initialize with the first song and a neutral value
    for musicRow in rows:
        try:
            tempList = [float(musicRow[i]) for i in range(1, len(musicRow))]
            tempList.append(heartRate)
            tempList.append(restingHR)
            tempTensor = torch.tensor(tempList, dtype=torch.float32)
            tempPrediction = model(tempTensor).item()  # Get the prediction from the model
            print(f"Song: {musicRow[0]}, Prediction: {tempPrediction}")
            tempPrediction = [musicRow[0], tempPrediction]
            if goalHRChange > 0:
                if tempPrediction[1] > currentSong[1]:
                    currentSong = tempPrediction.copy()  # Select song that increases HR
            else:
                if tempPrediction[1] < currentSong[1]:
                    currentSong = tempPrediction.copy()  # Select song that decreases HR
        except Exception as e:
            print(f"Error selecting music for row {musicRow}: {e}")
    print(f"Selected Song: {currentSong[0]}, Prediction: {currentSong[1]}")
    return currentSong[0]

@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    print(f"Received request: Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}")
    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, heartRate, restingHR, csvLocation)
    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

@app.route('/music/<filename>')
def play_music(filename):
    return send_from_directory(music_dir, filename)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user_guide')
def user_guide():
    return render_template('user_guide.html')

@app.route('/advanced_features')
def advanced_features():
    return render_template('advanced_features.html')

if __name__ == "__main__":
    directory_path = os.path.join(script_dir, "/Users/jeremyjohn/Desktop/music")
    csv_file = os.path.join(script_dir, csv_file)
    generate_csv(directory_path, csv_file)

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    Timer(1, open_browser).start()
    
    app.run(port=5000, debug=True)




