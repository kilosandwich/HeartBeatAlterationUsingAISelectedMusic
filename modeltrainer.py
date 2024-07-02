import os
import pygame
import time
import importlib.util
from tkinter import Tk, filedialog, simpledialog, messagebox, StringVar, Label, Entry, Button, Text
import logging
import threading
import json
from GetHeartRate import HeartRateReader 
import GetCharacteristics

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class HeartRateMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Heart Rate Monitor")

        self.music_directory = StringVar()
        self.csv_directory = StringVar()
        self.resting_heartrate = StringVar()
        self.song_name = StringVar()

        self.create_widgets()

    def create_widgets(self):
        Label(self.root, text="Select Music Folder:").grid(row=0, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.music_directory, width=50).grid(row=0, column=1, padx=10, pady=5)
        Button(self.root, text="Browse", command=self.browse_music_folder).grid(row=0, column=2, padx=10, pady=5)

        Label(self.root, text="Select CSV Storage Location:").grid(row=1, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.csv_directory, width=50).grid(row=1, column=1, padx=10, pady=5)
        Button(self.root, text="Select", command=self.browse_csv_folder).grid(row=1, column=2, padx=10, pady=5)

        Label(self.root, text="Current Song:").grid(row=2, column=0, padx=10, pady=5)
        Label(self.root, textvariable=self.song_name, width=50).grid(row=2, column=1, padx=10, pady=5)

        Label(self.root, text="Song Characteristics:").grid(row=3, column=0, padx=10, pady=5)
        self.song_characteristics = Text(self.root, height=10, width=50)
        self.song_characteristics.grid(row=3, column=1, padx=10, pady=5)
        self.song_characteristics.insert("1.0", "Song characteristics will be displayed here...")

        Label(self.root, text="Enter Resting Heart Rate:").grid(row=4, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.resting_heartrate, width=50).grid(row=4, column=1, padx=10, pady=5)

        Button(self.root, text="Start", command=self.start_process).grid(row=5, column=1, padx=10, pady=20)

    def browse_music_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.music_directory.set(folder_selected)
            self.display_song_characteristics(folder_selected)

    def browse_csv_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.csv_directory.set(folder_selected)

    def display_song_characteristics(self, folder):
        song_files = os.listdir(folder)
        characteristics = "\n".join(song_files)
        self.song_characteristics.delete("1.0", "end")
        self.song_characteristics.insert("1.0", characteristics)

    def start_process(self):
        music_folder = self.music_directory.get()
        csv_folder = self.csv_directory.get()
        resting_heartrate = self.resting_heartrate.get()

        if not music_folder or not csv_folder or not resting_heartrate:
            messagebox.showerror("Error", "All fields must be filled out.")
            return

        try:
            resting_heartrate = float(resting_heartrate)
        except ValueError:
            messagebox.showerror("Error", "Resting heart rate must be a number.")
            return

        self.song_characteristics.delete("1.0", "end")  # Clear previous characteristics

        threading.Thread(target=self.process_mp3_files, args=(music_folder, csv_folder, resting_heartrate)).start()

    def process_mp3_files(self, music_folder, csv_folder, resting_heartrate):
        mp3_files = find_mp3_files(music_folder)
        if not mp3_files:
            logging.error("No MP3 files found in the selected folder.")
            return

        results = []

        for mp3_file in mp3_files:
            self.process_mp3_file(mp3_file, results, resting_heartrate)

        save_results(results, csv_folder)

    def process_mp3_file(self, mp3_file, results, resting_heartrate):
        logging.info(f"Processing MP3 file: {mp3_file}")

        characteristics = get_characteristics(mp3_file)
        logging.debug(f"Characteristics for {mp3_file}: {characteristics}")

        if characteristics:
            self.root.after(0, self.update_song_characteristics, mp3_file, characteristics)

        play_mp3(mp3_file)

        heart_rate_reader = HeartRateReader()
        time.sleep(1)
        heart_rate = heart_rate_reader.get_heart_rate()

        if heart_rate is None:
            logging.error("No heart rate data received.")
            return

        change_in_heart_rate = heart_rate - resting_heartrate

        results.append({
            "file": mp3_file,
            "characteristics": characteristics,
            "resting_heartrate": resting_heartrate,
            "heart_rate": heart_rate,
            "change_in_heart_rate": change_in_heart_rate
        })

        logging.info(f"Processed {mp3_file}: Heart rate change is {change_in_heart_rate}")

    def update_song_characteristics(self, mp3_file, characteristics):
        self.song_name.set(os.path.basename(mp3_file))
        display_text = (f"Name: {characteristics.get('name', 'N/A')}\n"
                        f"Pitch: {characteristics.get('pitch', 'N/A')}\n"
                        f"Tempo: {characteristics.get('tempo', 'N/A')}\n"
                        f"Length: {characteristics.get('length', 'N/A')}\n")
        self.song_characteristics.delete("1.0", "end")
        self.song_characteristics.insert("1.0", display_text)

def execute_script(script_path):
    try:
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        script_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script_module)
        logging.info(f"Successfully executed script: {script_path}")
    except Exception as e:
        logging.error(f"Error running script {script_path}: {e}")

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None

pygame.mixer.init()

def play_mp3(file_path):
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        logging.info(f"Finished playing MP3 file: {file_path}")
    except pygame.error as e:
        logging.error(f"Error playing {file_path}: {e}")

def find_mp3_files(directory):
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    return mp3_files

def get_characteristics(filepath):
    characteristics = GetCharacteristics.get_characteristics(filepath)
    logging.debug(f"Fetched characteristics for {filepath}: {characteristics}")
    # Example characteristics structure
    # characteristics = {"pitch": "high", "tempo": "fast", "length": "3:45", "name": "example_song"}
    return characteristics

def get_user_resting_heart_rate():
    root = Tk()
    root.withdraw()
    resting_heart_rate = simpledialog.askfloat("Input", "Please enter your resting heart rate:")
    return resting_heart_rate

def save_results(results, folder):
    results_file = os.path.join(folder, "results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=4)
        logging.info(f"Results saved to {results_file}")
    except IOError as e:
        logging.error(f"Error writing to results file: {e}")

def main():
    root = Tk()
    app = HeartRateMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
