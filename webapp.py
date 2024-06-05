from flask import Flask, render_template, request, jsonify
import os
import glob
import csv
import time
import webbrowser
from threading import Timer
import numpy as np
import torch
import librosa
from flask_bootstrap import Bootstrap
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from ModelDefinition import SimpleNN

app = Flask(__name__)
Bootstrap(app)

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = "music_characteristics.csv"
TIMEOUT = 60
XX = 20
HR = 0

input_size = 9
hidden_size = 10
output_size = 1
learning_rate = 0.01
dropout_prob = 0.1

model_path = os.path.join(script_dir, "HBModel.pth")

model = SimpleNN(input_size, hidden_size, output_size, dropout_prob)
try:
    model.load_state_dict(torch.load(model_path))
    model.eval()
    print("Model loaded and set to evaluation mode.")
except Exception as e:
    print(f"Error loading model: {e}")

@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

def get_music_files():
    rootpath = r"C:\Users\ahmad\OneDrive\Desktop\Project\HeartBeatAlterationUsingAISelectedMusic-main\music"
    pattern = "*.mp3"
    files = glob.glob(os.path.join(rootpath, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': file} for file in files]

def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

def compute_tempo(audioInfo, samplingRate):
    try:
        tempo, _ = librosa.beat.beat_track(y=audioInfo, sr=samplingRate)
        return tempo
    except Exception as e:
        print(f"Error computing tempo: {e}")
        return None

def compute_average_pitch(audioInfo, samplingRate):
    try:
        pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
        return np.mean(pitches[pitches > 0])
    except Exception as e:
        print(f"Error computing pitch: {e}")
        return None

def get_characteristics(filepath):
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
        pitch_last_30 = compute_average_pitch(last_30s_audio,_samplingRate)

        return [
            avgTempo,
            tempo_first_30,
            tempo_last_30,
            songLength,
            pitch_first_30,
            pitch_last_30,
            avgPitch
        ]
    except Exception as e:
        print(f"Error getting characteristics for {filepath}: {e}")
        return [None] * 7

def generate_csv(directory_path, csv_file):
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Song Length", "Average Tempo", "Tempo First 30s", "Tempo Last 30s", "Average Pitch", "Pitch First 30s", "Pitch Last 30s"])
        
        for audio_file in audio_files:
            print(f"Processing file: {audio_file}")
            characteristics = get_characteristics(audio_file)
            print("Here are the file characteristics")
            print(characteristics)
            writer.writerow([os.path.basename(audio_file)] + characteristics)
            print(f"Characteristics for {audio_file}: {characteristics}")

def get_resting_HR():
    start_time = time.time()
    heart_rates = []

    while time.time() - start_time < TIMEOUT:
        current_rate = get_current_heart_rate()
        heart_rates.append(current_rate)

        if len(heart_rates) > 1 and (max(heart_rates) - min(heart_rates)) <= 3:
            return int(np.mean(heart_rates))

        time.sleep(XX)

    return -1

def get_current_heart_rate(device_id=0):
    global HR
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
        global HR
        if isinstance(data, HeartRateData):
            print(data.heart_rate)
            HR = data.heart_rate

    device.on_found = on_found
    device.on_device_data = on_device_data

    try:
        print(f"Starting {device}, press Ctrl-C to finish")
        node.start()
    except Exception as e:
        print(f"Error with ANT+ device: {e}")
    finally:
        device.close_channel()
        node.stop()
    return HR

def selectMusic(targetHR, heartRate, restingHR, csvLocation):
    targetHR = int(targetHR)
    heartRate = int(heartRate)
    restingHR = int(restingHR)

    goalHRChange = targetHR - heartRate
    print(f"Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}, Goal HR Change: {goalHRChange}")
    
    with open(csvLocation, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
    del rows[0]
    
    currentSong = [rows[0][0], 0]
    for musicRow in rows:
        try:
            tempList = [float(musicRow[i]) for i in range(1, len(musicRow))]
            tempList.append(heartRate)
            tempList.append(restingHR)
            tempTensor = torch.tensor(tempList, dtype=torch.float32)
            tempprediction = model(tempTensor).tolist()[0]
            print(f"Song: {musicRow[0]}, Prediction: {tempprediction}")
            tempprediction = [musicRow[0], tempprediction]
            if goalHRChange > 0:
                if tempprediction[1] > currentSong[1]:
                    currentSong = tempprediction.copy()
            else:
                if tempprediction[1] < currentSong[1]:
                    currentSong = tempprediction.copy()
        except Exception as e:
            print(f"Error selecting music for row {musicRow}: {e}")
    print(f"Selected Song: {currentSong[0]}, Prediction: {currentSong[1]}")
    return currentSong[0]

@app.route("/start_hr_monitor", methods=["GET"])
def start_hr_monitor():
    hr = get_resting_HR()
    return jsonify({"hr": hr})

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
    directory_path = r"C:\Users\ahmad\OneDrive\Desktop\Project\HeartBeatAlterationUsingAISelectedMusic-main\music"
    
    generate_csv(directory_path, csv_file)

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    Timer(1, open_browser).start()
    
    app.run(port=5000, debug=True)
