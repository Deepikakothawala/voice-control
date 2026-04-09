import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import pathlib
import shutil
import torch

# --- PRO-LEVEL MONKEY PATCH 1: TORCHAUDIO BUG ---
import torchaudio
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: [""]

# --- THE ULTIMATE BYPASS: FFmpeg & Shape Bug Fix ---
def safe_audio_load(filepath, *args, **kwargs):
    data, samplerate = sf.read(str(filepath), dtype='float32')
    
    # Check if SpeechBrain wants Channels First or Time First
    channels_first = kwargs.get('channels_first', True)
    
    if len(data.shape) == 1:
        # Mono audio
        if channels_first:
            data = data.reshape(1, -1) # [Channels, Time]
        else:
            data = data.reshape(-1, 1) # [Time, Channels]
    else:
        # Stereo audio
        if channels_first:
            data = data.transpose()
            
    return torch.from_numpy(data), samplerate

torchaudio.load = safe_audio_load
# --------------------------------------------------------

# --- PRO-LEVEL MONKEY PATCH 2: WINDOWS SYMLINK BUG (WinError 1314) ---
original_symlink_to = pathlib.Path.symlink_to

def safe_symlink_to(self, target, target_is_directory=False):
    try:
        original_symlink_to(self, target, target_is_directory)
    except OSError as e:
        if getattr(e, 'winerror', None) == 1314:
            if self.exists():
                self.unlink()
            if pathlib.Path(target).is_dir():
                shutil.copytree(target, self)
            else:
                shutil.copy(target, self)
        else:
            raise

pathlib.Path.symlink_to = safe_symlink_to
# --------------------------------------------------------------------

from speechbrain.inference.speaker import SpeakerRecognition

print("System: Booting Biometric Security Model...")
verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

fs = 16000
duration = 4

print("\nSystem: Security Gate Active.")
print("System: Say a random command like 'System access downloads'...")
print("\n>>> RECORDING NOW (4 seconds) <<<")

test_audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
sd.wait()

sf.write('test_audio.wav', test_audio, fs)
print("System: Audio captured. Analyzing vocal biometrics...\n")

score, prediction = verification.verify_files("master_profile.wav", "test_audio.wav")

match_score = score.item()
is_match = prediction.item()

print(f"Biometric Similarity Score: {match_score:.2f}")

if is_match and match_score > 0.25:
    print(">>> ACCESS GRANTED: Voice matches Master Profile.")
else:
    print(">>> ACCESS DENIED: Unauthorized user detected.")

if os.path.exists('test_audio.wav'):
    os.remove('test_audio.wav')