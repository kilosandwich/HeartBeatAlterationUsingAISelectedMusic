import os
import pygame
import time
import importlib.util
from tkinter import Tk, filedialog, simpledialog, messagebox, StringVar, Label, Entry, Button, Text
import logging
import threading
import csv
from GetHeartRate import HeartRateReader
import GetCharacteristics

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class HeartRateMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Heart Rate Monitor")

        self.music_directory = StringVar()
        self.csv_directory = StringVar()
        self.resting_heartrate = StringVar()
        self.song_name = StringVar()

        self.create_widgets()
        # on startup, create the heart rate reader, this will initiallize the connection to the heart rate monitor
        self.heart_rate_reader = HeartRateReader()
        # to prevent the user from doing anything on the front end, wait for 110 seconds using the wait for heart rate
        # data function, this will mean that any reading of the heart rate data will be gathered from the heart rate reader
        # only after it is full
        print("=================================================================")
        print("DO NOT BE ALARMED, WE NEED TO COLLECT YOUR HEART RATE DATA")
        print("USE OF THE PROGRAM IS SUSPENDED UNTIL YOUR DATA IS COLLECTED")
        print("=================================================================")
        wait_for_heart_rate_data(self.heart_rate_reader)
        print("################################################################")
        print("YOUR PROGRAM IS NOW AVAILABLE TO USE")
        print("################################################################")

    def create_widgets(self):
        # GUI for selecting the music folder
        Label(self.root, text="Select Music Folder:").grid(row=0, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.music_directory, width=50).grid(row=0, column=1, padx=10, pady=5)
        Button(self.root, text="Browse", command=self.browse_music_folder).grid(row=0, column=2, padx=10, pady=5)

        # GUI for selecting the CSV location
        Label(self.root, text="Select CSV Storage Location:").grid(row=1, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.csv_directory, width=50).grid(row=1, column=1, padx=10, pady=5)
        Button(self.root, text="Select", command=self.browse_csv_folder).grid(row=1, column=2, padx=10, pady=5)

        # Displays the current song
        Label(self.root, text="Current Song:").grid(row=2, column=0, padx=10, pady=5)
        Label(self.root, textvariable=self.song_name, width=50).grid(row=2, column=1, padx=10, pady=5)

        # Displays the song characteristics
        Label(self.root, text="Song Characteristics:").grid(row=3, column=0, padx=10, pady=5)
        self.song_characteristics = Text(self.root, height=10, width=50)
        self.song_characteristics.grid(row=3, column=1, padx=10, pady=5)
        self.song_characteristics.insert("1.0", "Song characteristics will be displayed here...")

        # Input box for the user's resting heart rate
        Label(self.root, text="Enter Resting Heart Rate:").grid(row=4, column=0, padx=10, pady=5)
        Entry(self.root, textvariable=self.resting_heartrate, width=50).grid(row=4, column=1, padx=10, pady=5)

        # Starts button to begin song processing
        Button(self.root, text="Start", command=self.start_process).grid(row=5, column=1, padx=10, pady=20)

    def browse_music_folder(self):
        # Opens a dialog to select a music folder and displays the mp3 files
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.music_directory.set(folder_selected)
            self.display_song_characteristics(folder_selected)

    def browse_csv_folder(self):
        # Opens a dialog to select a folder to save the CSVs
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.csv_directory.set(folder_selected)

    def display_song_characteristics(self, folder):
        # Displays the list of mp3s in the selected folder
        song_files = os.listdir(folder)
        characteristics = "\n".join(song_files)
        self.song_characteristics.delete("1.0", "end")
        self.song_characteristics.insert("1.0", characteristics)

    def start_process(self):
        # Validates the users input and starts processing mp3 files
        music_folder = self.music_directory.get()
        csv_folder = self.csv_directory.get()
        resting_heartrate = self.resting_heartrate.get()

        if not music_folder or not csv_folder or not resting_heartrate:
            messagebox.showerror("Error", "All fields must be filled out.")
            return

        try:
            self.resting_heartrate_value = float(resting_heartrate)
        except ValueError:
            messagebox.showerror("Error", "Resting heart rate must be a number.")
            return

        # Clears the previous song characteristics
        self.song_characteristics.delete("1.0", "end")

        # Starts a new thread to process MP3 files
        threading.Thread(target=self.process_mp3_files, args=(music_folder, csv_folder)).start()

    def process_mp3_files(self, music_folder, csv_folder):
        # Finds and processes each MP3 file in the selected folder
        mp3_files = find_mp3_files(music_folder)
        if not mp3_files:
            logging.error("No MP3 files found in the selected folder.")
            return

        for mp3_file in mp3_files:
            results = []
            self.process_mp3_file(mp3_file, results)
            save_results(results, csv_folder)

    def process_mp3_file(self, mp3_file, results):
        print("I am processing the mp3 file as requested!")
        # Processes an individual MP3 file to get its characteristics and simulate heart rate response
        logging.info(f"Processing MP3 file: {mp3_file}")

        characteristics = get_characteristics(mp3_file)
        logging.debug(f"Characteristics for {mp3_file}: {characteristics}")

        if characteristics:
            self.root.after(0, self.update_song_characteristics, mp3_file, characteristics)

        # Initialize HeartRateReader and wait for heart rate data to be populated
        # JK we initialized it when the class was initialized. We just need to read the heart rate list
        # from the heart rate reader
        initial_heart_rate = self.heart_rate_reader.get_heart_rate_int()
        heart_rate_data = self.heart_rate_reader.get_heart_rate()
        print("I have gathered the heart rate data: ", heart_rate_data)
        
        # This is the part where the song is played, the program is inaccessible while it is playing.
        play_mp3(mp3_file)
        # The song is over, get the user's ending heart rate
        change_in_heart_rate_data = initial_heart_rate - self.heart_rate_reader.get_heart_rate_int()

        # Now that the song has played, we can proceed with storing the data
        results.append({
            "Tempo of Song": characteristics[2],  # Adjust indices based on our list structure
            "Tempo of First 30 Seconds": characteristics[4],
            "Tempo of Last 30 Seconds": characteristics[5],
            "Length of Song": characteristics[3],
            "Pitch of First 30 Seconds": characteristics[0],
            "Pitch of Last 30 Seconds": characteristics[1],
            "Average Pitch of Song": characteristics[6],
            "HeartRate0": heart_rate_data[0] if len(heart_rate_data) > 0 else -1,
            "HeartRate1": heart_rate_data[1] if len(heart_rate_data) > 1 else -1,
            "HeartRate2": heart_rate_data[2] if len(heart_rate_data) > 2 else -1,
            "HeartRate3": heart_rate_data[3] if len(heart_rate_data) > 3 else -1,
            "HeartRate4": heart_rate_data[4] if len(heart_rate_data) > 4 else -1,
            "HeartRate5": heart_rate_data[5] if len(heart_rate_data) > 5 else -1,
            "HeartRate6": heart_rate_data[6] if len(heart_rate_data) > 6 else -1,
            "HeartRate7": heart_rate_data[7] if len(heart_rate_data) > 7 else -1,
            "HeartRate8": heart_rate_data[8] if len(heart_rate_data) > 8 else -1,
            "HeartRate9": heart_rate_data[9] if len(heart_rate_data) > 9 else -1,
            "RestingHeartRate": self.resting_heartrate_value,
            "ChangeInHeartRate": change_in_heart_rate_data
        })

        logging.info(f"Processed {mp3_file}")  # : Heart rate change is {change_in_heart_rate}")

    def update_song_characteristics(self, mp3_file, characteristics):
        # Updates the displayed song characteristics in the GUI
        self.song_name.set(os.path.basename(mp3_file))
        # Adjusts indices based on our list structure
        display_text = (f"Pitch of First 30 Seconds: {characteristics[0]}\n"
                        f"Pitch of Last 30 Seconds: {characteristics[1]}\n"
                        f"Tempo of Song: {characteristics[2]}\n"
                        f"Length of Song: {characteristics[3]}\n"
                        f"Tempo of First 30 Seconds: {characteristics[4]}\n"
                        f"Tempo of Last 30 Seconds: {characteristics[5]}\n"
                        f"Average Pitch of Song: {characteristics[6]}\n")
        self.song_characteristics.delete("1.0", "end")
        self.song_characteristics.insert("1.0", display_text)

