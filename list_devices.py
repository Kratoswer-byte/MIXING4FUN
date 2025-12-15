import sounddevice as sd

devices = sd.query_devices()
print(f"Default device: {sd.default.device}\n")
print("Dispositivi OUTPUT disponibili:\n")

for i, device in enumerate(devices):
    if device['max_output_channels'] > 0:
        default_mark = " [DEFAULT]" if i == sd.default.device[1] else ""
        print(f"{i}: {device['name']} (canali: {device['max_output_channels']}){default_mark}")
