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

from CSV_Handler import CSV_Handler

# This will start up Flask app and Bootstrap
app = Flask(__name__)
Bootstrap(app)

# Global variables and constants
script_dir = os.path.dirname(os.path.abspath(__file__))
music_dir = os.path.join(script_dir, "music")#this is defining the file path to the music directory
csv_file = os.path.join(script_dir, "music_characteristics.csv")#this is the path to the csv file
    #creation of the CSV_handler class automatically creates the CSV handler, which will read the data in the music folder
    #using the generate CSV function using a separate thread.
csv_handler = CSV_Handler(music_dir, csv_file)
TIMEOUT = 60
HR = 0  # Global variable that will store heart rate
input_size = 9
hidden_size = 10
output_size = 1
learning_rate = 0.01
dropout_prob = 0.1

model_path = os.path.join(script_dir, "HBModel.pth")#this will be defing the path taken to the model
model = SimpleNN(input_size, hidden_size, output_size, dropout_prob)
try:
    model.load_state_dict(torch.load(model_path))
    model.eval()#this is to endure that the mdoel is set to evaluation mode
    print("Model loaded and set to evaluation mode.")
except Exception as e:
    print(f"Error loading model: {e}")#print an error if the model doesnt load

if not os.path.exists(music_dir):
    os.makedirs(music_dir)#this will ensure there is a music directory or create one

# Initialize the HeartRateReader class
HR = HeartRateReader()
ALLOWED_EXTENSIONS = {'mp3'}#this makes sure the only acceptable file are mp3 files

def allowed_file(filename):#check to make sure the file has the allowed extension
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# this the Flask route for uploading files into the drop box the message that 
#appears will depend on if it's the correct extension for mp3 file then they will see succesful upload
@app.route("/upload", methods=["POST"])
def upload_file():
    global csv_handler #import the CSV_handler for the script in general
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(music_dir, filename))
        
        # once a file is uploaded the  CSV_Handler is to regenerate the CSV file after uploading new files
        csv_handler.songAdded()
        print("CSV file has been regenerated.")  # this will create the thread to regenerate the CSV so it runs faster
        
        return jsonify({'success': 'File uploaded successfully'}), 200#message that will appear if mp3 file uploads correctly
    else:
        return jsonify({'error': 'Invalid file type'}), 400# this will appear if its not a mp3 file submitted

@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = HR.get_resting_heart_rate() #get the resting heart rate from the user
    return jsonify({"hr": hr, "type": "resting"}) #return the heart rate to be displayed

@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = HR.get_heart_rate_int()# get the current heart rate 
    return jsonify({"hr": hr, "type": "current"})

@app.route("/get_approach_path_message", methods=["POST"])
def get_approach_path_message():
    data = request.json
    approachPath = data.get('approachPath', 'none') #get the approach path from the data request
    message = process_approach_path(approachPath)#process the selected apporach path
    return jsonify({'message': message})#return the message showing the approach path

# Message the user will see after they chose their approach path
def process_approach_path(approach_path):
    if approach_path == 'none':
        return "You chose none approach path"
    if approach_path == 'Shallow':
        return "You chose Shallow approach path"
    elif approach_path == 'Linear':
        return "You chose Linear approach path"
    elif approach_path == 'Steep':
        return "You chose Steep approach path"
    elif approach_path == 'Parabola':
        return "You chose Parabola approach path"
    elif approach_path == 'Fastest':
        return "You chose Fastest approach path"
    elif approach_path == 'Rollercoaster':
        return "You chose Rollercoaster approach path"
    else:
        return "Unknown approach path"

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    targetHR = int(data['targetHR'])#gets the target heart rate from the data
    restingHR = int(data['restingHR'])#gets the resting heart rate from the data
    approachPath = data.get('approachPath', 'none')#gets the chosen approach path from the request 

    # Get the current heart rate
    currentHR = HR.get_heart_rate_int()

    print(f"Received request: Target HR: {targetHR}, Current HR: {currentHR}, Resting HR: {restingHR}, Approach Path: {approachPath}")

    csvLocation = os.path.join(script_dir, "music_characteristics.csv")#this will define the csv loaction to make sure it's created
    selected_music = selectMusic(targetHR, currentHR, restingHR, csvLocation, approachPath)# this will select the music based on the data
    


        
    if selected_music:
        music_path = f'/music/{selected_music}' #define the music path to make sure correct song is returned
        return jsonify({'selected_music': music_path}) #return the selected music 
    return jsonify({'error': 'No song selected'})# this will show an error message if no song is selected

# Route for the main page
@app.route("/myapp")
def index():
    music_files = get_music_files()#this will get the lsit ofmp3 music files in directory
    return render_template('index.html', music_files=music_files)# this will send the music files to main

# Function to get music files
def get_music_files():
    pattern = "*.mp3"
    files = glob.glob(os.path.join(music_dir, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': f'/music/{os.path.basename(file)}'} for file in files]

@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']# this will get the target heart that should already be set
    heartRate = data['heartRate']# this get the current heart rate from the request that is sent 
    restingHR = data['restingHR']# this will read the heartr ate set or if thebutton is pressed
    approachPath = data.get('approachPath', 'SHALLOW')
    print(f"Received request: Target HR: {targetHR}, Current HR: {heartRate}, Resting HR: {restingHR}, Approach Path: {approachPath}")
    csvLocation = os.path.join(script_dir, "music_characteristics.csv")
    selected_music = selectMusic(targetHR, heartRate, restingHR, csvLocation, approachPath)
    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

@app.route('/music/<filename>')
def play_music(filename):
    return send_from_directory(music_dir, filename)# this will return the music file from the music directory

@app.route('/')
def home():
    return render_template('index.html')# the index is the home page so it will return the same page

@app.route('/user_guide')
def user_guide():
    return render_template('user_guide.html')# the user guide is it's own page so it will go to seperate page when pressed

@app.route('/advanced_features')
def advanced_features():
    return render_template('advanced_features.html')


if __name__ == "__main__":
   
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")# this opens the app in the default browser
    
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()# makes sure timer starts to open browser afeter 1 second
    
    app.run(port=5000)#port 5000 will be used to run the flask app











