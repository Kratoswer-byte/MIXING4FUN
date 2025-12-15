import sounddevice as sd
import numpy as np
import time

print("="*60)
print("TEST COMPLETO CATENA AUDIO - SOUNDBOARD → VOICEMEETER")
print("="*60)

# 1. Trova CABLE Input
devices = sd.query_devices()
cable_id = 22

device_info = sd.query_devices(cable_id)
print(f"\n📤 DISPOSITIVO OUTPUT SOUNDBOARD:")
print(f"   ID: {cable_id}")
print(f"   Nome: {device_info['name']}")
print(f"   Sample Rate: 48000 Hz")
print(f"   Canali: 2 (Stereo)")

# 2. Genera diversi toni per test qualità
print(f"\n🔊 INVIO SEQUENZA DI TEST:")
print(f"   Ti permetterà di verificare cosa arriva in Voicemeeter e Discord\n")

tests = [
    ("Tono 440Hz (La) - BASSO VOLUME", 440, 0.15, 2),
    ("Tono 880Hz (La alto) - VOLUME MEDIO", 880, 0.25, 2),
    ("Tono 220Hz (La basso) - VOLUME NORMALE", 220, 0.30, 2),
]

sample_rate = 48000

for i, (desc, freq, volume, duration) in enumerate(tests, 1):
    print(f"\n[TEST {i}/3] {desc}")
    print(f"   Controlla in Voicemeeter: Hardware Input 2")
    print(f"   Controlla in Discord: Fai 'Test Microfono'")
    print(f"   Riproduci tra: ", end="", flush=True)
    
    for countdown in range(3, 0, -1):
        print(f"{countdown}...", end="", flush=True)
        time.sleep(1)
    print("GO!")
    
    # Genera tono
    t = np.linspace(0, duration, int(sample_rate * duration))
    tone = volume * np.sin(2 * np.pi * freq * t)
    tone_stereo = np.column_stack([tone, tone])
    
    # Riproduci
    sd.play(tone_stereo, samplerate=sample_rate, device=cable_id)
    sd.wait()
    
    print(f"   ✓ Completato!")
    time.sleep(1)

print("\n" + "="*60)
print("VERIFICA RISULTATI:")
print("="*60)
print("""
✅ TUTTO OK se:
   1. In Voicemeeter vedi il fader di Hardware Input 2 muoversi
   2. I toni sono PULITI, CHIARI, senza distorsione
   3. In Discord (Test Microfono) vedi il livello muoversi
   4. L'audio che senti è identico a quello che vedi sui fader

❌ PROBLEMI se:
   1. Toni sgranati/distorti → Volume troppo alto o sample rate sbagliato
   2. Fader non si muove → Hardware Input 2 NON è su "CABLE Output"
   3. Discord non riceve → B1 non attivo su Input 2
   4. Non senti nulla → A1 non attivo o dispositivo A1 sbagliato

🔧 SETUP CORRETTO:
   Voicemeeter Hardware Input 2:
   - Dispositivo: WDM: CABLE Output (VB-Audio Virtual Cable)
   - A1: ✅ ON (verde) - per sentire nelle cuffie
   - B1: ✅ ON (arancione) - per inviare a Discord
   - Fader: -6dB / -12dB (NON a 0dB!)
   
   Voicemeeter Sample Rate:
   - Menu → System Settings → 48000 Hz
""")
