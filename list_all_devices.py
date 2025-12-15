import sounddevice as sd

print("=" * 70)
print("TUTTI I DISPOSITIVI AUDIO")
print("=" * 70)

devices = sd.query_devices()
for i, device in enumerate(devices):
    if device['max_output_channels'] > 0:  # Solo dispositivi di output
        print(f"\n[{i}] {device['name']}")
        print(f"    Canali out: {device['max_output_channels']}")
        print(f"    Sample Rate: {device['default_samplerate']} Hz")
