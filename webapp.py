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
from GetHeartRate import HeartRateReader
from selectMusic import selectMusic
from GetCharacteristics import get_characteristics

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

# Initialize the HeartRateReader class
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
    restingHR = data['restingHR']
    approachPath = data.get('approachPath')

    # Get the current heart rate
    currentHR = HR.get_heart_rate_int()

    print(f"Received request: Target HR: {targetHR}, Current HR: {currentHR}, Resting HR: {restingHR}, Approach Path: {approachPath}")

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

def generate_csv(directory_path, csv_file):
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    
    with open(csv_file, mode='w', newline='') as file):
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
    
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()
    
    app.run(port=5000)




