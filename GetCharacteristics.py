import librosa
import numpy as np

def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

def compute_tempo(audioInfo, samplingRate):
    tempo = librosa.beat.beat_track(y=audioInfo, sr=samplingRate)[0]
    try:
        #On some machines, tempo is inexplicably converted into an array, therefore the default
        #solution around this is to ATTEMPT to see if there is an array there. If there is not,
        #then everything is good

        #Try to see if there is an array
        tempo = tempo[0]
    except Exception as e:
        #There is not an array
        tempo = tempo
    return tempo

def compute_average_pitch(audioInfo, samplingRate):
    pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
    return np.mean(pitches)

def get_characteristics(filepath):
    print("I am attempting to analyze: ", filepath)
    y, samplingRate = librosa.load(filepath)
    print("Getting length")
    songLength = librosa.get_duration(y=y, sr=samplingRate)
    print("Getting tempo")
    avgTempo = compute_tempo(y, samplingRate)
    first_30s_audio = load_audio_segment(y, samplingRate, 0, 30)
    last_30s_audio = load_audio_segment(y, samplingRate, max(0, songLength - 30), 30)
    tempo_first_30 = compute_tempo(first_30s_audio, samplingRate)
    tempo_last_30 = compute_tempo(last_30s_audio, samplingRate)
    print("Getting pitch")
    avgPitch = compute_average_pitch(y, samplingRate)
    pitch_first_30 = compute_average_pitch(first_30s_audio, samplingRate)
    pitch_last_30 = compute_average_pitch(last_30s_audio, samplingRate)
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

#TEST IT
if __name__ == "__main__":
    print("I have started up!")
    filepath = "C:/Users/ahmad/OneDrive/Desktop/Project/HeartBeatAlterationUsingAISelectedMusic-main/Nixon.mp3"
    characteristics = get_characteristics(filepath)
    print(characteristics)