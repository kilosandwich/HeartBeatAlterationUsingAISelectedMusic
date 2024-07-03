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
    def __init__(self, music_dir: str, CSV_dir: str,):
        #On creation of this class, with the music folder and CSV directory as an input,
        #run generate CSV in a separate thread. This will mean that whichever program
        #uses this class will have the ability to continue operating without pause once 
        #the thread is initialized
        
        #keep in mind that running this COULD mean that there are race conditions 
        #if the writing is not finished in time, this should not be an issue since
        #generate CSV does not consider files that it has already consider,
        #and that new files when added via the front end runs generate CSV every time.
        
        #save the initialization inputs for later
        self.music_dir = music_dir
        self.CSV_dir = CSV_dir
        
        #start the thread that runs generate_csv
        self.createThread()
    def createThread(self):
        #This creates a thread for the specified music directory and csv directory
        print("You have added a new song! Generating new CSV")
        print("CSV handler thread created, running generate_csv with arguments: ", self.music_dir, " ", self.CSV_dir)
        self.thread = threading.Thread(target=generate_csv, args=(self.music_dir, self.CSV_dir))
        self.thread.daemon = True #shut down the thread once it is done to conserve resources
        self.thread.start()
    def songAdded(self):
        #theoretically, if this function is called while createThread is running, this will cause an error, therefore
        #the best solution is to FORCE the program to wait while songs are added.
        #this will be slower, but it will prevent the player from doing anything else that could cause a race condition.
        generate_csv(self.music_dir, self.CSV_dir)
    
        
#local debugging feature
if __name__ == "__main__":
    import os
    #find the directory this file is currently in
    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_dir = "music"
    csv_dir = "music_characteristics.csv"

    #get the absolute directory for the music folder one sublevel down
    music_dir = os.path.join(script_dir, music_dir)
    csv_dir = os.path.join(script_dir, csv_dir)
    Data = CSV_Handler(music_dir,csv_dir)