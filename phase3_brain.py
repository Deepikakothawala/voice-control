import os
import pathlib
import shutil
import torch
import numpy as np
import soundfile as sf
import sounddevice as sd
import difflib # <-- NEW: The Fuzzy Matching Autocorrect Brain

# ==========================================================
# 1. ACTIVATE PRO-LEVEL MONKEY PATCHES FIRST!
# ==========================================================
import torchaudio
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: [""]

def safe_audio_load(filepath, *args, **kwargs):
    data, samplerate = sf.read(str(filepath), dtype='float32')
    channels_first = kwargs.get('channels_first', True)
    if len(data.shape) == 1:
        if channels_first: data = data.reshape(1, -1)
        else: data = data.reshape(-1, 1)
    else:
        if channels_first: data = data.transpose()
    return torch.from_numpy(data), samplerate
torchaudio.load = safe_audio_load

original_symlink_to = pathlib.Path.symlink_to
def safe_symlink_to(self, target, target_is_directory=False):
    try:
        original_symlink_to(self, target, target_is_directory)
    except OSError as e:
        if getattr(e, 'winerror', None) == 1314:
            if self.exists(): self.unlink()
            if pathlib.Path(target).is_dir(): shutil.copytree(target, self)
            else: shutil.copy(target, self)
        else: raise
pathlib.Path.symlink_to = safe_symlink_to

# ==========================================================
# 2. LOAD AI LIBRARIES
# ==========================================================
import speech_recognition as sr
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import SpeakerRecognition
import pyautogui

# ==========================================================
# 3. BOOT SEQUENCE
# ==========================================================
print("System: Booting Voice Engine...")
stt_model = WhisperModel("small.en", device="cpu", compute_type="int8")

print("System: Booting Biometric Security...")
verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 400 
recognizer.dynamic_energy_threshold = True

# ==========================================================
# 4. THE COMMAND DICTIONARY (THE UPGRADED SMART BRAIN)
# ==========================================================
def execute_command(command_text):
    # Our list of absolute valid commands
    valid_commands = [
        "system access downloads", 
        "system access desktop",
        "system terminate window", 
        "system task switch",
        "system browser launch", 
        "system tab open", 
        "system tab close"
    ]
    
    # NEW: Fuzzy matching! It finds the closest valid command.
    # cutoff=0.7 means it requires at least a 70% match to prevent accidental triggers.
    matches = difflib.get_close_matches(command_text, valid_commands, n=1, cutoff=0.7)
    
    if not matches:
        print(f">>> UNKNOWN COMMAND: Heard [{command_text}] - No close matches found.")
        return
        
    matched_cmd = matches[0]
    print(f"\n>>> AUTOCORRECTED [{command_text}] -> [{matched_cmd}]")
    
    # Core OS Commands (Using foolproof Windows shell commands)
    if matched_cmd == "system access downloads":
        print(">>> EXECUTING: OPEN DOWNLOADS")
        os.system("explorer shell:Downloads")
        
    elif matched_cmd == "system access desktop":
        print(">>> EXECUTING: OPEN DESKTOP")
        os.system("explorer shell:Desktop")
        
    # Window Management
    elif matched_cmd == "system terminate window":
        print(">>> EXECUTING: CLOSE WINDOW")
        pyautogui.hotkey('alt', 'f4')
        
    elif matched_cmd == "system task switch":
        print(">>> EXECUTING: ALT-TAB")
        pyautogui.hotkey('alt', 'tab')
        
    # Web Browsing
    elif matched_cmd == "system browser launch":
        print(">>> EXECUTING: LAUNCH BROWSER")
        # Forcing a URL bypasses the profile picker!
        os.system("start chrome https://www.google.com")
        
    elif matched_cmd == "system tab open":
        print(">>> EXECUTING: NEW TAB")
        pyautogui.hotkey('ctrl', 't')
        
    elif matched_cmd == "system tab close":
        print(">>> EXECUTING: CLOSE TAB")
        pyautogui.hotkey('ctrl', 'w')

# ==========================================================
# 5. THE MAIN LOOP
# ==========================================================
with sr.Microphone() as source:
    print("\nSystem: Calibrating for background noise... (2 seconds)")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("\n========================================")
    print("ALL SYSTEMS GREEN. AWAITING COMMANDS.")
    print("========================================\n")

    while True:
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
            temp_filename = "temp_voice_command.wav"
            
            with open(temp_filename, "wb") as f:
                f.write(audio.get_wav_data())
            
            segments, _ = stt_model.transcribe(
                temp_filename, beam_size=5, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            full_text = ""
            for segment in segments:
                full_text += segment.text.strip() + " "
                
            clean_text = full_text.lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
            
            if clean_text.startswith("system"):
                print(f"\nWake Word Detected. Raw Audio: [{clean_text}]")
                print("Verifying Biometrics...")
                
                score, prediction = verification.verify_files("master_profile.wav", temp_filename)
                
                if prediction.item() and score.item() > 0.25:
                    print(f"Access Granted (Score: {score.item():.2f})")
                    execute_command(clean_text)
                else:
                    print(f"!!! ACCESS DENIED !!! Unauthorized user. (Score: {score.item():.2f})")
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except KeyboardInterrupt:
            print("\nSystem: Manual Abort. Shutting down.")
            break
        except Exception as e:
            pass