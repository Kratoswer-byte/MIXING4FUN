import sounddevice as sd

devices = sd.query_devices()
print("\n🔊 DISPOSITIVI CABLE:")
for i, d in enumerate(devices):
    if 'cable' in d['name'].lower():
        print(f"  [{i}] {d['name']}")
        print(f"      Input channels: {d['max_input_channels']}")
        print(f"      Output channels: {d['max_output_channels']}")
        print()
