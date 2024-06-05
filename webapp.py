import os
import glob
import csv
import time
import webbrowser
from threading import Timer
import numpy as np
import torch
import librosa
from flask import Flask, render_template, request, jsonify
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
csv_file = "music_characteristics.csv"
TIMEOUT = 60
XX = 20
HR = 0  # Global variable that will store heart rate

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

# Route for the main page
@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

# Function to get music files
def get_music_files():
    rootpath = "/Users/jeremyjohn/Desktop/music"
    pattern = "*.mp3"
    files = glob.glob(os.path.join(rootpath, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': file} for file in files]

# Function to load audio segment
def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

# Function to compute tempo
def compute_tempo(audioInfo, samplingRate):
    try:
        tempo, _ = librosa.beat.beat_track(y=audioInfo, sr=samplingRate)
        return float(tempo)
    except Exception as e:
        print(f"Error computing tempo: {e}")
        return None

# Function to compute average pitch
def compute_average_pitch(audioInfo, samplingRate):
    try:
        pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
        return float(np.mean(pitches[pitches > 0]))
    except Exception as e:
        print(f"Error computing pitch: {e}")
        return None

# Function to get the (get characteristics) of a music file
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

# Function to generate the CSV with audio characteristics
def generate_csv(directory_path, csv_file):
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Song Length", "Average Tempo", "Tempo First 30s", "Tempo Last 30s", "Average Pitch", "Pitch First 30s", "Pitch Last 30s"])
        
        for audio_file in audio_files:
            if os.path.isfile(audio_file):
                print(f"Processing file: {audio_file}")
                characteristics = get_characteristics(audio_file)
                if characteristics and any(c is not None for c in characteristics):
                    print("Here are the file characteristics")
                    print(characteristics)
                    writer.writerow([os.path.basename(audio_file)] + characteristics)
                    print(f"Characteristics for {audio_file}: {characteristics}")
                else:
                    print(f"Skipping file due to processing errors: {audio_file}")
            else:
                print(f"Skipping directory: {audio_file}")

# Function to get the user's current heart rate (both resting and current)
def get_heart_rate(device_id=0):
    HR = 0
    while True:
        try:
            node = Node()
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            device = HeartRate(node, device_id=device_id)
            break
        except Exception as e:
            print("Failed to initialize node, trying again!")

    def on_found():
        print(f"Device {device} found and receiving")

    def on_device_data(page: int, page_name: str, data):
        nonlocal HR
        if isinstance(data, HeartRateData):
            print(data.heart_rate)
            HR = data.heart_rate
            device.on_device_data = None  # Unregister the callback function

    device.on_found = on_found
    device.on_device_data = on_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except Exception as e:
        print("Closing ANT+ device...")
    finally:
        device.close_channel()
        node.stop()

    return HR

# Function to get the user's current resting heart rate
def get_resting_HR(device_id=0):
    TIMEOUT = 60
    start_time = time.time()
    heart_rates = []
    resting_heart_rate = None
    node = None
    device = None

    while True:
        try:
            node = Node()
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            device = HeartRate(node, device_id=device_id)
            break
        except Exception as e:
            print("Failed to initialize node, trying again!")

    def on_found():
        print(f"Device {device} found and receiving")

    def on_device_data(page: int, page_name: str, data):
        nonlocal TIMEOUT
        nonlocal start_time
        nonlocal heart_rates
        nonlocal resting_heart_rate  

        if isinstance(data, HeartRateData):
            current_rate = data.heart_rate
            print(f"Heart rate update {current_rate} bpm")
            heart_rates.append(current_rate)
            print(heart_rates)
            if len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3:
                resting_heart_rate = int(np.mean(heart_rates))  
                device.close_channel()
                node.stop()
            
            if (time.time() - start_time) >= TIMEOUT:
                resting_heart_rate = -1  
                device.close_channel()
                node.stop()

    device.on_found = on_found
    device.on_device_data = on_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except KeyboardInterrupt:
        print("Closing ANT+ device...")
    finally:
        if device:
            try:
                device.close_channel()
            except Exception as e:
                print(f"Error closing device channel: {e}")
        if node:
            try:
                node.stop()
            except Exception as e:
                print(f"Error stopping node: {e}")

    return resting_heart_rate

# This function selects music based on heart rate reading 
def selectMusic(targetHR, heartRate, restingHR, csvLocation):
    targetHR = int(targetHR)
    heartRate = int(heartRate)
    restingHR = int(restingHR)

    goalHRChange = targetHR - heartRate
    print(f"Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}, Goal HR Change: {goalHRChange}")
    
    with open(csvLocation, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    
    if len(rows) <= 1:
        print("No data available in the CSV file.")
        return None

    header = rows[0]
    rows = rows[1:]  # Skip the header row and only record the information
    
    best_song = None
    best_prediction = None
    
    for musicRow in rows:
        try:
            song_data = [float(musicRow[i]) for i in range(1, len(musicRow))]
            song_data.append(heartRate)
            song_data.append(restingHR)
            song_tensor = torch.tensor(song_data, dtype=torch.float32)
            prediction = model(song_tensor).item()
            print(f"Song: {musicRow[0]}, Prediction: {prediction}")

            if best_song is None or (
                (goalHRChange > 0 and prediction > best_prediction) or
                (goalHRChange <= 0 and prediction < best_prediction)
            ):
                best_song = musicRow[0]
                best_prediction = prediction
                
        except Exception as e:
            print(f"Error selecting music for row {musicRow}: {e}")
    
    print(f"Selected Song: {best_song}, Prediction: {best_prediction}")
    return best_song

# Route that starts heart rate monitoring for resting heart rate
@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = get_resting_HR()
    return jsonify({"hr": hr, "type": "resting"})

# Route that starts heart rate monitoring for current heart rate
@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = get_heart_rate()
    return jsonify({"hr": hr, "type": "current"})

# Route to get music recommendations from heart rate
@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    print(f"Received request: Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}")
    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, heartRate, restingHR, csvLocation)
    return jsonify({'selected_music': selected_music})

if __name__ == "__main__":
    directory_path = "/Users/jeremyjohn/Desktop/music"
    
    # Generate CSV file with the added audio characteristics
    generate_csv(directory_path, csv_file)

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    # Start a timer to open the browser
    Timer(1, open_browser).start()
    
    # Start the Flask application
    app.run(port=5000, debug=True)


