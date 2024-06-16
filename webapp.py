import os
import pygame
import time
import importlib.util
from tkinter import Tk, filedialog, Label, Button, Entry, StringVar
import logging
import threading
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

def choose_music_folder():
    folder_selected = filedialog.askdirectory()
    return folder_selected

def choose_csv_file():
    file_selected = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    return file_selected

def process_mp3_file(mp3_file, results, resting_heart_rate):
    logging.info(f"Processing MP3 file: {mp3_file}")

    execute_script("GetCharacteristics.py")
    execute_script("GetRestingHeartRate.py")

    characteristics_str = read_file("characteristics.txt")
    resting_heart_rate_str = read_file("resting_heart_rate.txt")

    if characteristics_str is None or resting_heart_rate_str is None:
        return

    characteristics = eval(characteristics_str)
    resting_heart_rate = float(resting_heart_rate_str)

    update_feedbacks(mp3_file, characteristics, resting_heart_rate, None)

    play_mp3(mp3_file)

    execute_script("GetRestingHeartRate.py")

    heart_rate_str = read_file("resting_heart_rate.txt")
    if heart_rate_str is None:
        return

    heart_rate = float(heart_rate_str)

    update_feedbacks(mp3_file, characteristics, resting_heart_rate, heart_rate)

    change_in_heart_rate = heart_rate - resting_heart_rate

    results.append({
        "file": mp3_file,
        "characteristics": characteristics,
        "resting_heart_rate": resting_heart_rate,
        "heart_rate": heart_rate,
        "change_in_heart_rate": change_in_heart_rate
    })

def save_results(results, csv_file_path):
    try:
        with open(csv_file_path, 'a') as f:
            for result in results:
                f.write(f"{result['file']},{result['characteristics']},{result['resting_heart_rate']},{result['heart_rate']},{result['change_in_heart_rate']}\n")
        logging.info(f"Results appended to {csv_file_path}")
    except IOError as e:
        logging.error(f"Error writing to CSV file: {e}")

def main():
    def start_processing():
        resting_heart_rate = float(resting_heart_rate_var.get())
        music_folder = music_folder_var.get()
        csv_file_path = csv_file_var.get()

        if not music_folder:
            logging.error("No music folder selected. Exiting.")
            return

        mp3_files = find_mp3_files(music_folder)
        if not mp3_files:
            logging.error("No MP3 files found in the selected folder.")
            return

        results = []
        threads = []

        for mp3_file in mp3_files:
            thread = threading.Thread(target=process_mp3_file, args=(mp3_file, results, resting_heart_rate))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        save_results(results, csv_file_path)

    root = Tk()
    root.title("Trainer App")

    resting_heart_rate_label = Label(root, text="Resting Heart Rate")
    resting_heart_rate_label.pack()
    resting_heart_rate_var = StringVar()
    resting_heart_rate_entry = Entry(root, textvariable=resting_heart_rate_var)
    resting_heart_rate_entry.pack()
    resting_heart_rate_feedback = Label(root, text="", fg="blue")
    resting_heart_rate_feedback.pack()

    music_folder_label = Label(root, text="Music Folder")
    music_folder_label.pack()
    music_folder_var = StringVar()
    music_folder_button = Button(root, text="Select Music Folder", command=lambda: [music_folder_var.set(choose_music_folder()), music_folder_feedback.config(text=f"Selected folder: {music_folder_var.get()}")])
    music_folder_button.pack()
    music_folder_feedback = Label(root, text="", fg="blue")
    music_folder_feedback.pack()

    csv_file_label = Label(root, text="Training Data CSV File")
    csv_file_label.pack()
    csv_file_var = StringVar()
    csv_file_button = Button(root, text="Select CSV File", command=lambda: [csv_file_var.set(choose_csv_file()), csv_file_feedback.config(text=f"Selected file: {csv_file_var.get()}")])
    csv_file_button.pack()
    csv_file_feedback = Label(root, text="", fg="blue")
    csv_file_feedback.pack()

    start_button = Button(root, text="Start Processing", command=lambda: [start_processing(), start_feedback.config(text="Processing started...")])
    start_button.pack()
    start_feedback = Label(root, text="", fg="blue")
    start_feedback.pack()

    current_song_feedback = Label(root, text="", fg="blue")
    current_song_feedback.pack()

    music_characteristics_feedback = Label(root, text="", fg="blue")
    music_characteristics_feedback.pack()

    recorded_heartbeat_feedback = Label(root, text="", fg="blue")
    recorded_heartbeat_feedback.pack()

    ending_heartbeat_feedback = Label(root, text="", fg="blue")
    ending_heartbeat_feedback.pack()

    def update_feedbacks(mp3_file, characteristics, resting_heart_rate, heart_rate):
        current_song_feedback.config(text=f"Currently playing: {mp3_file}")
        music_characteristics_feedback.config(text=f"Music characteristics: {characteristics}")
        recorded_heartbeat_feedback.config(text=f"Recorded heartbeat before playing: {resting_heart_rate}")
        ending_heartbeat_feedback.config(text=f"Recorded ending heartbeat: {heart_rate}")

    root.mainloop()

if __name__ == "__main__":
    main()
