import os
import pathlib
import shutil
import torch
import numpy as np
import soundfile as sf
import difflib 
import pyautogui
import time 
import pyttsx3 
import psutil  

# ==========================================================
# 1. OS-LEVEL AUDIO PATCHES (Prevents Windows Crashes)
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
    try: original_symlink_to(self, target, target_is_directory)
    except OSError as e:
        if getattr(e, 'winerror', None) == 1314:
            if self.exists(): self.unlink()
            if pathlib.Path(target).is_dir(): shutil.copytree(target, self)
            else: shutil.copy(target, self)
        else: raise
pathlib.Path.symlink_to = safe_symlink_to

# ==========================================================
# 2. INITIALIZE TTS ENGINE (THE MOUTH)
# ==========================================================
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
engine.setProperty('rate', 180) # Slightly faster for production feel

def speak(text):
    print(f"KRIVANTA: {text}")
    engine.say(text)
    engine.runAndWait()

# ==========================================================
# 3. BOOT AI LIBRARIES (EARS & BIOMETRICS)
# ==========================================================
import speech_recognition as sr
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import SpeakerRecognition

print("System: Booting Whisper STT Engine...")
stt_model = WhisperModel("small.en", device="cpu", compute_type="int8")

print("System: Booting Biometric Security Engine...")
verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

# Microphone Production Tuning
recognizer = sr.Recognizer()
recognizer.energy_threshold = 1000 # High threshold to ignore AC units/fans
recognizer.dynamic_energy_threshold = False # Prevents auto-adjusting to noise
recognizer.pause_threshold = 0.5 # Executes immediately after 0.5s of silence

# Ensure Security Directory Exists
if not os.path.exists("authorized_voices"):
    os.makedirs("authorized_voices")
    print("WARNING: 'authorized_voices' folder created. Please add .wav profiles.")

is_sleeping = False

# ==========================================================
# 4. THE COMMAND ENGINE
# ==========================================================
def execute_command(command_text, user_name):
    global is_sleeping

    # --- STATE MANAGEMENT ---
    if is_sleeping:
        if "system wake" in command_text:
            is_sleeping = False
            speak(f"Welcome back, {user_name}. Systems online.")
        return 

    if "system sleep" in command_text:
        is_sleeping = True
        speak("Entering standby mode.")
        return

    # --- DYNAMIC 1: UNIVERSAL MAXIMIZED LAUNCHER ---
    if command_text.startswith("system launch "):
        target = command_text.replace("system launch ", "").strip()
        speak(f"Launching {target}")
        
        # Hits the Windows key, types the app, and hits Enter
        pyautogui.press('win')
        time.sleep(0.5)
        pyautogui.write(target)
        time.sleep(0.8)
        pyautogui.press('enter')
        
        # Attempt to force maximization after 2 seconds
        time.sleep(2)
        pyautogui.hotkey('win', 'up') 
        return

    # --- DYNAMIC 2: HIGH-SPEED DICTATION ---
    if command_text.startswith("system type "):
        text_to_type = command_text.replace("system type ", "").strip()
        print(f">>> DICTATING: {text_to_type}")
        pyautogui.write(text_to_type, interval=0.01) # Types blazing fast
        return

    # --- STATIC CORE 4 COMMANDS ---
    valid_commands = [
        "system status", "system desktop", "system downloads", "system documents",
        "system maximize", "system minimize", "system snap left", "system snap right", 
        "system close window", "system switch app",
        "system browser", "system new tab", "system close tab", 
        "system scroll down", "system scroll up",
        "system mute", "system volume up", "system volume down", "system play media", "system lock pc"
    ]
    
    matches = difflib.get_close_matches(command_text, valid_commands, n=1, cutoff=0.7)
    if not matches:
        return 
        
    cmd = matches[0]
    print(f"\n>>> EXECUTING ACTION: [{cmd.upper()}]")
    
    if cmd == "system status":
        battery = psutil.sensors_battery()
        percent = battery.percent if battery else "unknown"
        speak(f"All systems optimal. Battery is at {percent} percent.")
    elif cmd == "system desktop":
        os.system(r'explorer /n, "C:\Users\lalit\OneDrive\Desktop"')
    elif cmd == "system downloads":
        os.system(r'explorer /n, "C:\Users\lalit\Downloads"')
    elif cmd == "system documents":
        os.system(r'explorer /n, "C:\Users\lalit\Documents"')
        
    elif cmd == "system maximize": pyautogui.hotkey('win', 'up')
    elif cmd == "system minimize": pyautogui.hotkey('win', 'down')
    elif cmd == "system snap left": pyautogui.hotkey('win', 'left')
    elif cmd == "system snap right": pyautogui.hotkey('win', 'right')
    elif cmd == "system close window": pyautogui.hotkey('alt', 'f4')
    elif cmd == "system switch app": pyautogui.hotkey('alt', 'tab')
        
    elif cmd == "system browser": os.system("start chrome https://www.google.com") 
    elif cmd == "system new tab": pyautogui.hotkey('ctrl', 't')
    elif cmd == "system close tab": pyautogui.hotkey('ctrl', 'w')
    elif cmd == "system scroll down": pyautogui.press('pagedown')
    elif cmd == "system scroll up": pyautogui.press('pageup')
        
    elif cmd == "system mute": pyautogui.press('volumemute')
    elif cmd == "system volume up": 
        for _ in range(5): pyautogui.press('volumeup')
    elif cmd == "system volume down": 
        for _ in range(5): pyautogui.press('volumedown')
    elif cmd == "system play media": pyautogui.press('playpause')
    elif cmd == "system lock pc": os.system("rundll32.exe user32.dll,LockWorkStation")

# ==========================================================
# 5. THE PRODUCTION MAIN LOOP
# ==========================================================
with sr.Microphone() as source:
    print("\nSystem: Calibrating microphone for production environment...")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("\n========================================")
    print(" KRIVANTA OS ONLINE. MULTI-USER SECURED.")
    print("========================================\n")
    
    speak("Krivanta OS is online. Awaiting authorized voice input.")

    while True:
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
            temp_filename = "temp_voice_command.wav"
            
            with open(temp_filename, "wb") as f:
                f.write(audio.get_wav_data())
            
            # High-speed transcription
            segments, _ = stt_model.transcribe(
                temp_filename, beam_size=1, vad_filter=True, # Beam size 1 for maximum speed
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            full_text = "".join([s.text.strip() + " " for s in segments])
            clean_text = full_text.lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
            
            if clean_text.startswith("system") or clean_text.startswith("krivanta"):
                print(f"\nProcessing Audio: [{clean_text}]")
                
                access_granted = False
                authorized_user = "Unknown"
                
                # Multi-User Biometric Loop
                for filename in os.listdir("authorized_voices"):
                    if filename.endswith(".wav"):
                        filepath = os.path.join("authorized_voices", filename)
                        score, prediction = verification.verify_files(filepath, temp_filename)
                        
                        # Threshold tuned to 0.15 for balance of security and speed
                        if prediction.item() and score.item() > 0.15:
                            access_granted = True
                            authorized_user = filename.replace(".wav", "").capitalize()
                            break 
                
                if access_granted:
                    print(f">>> BIOMETRICS PASSED: {authorized_user}")
                    execute_command(clean_text, authorized_user)
                else:
                    speak("Access denied.")
                    print("!!! SECURITY ALERT: Voice print not recognized in database.")
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except KeyboardInterrupt:
            speak("Powering down Krivanta OS.")
            break
        except Exception as e:
            pass # Failsafe to prevent OS from crashing on read errors