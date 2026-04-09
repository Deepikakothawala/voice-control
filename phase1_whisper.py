import speech_recognition as sr
from faster_whisper import WhisperModel
import os

# 1. Load the AI Engine
print("System: Booting Whisper AI Engine...")
model = WhisperModel("small.en", device="cpu", compute_type="int8")

# 2. Initialize the Microphone Controller
recognizer = sr.Recognizer()

# PRO-TWEAK: Raise the baseline threshold so fans/breathing don't trigger it
recognizer.energy_threshold = 400 
recognizer.dynamic_energy_threshold = True

# 3. The Core Listening Loop
with sr.Microphone() as source:
    print("System: Calibrating for background noise... Please stay quiet for 2 seconds.")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("System: Calibration Complete. Microphone Active. Start speaking (Ctrl+C to quit).")

    while True:
        try:
            # The system listens until you stop speaking
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
            
            temp_filename = "temp_voice_command.wav"
            with open(temp_filename, "wb") as f:
                f.write(audio.get_wav_data())
            
            # PRO-TWEAK: vad_filter=True completely destroys the "Thank You" hallucinations
            segments, info = model.transcribe(
                temp_filename, 
                beam_size=5, 
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Extract and print the text
            for segment in segments:
                command_text = segment.text.strip()
                if command_text:
                    # We force it to lowercase and remove punctuation here to prep for Phase 3!
                    clean_text = command_text.lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                    print(f"System Heard: [{clean_text}]")
                    
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except KeyboardInterrupt:
            print("\nSystem: Manual Abort. Shutting down.")
            break
        except Exception as e:
            pass