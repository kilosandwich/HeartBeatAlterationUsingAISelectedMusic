import librosa
import numpy as np

def load_audio_segment(audioInfo, samplingRate, startTime, durationTime):
    return audioInfo[int(startTime * samplingRate):int((startTime + durationTime) * samplingRate)]

def compute_tempo(audioInfo, samplingRate):
    return librosa.beat.beat_track(y=audioInfo, sr=samplingRate)[0]

def compute_average_pitch(audioInfo, samplingRate):
    pitches, _ = librosa.piptrack(y=audioInfo, sr=samplingRate)
    return np.mean(pitches[pitches > 0])

def get_characteristics(filepath):
    y, samplingRate = librosa.load(filepath)
    songLength = librosa.get_duration(y=y, sr=samplingRate)
    avgTempo = compute_tempo(y, samplingRate)
    first_30s_audio = load_audio_segment(y, samplingRate, 0, 30)
    last_30s_audio = load_audio_segment(y, samplingRate, max(0, songLength - 30), 30)
    tempo_first_30 = compute_tempo(first_30s_audio, samplingRate)
    tempo_last_30 = compute_tempo(last_30s_audio, samplingRate)
    avgPitch = compute_average_pitch(y, samplingRate)
    pitch_first_30 = compute_average_pitch(first_30s_audio, samplingRate)
    pitch_last_30 = compute_average_pitch(last_30s_audio, samplingRate)

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
    filepath = "Nixon.mp3"
    characteristics = get_characteristics(filepath)
    print(characteristics)