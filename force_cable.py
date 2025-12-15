import json
import os

config_file = "soundboard_config.json"

# Forza CABLE Input nel config
cable_id = 61  # CABLE Input 2 canali, 48kHz nativo - PERFETTO per Discord!

config = {}
if os.path.exists(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

config['audio_output_device'] = cable_id

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✓ Configurazione salvata con dispositivo {cable_id} (CABLE Input 2ch 48kHz)")
print("\nOra riavvia il soundboard:")
print("$env:PATH += \";$PWD\\ffmpeg-8.0.1-essentials_build\\bin\"; python main.py")
