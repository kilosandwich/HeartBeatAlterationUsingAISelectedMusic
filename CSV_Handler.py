################################
"""
Hello future brave astronaut, welcome to the CSV handler file

PURPOSE: 
This file is meant to handle all the initialization for the CSV. 
This file will take the expected CSV directory as an input,
and the expected music directory as an input.
It will then run GenerateCSV in a separate thread so that the
program runs faster.
"""
import threading
from GenerateCSV import generate_csv

class CSV_Handler():
    def __init__(self, music_dir: str, CSV_dir: str):
        # On creation of this class, with the music folder and CSV directory as an input,
        # run generate CSV in a separate thread. This will mean that whichever program
        # uses this class will have the ability to continue operating without pause once 
        # the thread is initialized
        
        # keep in mind that running this COULD mean that there are race conditions 
        # if the writing is not finished in time, this should not be an issue since
        # generate CSV does not consider files that it has already consider,
        # and that new files when added via the front end runs generate CSV every time.
        
        # save the initialization inputs for later
        self.music_dir = music_dir
        self.CSV_dir = CSV_dir
        self.is_running = False  # Add a flag to check if the thread is already running
        self.lock = threading.Lock()  # Add a lock for thread safety
        
        # start the thread that runs generate_csv
        print("CSV_Handler instantiated")
        self.createThread()

    def createThread(self):
        with self.lock:
            if self.is_running:
                print("CSV generation is already running. Skipping new thread creation.")
                return
            self.is_running = True
            print("You have added a new song! Generating new CSV")
            print("CSV handler thread created, running generate_csv with arguments: ", self.music_dir, " ", self.CSV_dir)
            self.thread = threading.Thread(target=self.run_generate_csv)
            self.thread.daemon = True  # shut down the thread once it is done to conserve resources
            self.thread.start()

    def run_generate_csv(self):
        generate_csv(self.music_dir, self.CSV_dir)
        with self.lock:
            self.is_running = False  # Resets the flag when it is done -_-

    def songAdded(self):
        with self.lock:
            if self.is_running:
                print("CSV generation is already running, we are waiting for it to finish")
                self.thread.join()
            generate_csv(self.music_dir, self.CSV_dir)

# Local debugging feature
if __name__ == "__main__":
    import os
    # Find the directory this file is currently in
    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_dir = "music"
    csv_dir = "music_characteristics.csv"

    # Get the absolute directory for the music folder one sublevel down
    music_dir = os.path.join(script_dir, music_dir)
    csv_dir = os.path.join(script_dir, csv_dir)
    Data = CSV_Handler(music_dir, csv_dir)
