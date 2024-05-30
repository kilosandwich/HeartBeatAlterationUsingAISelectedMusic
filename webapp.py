"""this is the main file for the front end it will load the webpage with the list of mp3 files from the given directory. 
 it will also create a csv with the git charactersitics, in the rootpath function put the directory that has the music file
you want to use. Also put the directory path in the if __name__ == "__main__": for the directory path."""

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import os
import glob
import librosa
import numpy as np
import csv
import webbrowser 
from threading import Timer


app = Flask(__name__)
Bootstrap(app)
csv_file = "music_characteristics.csv"
# this is the csv file that will have the getcharacteristics

@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

def get_music_files():
    rootpath = "/Users/jeremyjohn/Desktop/music" #where you put your file path for the song folder you want to use
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
        
        for audio_file in audio_files:
            print(f"Processing file: {audio_file}")
            characteristics = get_characteristics(audio_file)
            writer.writerow([os.path.basename(audio_file)] + characteristics)
            print(f"Characteristics for {audio_file}: {characteristics}")


if __name__ == "__main__":
    directory_path = "/Users/jeremyjohn/Desktop/music"  # the directory path that has  audio files
    
    # Generate CSV file with audio get_characteristics
    generate_csv(directory_path, csv_file)
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/myapp")
    
    # Start a timer to open the browser
    Timer(1, open_browser).start()
    
    # Run the Flask application
    app.run(port=5000, debug=True)
    
    #app.run(port=5000)
    #app.run(port=5000, debug=True)
    
    # this opens the browser after starting the Flask app
   # def open_browser():
        #webbrowser.open_new("http://127.0.0.1:5000/myapp")
        #the flask app is running on http://127.0.0.1.5000
    
    # Starts a timer to get the browser open
    #Timer(1, open_browser).start()
    
    # Run the Flask application
    #app.run(port=5000, debug=True)
    #flask_thread = Thread(target=run_flask_app)
    #flask_thread.start()
        
    

