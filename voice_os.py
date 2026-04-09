import os
import pathlib
import shutil
import torch
import numpy as np
import soundfile as sf
import sounddevice as sd
import difflib 
import pyautogui
import time 
import pyttsx3 
import psutil  
import easyocr # NEW: The Vision AI
import mss     # NEW: The High-Speed Screenshot Engine
import cv2     # NEW: Image processing

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
# 2. INITIALIZE ENGINES (MOUTH & EYES)
# ==========================================================
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
engine.setProperty('rate', 175)

def speak(text):
    print(f"KRIVANTA: {text}")
    engine.say(text)
    engine.runAndWait()

print("System: Booting Vision AI (This takes a moment)...")
# Initialize the OCR reader. It will use CPU if no compatible GPU is found.
ocr_reader = easyocr.Reader(['en']) 

# ==========================================================
# 3. LOAD AUDIO AI LIBRARIES (EARS & BOUNCER)
# ==========================================================
import speech_recognition as sr
from faster_whisper import WhisperModel
from speechbrain.inference.speaker import SpeakerRecognition

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

is_sleeping = False

# ==========================================================
# 4. THE COMMAND DICTIONARY (THE KRIVANTA BRAIN)
# ==========================================================
def execute_command(command_text):
    global is_sleeping

    if is_sleeping:
        if "system wake" in command_text:
            is_sleeping = False
            speak("Systems reactivated. I am listening.")
        return 

    if "system sleep" in command_text:
        is_sleeping = True
        speak("Entering standby mode.")
        return

    # --- DYNAMIC 1: THE SIGHT ENGINE (NEW) ---
    if command_text.startswith("system sight click "):
        target_word = command_text.replace("system sight click ", "").strip().lower()
        speak(f"Scanning for {target_word}")
        print(f">>> EXECUTING OCR SCAN FOR: [{target_word.upper()}]")
        
        with mss.mss() as sct:
            # 1. Take a screenshot of the main monitor
            monitor = sct.monitors[1]
            screenshot = np.array(sct.grab(monitor))
            
            # 2. Convert to grayscale to make the AI read it faster
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
            
            # 3. Read all the text on the screen
            results = ocr_reader.readtext(gray)
            
            # 4. Hunt for the target word
            found = False
            for (bbox, text, prob) in results:
                if target_word in text.lower():
                    # Calculate the exact dead-center X and Y coordinates of the word
                    center_x = int((bbox[0][0] + bbox[2][0]) / 2) + monitor["left"]
                    center_y = int((bbox[0][1] + bbox[2][1]) / 2) + monitor["top"]
                    
                    pyautogui.click(center_x, center_y)
                    speak("Clicking target.")
                    found = True
                    break # Stop looking once we click it
            
            if not found:
                speak(f"I cannot see {target_word} on the screen.")
        return

    # --- DYNAMIC 2: UNIVERSAL LAUNCHER ---
    if command_text.startswith("system launch "):
        target = command_text.replace("system launch ", "").strip()
        speak(f"Launching {target}")
        pyautogui.press('win')
        time.sleep(0.5)
        pyautogui.write(target)
        time.sleep(0.8)
        pyautogui.press('enter')
        return

    # --- DYNAMIC 3: DICTATION MODE ---
    if command_text.startswith("system type "):
        text_to_type = command_text.replace("system type ", "").strip()
        speak("Typing")
        pyautogui.write(text_to_type)
        return

    # --- STRICT SHORTCUT COMMANDS ---
    valid_commands = [
        "system status", "system desktop", "system downloads", "system documents", "system drives",
        "system go up", "system go back", 
        "system maximize", "system minimize", "system snap left", "system snap right", 
        "system close window", "system switch app",
        "system browser", "system new tab", "system close tab", "system recover tab", "system next tab",
        "system scroll down", "system scroll up",
        "system mute", "system volume up", "system volume down", "system play media", "system lock pc"
    ]
    
    matches = difflib.get_close_matches(command_text, valid_commands, n=1, cutoff=0.7)
    if not matches:
        return 
        
    cmd = matches[0]
    print(f"\n>>> EXECUTING: [{cmd.upper()}]")
    
    if cmd == "system status":
        battery = psutil.sensors_battery()
        percent = battery.percent if battery else "unknown"
        speak(f"All systems operational. Battery is at {percent} percent.")
    elif cmd == "system desktop":
        os.system(r'explorer /n, "C:\Users\lalit\OneDrive\Desktop"')
    elif cmd == "system downloads":
        os.system(r'explorer /n, "C:\Users\lalit\Downloads"')
    elif cmd == "system documents":
        os.system(r'explorer /n, "C:\Users\lalit\Documents"')
    elif cmd == "system drives":
        os.system(r'explorer /n, "shell:::{20D04FE0-3AEA-1069-A2D8-08002B30309D}"') 
    elif cmd == "system go up":
        pyautogui.hotkey('alt', 'up')
    elif cmd == "system go back":
        pyautogui.hotkey('alt', 'left')
    elif cmd == "system maximize":
        pyautogui.hotkey('win', 'up')
    elif cmd == "system minimize":
        pyautogui.hotkey('win', 'down')
    elif cmd == "system snap left":
        pyautogui.hotkey('win', 'left')
    elif cmd == "system snap right":
        pyautogui.hotkey('win', 'right')
    elif cmd == "system close window":
        pyautogui.hotkey('alt', 'f4')
    elif cmd == "system switch app":
        pyautogui.hotkey('alt', 'tab')
    elif cmd == "system browser":
        os.system("start chrome https://www.google.com") 
    elif cmd == "system new tab":
        pyautogui.hotkey('ctrl', 't')
    elif cmd == "system close tab":
        pyautogui.hotkey('ctrl', 'w')
    elif cmd == "system recover tab":
        pyautogui.hotkey('ctrl', 'shift', 't')
    elif cmd == "system next tab":
        pyautogui.hotkey('ctrl', 'tab')
    elif cmd == "system scroll down":
        pyautogui.press('pagedown')
    elif cmd == "system scroll up":
        pyautogui.press('pageup')
    elif cmd == "system mute":
        pyautogui.press('volumemute')
    elif cmd == "system volume up":
        for _ in range(5): pyautogui.press('volumeup')
    elif cmd == "system volume down":
        for _ in range(5): pyautogui.press('volumedown')
    elif cmd == "system play media":
        pyautogui.press('playpause')
    elif cmd == "system lock pc":
        os.system("rundll32.exe user32.dll,LockWorkStation")

# ==========================================================
# 5. THE MAIN LOOP
# ==========================================================
with sr.Microphone() as source:
    print("\nSystem: Calibrating for background noise... (2 seconds)")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("\n========================================")
    print(" KRIVANTA CORE ONLINE. MACHINE VISION ACTIVE.")
    print("========================================\n")
    
    speak("Krivanta core is online with visual processing active.")

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
                print(f"\nWake Word Detected: [{clean_text}]")
                
                score, prediction = verification.verify_files("master_profile.wav", temp_filename)
                
                if prediction.item() and score.item() > 0.10:
                    execute_command(clean_text)
                else:
                    print(f"!!! ACCESS DENIED !!! Unauthorized user. (Score: {score.item():.2f})")
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        except KeyboardInterrupt:
            speak("Shutting down the Krivanta core. Goodbye.")
            break
        except Exception as e:
            pass