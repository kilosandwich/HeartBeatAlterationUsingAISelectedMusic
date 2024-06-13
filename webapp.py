import os
import glob
import webbrowser
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_bootstrap import Bootstrap
from ModelDefinition import SimpleNN  

from GetCharacteristics import get_characteristics
from generateCSV import generate_csv
from getHeartRate import get_heart_rate
from GetRestingHeartRate import get_resting_HR
from selectMusic import selectMusic

app = Flask(__name__)
Bootstrap(app)

script_dir = os.path.dirname(os.path.abspath(__file__))
music_dir = os.path.join(script_dir, "music")
csv_file = "music_characteristics.csv"

if not os.path.exists(music_dir):
    os.makedirs(music_dir)

model = SimpleNN(9, 10, 1, 0.1)
model_path = os.path.join(script_dir, "HBModel.pth")

try:
    model.load_state_dict(torch.load(model_path))
    model.eval()
except Exception as e:
    print(f"Error loading model: {e}")

@app.route("/myapp")
def index():
    pattern = "*.mp3"
    files = glob.glob(os.path.join(music_dir, pattern))
    music_files = [{'file_name': os.path.basename(file), 'file_path': f'/music/{os.path.basename(file)}'} for file in files]
    return render_template('index.html', music_files=music_files)

@app.route("/start_resting_hr_monitor", methods=["GET"])
def start_resting_hr_monitor():
    hr = get_resting_HR()
    return jsonify({"hr": hr, "type": "resting"})

@app.route("/start_current_hr_monitor", methods=["GET"])
def start_current_hr_monitor():
    hr = get_heart_rate()
    return jsonify({"hr": hr, "type": "current"})

@app.route("/get_music", methods=["POST"])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    selected_music = selectMusic(targetHR, heartRate, restingHR, os.path.join(script_dir, "music_characteristics.csv"))
    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

@app.route('/music/<filename>')
def play_music(filename):
    return send_from_directory(music_dir, filename)

if __name__ == "__main__":
    directory_path = os.path.join(script_dir, "music")
    generate_csv(directory_path, csv_file)
    webbrowser.open_new("http://127.0.0.1:5000/myapp")
    app.run(port=5000, debug=True)
