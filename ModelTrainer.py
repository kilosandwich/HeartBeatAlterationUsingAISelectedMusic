import os
import pygame
import time
import importlib.util
from tkinter import Tk, filedialog

# This function dynamically loads and executes a script
def execute_script(script_path):
    try:
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        script_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script_module)
    except Exception as e:
        print(f"Error running script {script_path}: {e}")

# Reads the results from a file
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

pygame.mixer.init()

# Plays mp3 files
def play_mp3(file_path):
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except pygame.error as e:
        print(f"Error playing {file_path}: {e}")

# THis scans a directory for MP3 files
def find_mp3_files(directory):
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    return mp3_files

# Prompts the user to select a folder with the MP3 files
def choose_music_folder():
    Tk().withdraw()  # Hide the root Tkinter window
    folder_selected = filedialog.askdirectory(initialdir="C:/Users/ahmad/OneDrive/School/Capstone")
    return folder_selected

def main():
    music_folder = choose_music_folder()
    if not music_folder:
        print("No folder selected. Exiting.")
        return

    mp3_files = find_mp3_files(music_folder)
    if not mp3_files:
        print("No MP3 files found in the selected folder.")
        return

    results = []

    for mp3_file in mp3_files:
        print(f"Playing: {mp3_file}")
        
        # Execute external scripts
        execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetCharacteristics.py")
        execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetRestingHeartRate.py")
        
        # Read characteristics and resting heart rate before playing the music to see the 
        characteristics_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/characteristics.txt")
        resting_heart_rate_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/resting_heart_rate.txt")

        if characteristics_str is None or resting_heart_rate_str is None:
            continue
        
        characteristics = eval(characteristics_str)
        resting_heart_rate = float(resting_heart_rate_str)
        
        # Plays the mp3 file
        play_mp3(mp3_file)
        
        # gets the users resting heart rate again after playing the music to see the new resting heart rate
        execute_script("C:/Users/ahmad/OneDrive/School/Capstone/GetRestingHeartRate.py")
        
        # Gets the users heart rate after playing the file
        heart_rate_str = read_file("C:/Users/ahmad/OneDrive/School/Capstone/resting_heart_rate.txt")
        if heart_rate_str is None:
            continue
        
        heart_rate = float(heart_rate_str)
        
        # Calculates the change in the users heart rate
        change_in_heart_rate = heart_rate - resting_heart_rate
        
        # Appends the results to the list
        results.append({
            "file": mp3_file,
            "characteristics": characteristics,
            "resting_heart_rate": resting_heart_rate,
            "heart_rate": heart_rate,
            "change_in_heart_rate": change_in_heart_rate
        })

    # Saves results to a text file (which may be altered later)
    results_file = os.path.join(music_folder, "results.txt")
    try:
        with open(results_file, 'w') as f:
            for result in results:
                f.write(str(result) + '\n')
        print(f"Results saved to {results_file}")
    except IOError as e:
        print(f"Error writing to results file: {e}")

if __name__ == "__main__":
    main()
