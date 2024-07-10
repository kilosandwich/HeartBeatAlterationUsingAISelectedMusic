import librosa
import numpy as np

# Function to load a segment of audio from a given start time and duration
def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

# Function to compute the tempo of an audio segment
def compute_tempo(audioInfo, samplingRate):
    tempo = librosa.beat.beat_track(y=audioInfo, sr=samplingRate)[0]
    try:
        # On some machines, tempo is inexplicably converted into an array, therefore the default
        # solution around this is to ATTEMPT to see if there is an array there. If there is not,
        # then everything is good

        tempo = tempo[0]
    except Exception as e:
        tempo = tempo
    return tempo

# Computse the avg pitch 
def compute_average_pitch(audioInfo, samplingRate):
    pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
    return np.mean(pitches)

# Gets the characteristics of a song, which includes the duration, tempo, pitch, etc
def get_characteristics(filepath):
    print("I am attempting to analyze: ", filepath)
    y, samplingRate = librosa.load(filepath)  # Loads the mp3 file
    print("Getting length")
    songLength = librosa.get_duration(y=y, sr=samplingRate)  # Gets the duration of the song
    print("Getting tempo")
    avgTempo = compute_tempo(y, samplingRate)  # Computes the avg tempo
    first_30s_audio = load_audio_segment(y, samplingRate, 0, 30)  # Loads the first 30 secs of the song
    last_30s_audio = load_audio_segment(y, samplingRate, max(0, songLength - 30), 30)  # Loads the last 30 secs of the song
    tempo_first_30 = compute_tempo(first_30s_audio, samplingRate)  # Computes the tempo of the first 30 secs
    tempo_last_30 = compute_tempo(last_30s_audio, samplingRate)  # Computes the tempo of the last 30 secs
    print("Getting pitch")
    avgPitch = compute_average_pitch(y, samplingRate)  # Computes the average pitch
    pitch_first_30 = compute_average_pitch(first_30s_audio, samplingRate)  # Computes the pitch of the first 30 secs
    pitch_last_30 = compute_average_pitch(last_30s_audio, samplingRate)  # Computes the pitch of the last 30 secs
    print("Here are the music characteristics we gathered")
    print([
        avgTempo,
        tempo_first_30,
        tempo_last_30,
        songLength,
        pitch_first_30,
        pitch_last_30,
        avgPitch
    ])

    return [
        avgTempo,
        tempo_first_30,
        tempo_last_30,
        songLength,
        pitch_first_30,
        pitch_last_30,
        avgPitch
    ]

# Tests the get_characteristics function
if __name__ == "__main__":
    print("I have started up!")
    filepath = "C:/Users/ahmad/OneDrive/Desktop/Project/HeartBeatAlterationUsingAISelectedMusic-main/Nixon.mp3"  # Will be altered with further testing
    characteristics = get_characteristics(filepath)  # Gets the characteristics of the test audio file
    print(characteristics)  # Prints the characteristics
