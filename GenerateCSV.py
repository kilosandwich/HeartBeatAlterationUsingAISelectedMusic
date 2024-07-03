import os
import csv
import glob
from GetCharacteristics import get_characteristics
#Tell the user this function only accepts strings
def generate_csv(directory_path: str, csv_file: str):
    print("Music directory is: ", directory_path, "the CSV file to save to is: ", csv_file)
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    processed_files = set()
    if os.path.exists(csv_file):
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            #if the file is not blank, then see what files already exist. 
            try:
                next(reader)  
                for row in reader:
                    print(row[0])
                    processed_files.add(row[0])
            except Exception as e:
                print("CSV is blank! No files to skip!")
        print("These are the files ALREADY found in: ", directory_path, " that we tried to write to ", csv_file)
        print(processed_files)
        print("=================================================")

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not processed_files:
            writer.writerow(["File", "Song Length", "Average Tempo", "Tempo First 30s", "Tempo Last 30s", "Average Pitch", "Pitch First 30s", "Pitch Last 30s"])
        for audio_file in audio_files:
            musicFilePath = os.path.basename(audio_file)
            if musicFilePath in processed_files:
                continue
            characteristics = get_characteristics(audio_file)
            rowToWrite = [musicFilePath] + characteristics
            writer.writerow(rowToWrite)
            
if __name__ == "__main__":
    import os
    #debugging program to ONLY run when this function is the only one running

    #find the directory this file is currently in
    script_dir = os.path.dirname(os.path.abspath(__file__))
    music_dir = "music"
    csv_dir = "music_characteristics.csv"

    #get the absolute directory for the music folder one sublevel down
    music_dir = os.path.join(script_dir, music_dir)
    csv_dir = os.path.join(script_dir, csv_dir)
    generate_csv(music_dir, csv_dir )