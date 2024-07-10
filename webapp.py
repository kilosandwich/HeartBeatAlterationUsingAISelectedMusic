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
from ModelDefinition import SimpleNN  
from GetHeartRate import HeartRateReader
from selectMusic import selectMusic
from GetCharacteristics import get_characteristics
from GenerateCSV import generate_csv

# Sets up the Flask app and Bootstrap for a nice UI
app = Flask(__name__)
Bootstrap(app)

script_dir = os.path.dirname(os.path.abspath(__file__))
music_dir = os.path.join(script_dir, "music")
csv_file = os.path.join(script_dir, "music_characteristics.csv")
TIMEOUT = 60  # Times out in 60 seconds
HR = 0  # This will store the heart rate
input_size = 9
hidden_size = 10
output_size = 1
learning_rate = 0.01
dropout_prob = 0.1

model_path = os.path.join(script_dir, "HBModel.pth")

# Loads the pre-trained model
model = SimpleNN(input_size, hidden_size, output_size, dropout_prob)
try:
    model.load_state_dict(torch.load(model_path))
    model.eval()  # Sets the model to evaluation mode
    print("Model loaded and set to evaluation mode.")
except Exception as e:
    print(f"Error loading model: {e}")

# This makes sure that the music directory exists
if not os.path.exists(music_dir):
    os.makedirs(music_dir)

# Initializes the heart rate reader, pretty simple
HR = HeartRateReader()

# Allowed file extensions for uploading music, which are only mp3 
ALLOWED_EXTENSIONS = {'mp3'}

# Checks if a file has one of the allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Handles file uploads by using a POST request
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
        
        # Regenerates the CSV file after uploading new files
        generate_csv(music_dir, csv_file)
        print("CSV file has been regenerated.")
        
        return jsonify({'success': 'File uploaded successfully'}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400

# Starts monitoring the users resting heart rate
@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = HR.get_resting_heart_rate()
    return jsonify({"hr": hr, "type": "resting"})

# Starts monitoring the users current heart rate
@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = HR.get_heart_rate_int()
    return jsonify({"hr": hr, "type": "current"})

# Gets a message based on the users selected approach path
@app.route("/get_approach_path_message", methods=["POST"])
def get_approach_path_message():
    data = request.json
    approachPath = data.get('approachPath', 'SHALLOW')
    message = process_approach_path(approachPath)
    return jsonify({'message': message})

# Returns a message based on the approach path
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

    # Gets the current heart rate
    currentHR = HR.get_heart_rate_int()

    print(f"Received request: Target HR: {targetHR}, Current HR: {currentHR}, Resting HR: {restingHR}, Approach Path: {approachPath}")

    # Path to the CSV file with music characteristics
    csvLocation = os.path.join(script_dir, "music_characteristics.csv")

    # Selects the appropriate music based on the heart rate and approach path
    selected_music = selectMusic(targetHR, currentHR, restingHR, csvLocation, approachPath)

    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

# Main page showing the list of music files
@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

# Gets the list of mp3 files in the music directory
def get_music_files():
    pattern = "*.mp3"
    files = glob.glob(os.path.join(music_dir, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': f'/music/{os.path.basename(file)}'} for file in files]

# Gets music based on the heart rate data provided by the user
@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    approachPath = data.get('approachPath', 'SHALLOW')
    print(f"Received request: Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}, Approach Path: {approachPath}")
    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, heartRate, restingHR, csvLocation, approachPath)
    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

# Plays a specific mp3 file
@app.route('/music/<filename>')
def play_music(filename):
    return send_from_directory(music_dir, filename)

# Home page route
@app.route('/')
def home():
    return render_template('index.html')

# Users guide page route
@app.route('/user_guide')
def user_guide():
    return render_template('user_guide.html')

# This is the advanced features page route
@app.route('/advanced_features')
def advanced_features():
    return render_template('advanced_features.html')

# Generates a CSV file with the characteristics of the music files
def generate_csv(directory_path, csv_file_path):
    headers = [
        'file_name', 'avg_tempo', 'tempo_first_30', 'tempo_last_30',
        'song_length', 'pitch_first_30', 'pitch_last_30', 'avg_pitch'
    ]

    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for filename in os.listdir(directory_path):
            if filename.endswith('.mp3'):
                file_path = os.path.join(directory_path, filename)
                print(f"Analyzing: {file_path}")

                # Extracts the characteristics of the song
                characteristics = get_characteristics(file_path)
                writer.writerow([filename] + characteristics)

if __name__ == "__main__":

    # Opens the browser with the app
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()
    
    # Runs the Flask application
    app.run(port=5000)
4