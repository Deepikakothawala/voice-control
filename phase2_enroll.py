import sounddevice as sd
import soundfile as sf
import numpy as np

fs = 16000  
duration = 5  

print("System: Get ready to record your Master Voice Profile.")
print("System: Please say something like: 'System, this is my authorized voice profile for access.'")
print("System: Recording will start in 3 seconds...\n")

import time
time.sleep(3)

print(">>> RECORDING NOW (Speak for 5 seconds) <<<")
# Capture the audio
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
sd.wait()  

# PRO-FIX: Save using soundfile to guarantee perfect headers
sf.write('master_profile.wav', myrecording, fs)
print("\nSystem: Success! Master Profile saved as 'master_profile.wav'.")