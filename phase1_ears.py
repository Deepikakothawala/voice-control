import queue
import sys
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# 1. Setup the Audio Queue (Buffer)
# This ensures if your PC lags, the audio isn't lost; it waits in line.
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    """This function captures audio from the mic and puts it in the queue."""
    if status:
        print(f"Hardware Error: {status}", file=sys.stderr)
    q.put(bytes(indata))

# 2. Load the Offline Model
print("System: Loading Voice Model... Please wait.")
try:
    # This looks for the folder named "model" you created in Step 2
    model = Model("model") 
except Exception as e:
    print("Error: Could not find the 'model' folder. Did you extract and rename it?")
    sys.exit(1)

# 3. Initialize the Recognizer (Setting sample rate to 16000 Hz)
recognizer = KaldiRecognizer(model, 16000)

print("System: Microphone Active. Start speaking (Press Ctrl+C to stop).")

# 4. The Main Listening Loop
try:
    # Open the microphone stream
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            # Pull audio from the queue
            data = q.get()
            
            # If the recognizer detects a complete sentence/phrase
            if recognizer.AcceptWaveform(data):
                # Vosk outputs a JSON string, we need to parse it to get just the text
                result = json.loads(recognizer.Result())
                recognized_text = result.get("text", "")
                
                # Only print if it actually heard words
                if recognized_text:
                    print(f"System Heard: [{recognized_text}]")

except KeyboardInterrupt:
    print("\nSystem: Shutting down listening phase.")
except Exception as e:
    print(f"\nSystem Critical Error: {e}")