def wait_for_heart_rate_data(heart_rate_reader):
    # by default, the heart rate reader reads a new data point every 10 seconds, for a total list length of 10
    # therefore if we wait 110 seconds then the list will be populated instead of empty. Note that this function
    # only has to be run on start up
    time.sleep(110)
    # return the current heart rate (technically we don't need to return anything, we could just run
    # heart rate reader.get_heart_rate() after the pause.
    # return heart_rate_reader.get_heart_rate()
    """
        logging.info("Waiting for heart rate data to be populated...")
        while True:
            heart_rate_reader.read_heart_rate()
            if len(heart_rate_reader.current_heart_rate) >= size:
                logging.info("Heart rate data populated.")
                
            time.sleep(1)
    """

def execute_script(script_path):
    # Dynamically executes an external Python script
    try:
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        script_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script_module)
        logging.info(f"Successfully executed script: {script_path}")
    except Exception as e:
        logging.error(f"Error running script {script_path}: {e}")

def read_file(file_path):
    # Reads a file and return its contents
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None

# Initialize Pygame for mp3 files
pygame.mixer.init()

def play_mp3(file_path):
    print("MUSIC NOW PLAYING: ", file_path)
    # Plays an MP3 file using Pygame
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            # repeatedly check if the music is playing, when it is no longer playing, the song is over. Mission accomplished.
            # this section of code stops the rest of the code for the front end from executing, the front end is completely
            # unusable while it is playing.
            time.sleep(1)
        logging.info(f"Finished playing MP3 file: {file_path}")
    except pygame.error as e:
        # so you messed up, it happens, the song isn't playing
        logging.error(f"Error playing {file_path}: {e}")

