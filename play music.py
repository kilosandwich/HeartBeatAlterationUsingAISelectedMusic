#this part of the code will be added to the get music function with an if statement to play
#the song after it's selected the player will only appear if the selected song is given
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# Global variable for the music directory
music_dir = "insert music folder"  # put your music folder here

@app.route('/music/<filename>')
def serve_music(filename):
    return send_from_directory(music_dir, filename)

@app.route('/get_music', methods=['POST'])
def get_music():
    data = request.json
    targetHR = data['targetHR']
    heartRate = data['heartRate']
    restingHR = data['restingHR']
    selected_music = selectMusic(targetHR, heartRate, restingHR, csv_file)
    if selected_music:
        music_path = f'/music/{selected_music}'
        return jsonify({'selected_music': music_path})
    return jsonify({'error': 'No song selected'})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
