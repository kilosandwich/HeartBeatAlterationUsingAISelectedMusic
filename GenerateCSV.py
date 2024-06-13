import os
import csv
import glob

def generate_csv(directory_path, csv_file):
    pattern = "*.mp3"
    audio_files = glob.glob(os.path.join(directory_path, pattern))
    processed_files = set()
    if os.path.exists(csv_file):
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  
            for row in reader:
                processed_files.add(row[0])

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