def find_mp3_files(directory):
    # Finds all MP3 files in a directory and its subdirectories
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    return mp3_files

def get_characteristics(filepath):
    # Gets song characteristics
    characteristics = GetCharacteristics.get_characteristics(filepath)
    logging.debug(f"Fetched characteristics for {filepath}: {characteristics}")
    print(f"Fetched characteristics for {filepath}: {characteristics}")  # Debug
    print(f"Type of characteristics: {type(characteristics)}")  # Debug
    return characteristics

def get_user_resting_heart_rate():
    # Prompts the user to enter their resting heart rate
    root = Tk()
    root.withdraw()
    resting_heart_rate = simpledialog.askfloat("Input", "Please enter your resting heart rate:")
    return resting_heart_rate

def save_results(results, folder):
    # Saves the results to a CSV file
    results_file = os.path.join(folder, "results.csv")
    file_exists = os.path.isfile(results_file)
    
    try:
        with open(results_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Tempo of Song",
                "Tempo of First 30 Seconds",
                "Tempo of Last 30 Seconds",
                "Length of Song",
                "Pitch of First 30 Seconds",
                "Pitch of Last 30 Seconds",
                "Average Pitch of Song",
                "HeartRate0",
                "HeartRate1",
                "HeartRate2",
                "HeartRate3",
                "HeartRate4",
                "HeartRate5",
                "HeartRate6",
                "HeartRate7",
                "HeartRate8",
                "HeartRate9",
                "RestingHeartRate",
                "ChangeInHeartRate"
            ])
            if not file_exists:
                writer.writeheader()
                print('Headers initialized')
            for result in results:
                print(result)
                writer.writerow(result)
        logging.info(f"Results saved to {results_file}")
    except Exception as e:
        logging.error(f"Error writing to results file: {e}")

def main():
    # Starts the GUI
    root = Tk()
    app = HeartRateMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
