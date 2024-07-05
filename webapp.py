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
from werkzeug.utils import secure_filename
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from ModelDefinition import SimpleNN  # Ensure to import your model class
from GetHeartRate import HeartRateReader
from selectMusic import selectMusic
from GetCharacteristics import get_characteristics
from GenerateCSV import generate_csv

# Initialize Flask app and Bootstrap
app = Flask(__name__)
Bootstrap(app)

# Global variables and constants
script_dir = os.path.dirname(os.path.abspath(__file__))
music_dir = os.path.join(script_dir, "music")
csv_file = os.path.join(script_dir, "music_characteristics.csv")
TIMEOUT = 60
HR = 0  # Global variable that will store heart rate

if not os.path.exists(music_dir):
    os.makedirs(music_dir)

# Initialize the HeartRateReader class
HR = HeartRateReader()
ALLOWED_EXTENSIONS = {'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(music_dir, filename))
        
        # Regenerate the CSV file after uploading new files
        generate_csv(music_dir, csv_file)
        print("CSV file has been regenerated.")
        
        return jsonify({'success': 'File uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = HR.get_resting_heart_rate()
    return jsonify({"hr": hr, "type": "resting"})

@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = HR.get_heart_rate_int()
    return jsonify({"hr": hr, "type": "current"})

@app.route("/get_approach_path_message", methods=["POST"])
def get_approach_path_message():
    data = request.json
    approachPath = data.get('approachPath', 'SHALLOW')
    message = process_approach_path(approachPath)
    return jsonify({'message': message})

def process_approach_path(approach_path):
    if approach_path == 'random':
        return "You chose random approach path"
    if approach_path == 'SHALLOW':
        return "You chose SHALLOW approach path"
    elif approach_path == 'LINEAR':
        return "You chose LINEAR approach path"
    elif approach_path == 'STEEP':
        return "You chose STEEP approach path"
    elif approach_path == 'Parabola':
        return "You chose Parabola approach path"
    elif approach_path == 'Rollercoaster':
        return "You chose Rollercoaster approach path"
    else:
        return "Unknown approach path"

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    targetHR = int(data['targetHR'])
    restingHR = int(data['restingHR'])
    approachPath = data.get('approachPath', 'SHALLOW')

    # Get the current heart rate
    currentHR = HR.get_heart_rate_int()

    print(f"Received request: Target HR: {targetHR}, Current HR: {currentHR}, Resting HR: {restingHR}, Approach Path: {approachPath}")

    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, currentHR, restingHR, csvLocation)

    approach_messages = {
        "SHALLOW": process_approach_path("SHALLOW"),
        "LINEAR": process_approach_path("LINEAR"),
        "STEEP": process_approach_path("STEEP"),
        "Parabola": process_approach_path("Parabola"),
        "Rollercoaster": process_approach_path("Rollercoaster")
    }

    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({**approach_messages, 'selected_music': music_path})
    return jsonify({**approach_messages, 'error': 'No song selected'})

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

@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    approachPath = data.get('approachPath', 'SHALLOW')
    print(f"Received request: Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}, Approach Path: {approachPath}")
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
    directory_path = os.path.join(script_dir, music_dir)
    csv_file_path = os.path.join(script_dir, csv_file)
    generate_csv(directory_path, csv_file_path)

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()
    
    app.run(port=5000)










