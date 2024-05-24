from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import os
import glob

app = Flask(__name__)
Bootstrap(app)

@app.route("/myapp")
def index():
    music_files = get_music_files()
    return render_template('index.html', music_files=music_files)

def get_music_files():
    rootpath = "/Users/jeremyjohn/Desktop/music"
    pattern = "*.mp3"
    files = glob.glob(os.path.join(rootpath, pattern))
    return [{'file_name': os.path.basename(file), 'file_path': file} for file in files]

if __name__ == '__main__':
    app.run(port=5000, debug=True)