import os
import pygame
import time
import importlib.util
from tkinter import Tk, filedialog
import logging
import threading
import json

# Setup logging
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
    Tk().withdraw()
    folder_selected = filedialog.askdirectory(initialdir="C:/Users/ahmad/OneDrive/School/Capstone")
    return folder_selected

def process_mp3_file(mp3_file, results):
    logging.info(f"Processing MP3 file: {mp3_file}")

    execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetCharacteristics.py")
    execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetRestingHeartRate.py")

    characteristics_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/characteristics.txt")
    resting_heart_rate_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/resting_heart_rate.txt")

    if characteristics_str is None or resting_heart_rate_str is None:
        return

    characteristics = eval(characteristics_str)
    resting_heart_rate = float(resting_heart_rate_str)

    play_mp3(mp3_file)

    execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetRestingHeartRate.py")

    heart_rate_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/resting_heart_rate.txt")
    if heart_rate_str is None:
        return

    heart_rate = float(heart_rate_str)

    change_in_heart_rate = heart_rate - resting_heart_rate

    results.append({
        "file": mp3_file,
        "characteristics": characteristics,
        "resting_heart_rate": resting_heart_rate,
        "heart_rate": heart_rate,
        "change_in_heart_rate": change_in_heart_rate
    })

def save_results(results, folder):
    results_file = os.path.join(folder, "results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=4)
        logging.info(f"Results saved to {results_file}")
    except IOError as e:
        logging.error(f"Error writing to results file: {e}")

def main():
    music_folder = choose_music_folder()
    if not music_folder:
        logging.error("No folder selected. Exiting.")
        return

    mp3_files = find_mp3_files(music_folder)
    if not mp3_files:
        logging.error("No MP3 files found in the selected folder.")
        return

    results = []
    threads = []

    for mp3_file in mp3_files:
        thread = threading.Thread(target=process_mp3_file, args=(mp3_file, results))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    save_results(results, music_folder)

if __name__ == "__main__":
    main()
