import sounddevice as sd
import numpy as np
import time

print("TEST INVIO AUDIO A CABLE INPUT\n")

# Trova CABLE Input
devices = sd.query_devices()
cable_id = None

for i, device in enumerate(devices):
    if "CABLE Input" in device['name'] and device['max_output_channels'] > 0:
        print(f"Trovato: {i} - {device['name']} (canali: {device['max_output_channels']})")
        if cable_id is None:
            cable_id = i

if cable_id is None:
    print("ERRORE: CABLE Input non trovato!")
    exit(1)

print(f"\nUso dispositivo {cable_id}")
print("\nInvio tono test di 3 secondi a 440Hz (La)...")
print("CONTROLLA VOICEMEETER: Il fader di Hardware Input 2 dovrebbe muoversi!\n")

# Genera tono a 440Hz
duration = 3  # secondi
sample_rate = 44100
t = np.linspace(0, duration, int(sample_rate * duration))
tone = 0.3 * np.sin(2 * np.pi * 440 * t)  # Volume 0.3 per sicurezza

# Converti a stereo
tone_stereo = np.column_stack([tone, tone])

try:
    # Riproduci su CABLE Input
    sd.play(tone_stereo, samplerate=sample_rate, device=cable_id)
    
    for i in range(3):
        print(f"Riproduzione in corso... {i+1}/3 secondi")
        time.sleep(1)
    
    sd.wait()
    print("\n✓ Test completato!")
    print("\nSe il fader in Voicemeeter NON si è mosso:")
    print("1. Voicemeeter Hardware Input 2 NON è impostato su 'CABLE Output'")
    print("2. Oppure Voicemeeter non è in esecuzione")
    
except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    print("\nProblema nell'invio audio a CABLE Input")
