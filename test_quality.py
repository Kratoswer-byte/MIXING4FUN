import sounddevice as sd
import soundfile as sf
import numpy as np

print("TEST QUALITÀ AUDIO SU CABLE INPUT\n")

# Genera tono pulito a 48kHz (standard Discord)
duration = 2
sample_rate = 48000
freq = 440

t = np.linspace(0, duration, int(sample_rate * duration))
tone = 0.2 * np.sin(2 * np.pi * freq * t)  # Volume moderato
tone_stereo = np.column_stack([tone, tone])

# Trova CABLE Input
devices = sd.query_devices()
cable_id = 22

print(f"Invio tono test a 48kHz (qualità Discord)...")
print("Controlla in Discord se senti un tono pulito e chiaro\n")

try:
    sd.play(tone_stereo, samplerate=sample_rate, device=cable_id)
    sd.wait()
    print("✓ Test completato!")
    print("\nSe senti ancora sgranato:")
    print("1. Voicemeeter sample rate NON è 48000 Hz")
    print("2. Volume troppo alto (distorsione)")
    print("3. Discord non è impostato su alta qualità")
except Exception as e:
    print(f"Errore: {e}")
