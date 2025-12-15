import sounddevice as sd
import json
import os

print("="*70)
print("DEBUG CONFIGURAZIONE DISPOSITIVO AUDIO")
print("="*70)

# 1. Leggi config salvato
config_file = "soundboard_config.json"
if os.path.exists(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    saved_device = config.get('audio_output_device', None)
    print(f"\n📄 CONFIG FILE:")
    print(f"   Dispositivo salvato: {saved_device}")
else:
    print(f"\n❌ Config file non trovato!")
    saved_device = None

# 2. Device di default
default_device = sd.default.device
print(f"\n🔊 DISPOSITIVO DEFAULT SISTEMA:")
print(f"   ID: {default_device}")
if default_device[1] is not None:
    dev_info = sd.query_devices(default_device[1])
    print(f"   Nome: {dev_info['name']}")
    print(f"   Canali out: {dev_info['max_output_channels']}")

# 3. Trova tutti i CABLE Input
print(f"\n🔍 DISPOSITIVI CABLE INPUT DISPONIBILI:")
devices = sd.query_devices()
cable_devices = []

for i, device in enumerate(devices):
    if "CABLE Input" in device['name'] and device['max_output_channels'] > 0:
        cable_devices.append((i, device))
        print(f"   [{i}] {device['name']}")
        print(f"       Canali: {device['max_output_channels']}")
        print(f"       Sample Rates: {device.get('default_samplerate', 'N/A')} Hz")
        
        # Test compatibilità
        try:
            test_stream = sd.OutputStream(
                samplerate=48000,
                blocksize=512,
                device=i,
                channels=2,
                dtype='float32'
            )
            test_stream.close()
            print(f"       ✅ COMPATIBILE con 48kHz stereo")
        except Exception as e:
            print(f"       ❌ ERRORE: {e}")

if not cable_devices:
    print("   ❌ NESSUN CABLE Input trovato!")

# 4. Quale dispositivo userebbe il mixer?
print(f"\n🎛️  DISPOSITIVO CHE IL MIXER USEREBBE:")
if saved_device is not None:
    try:
        dev_info = sd.query_devices(saved_device)
        print(f"   ID: {saved_device}")
        print(f"   Nome: {dev_info['name']}")
        
        # Verifica se è CABLE
        if "CABLE Input" in dev_info['name']:
            print(f"   ✅ È un CABLE Input (CORRETTO)")
        else:
            print(f"   ❌ NON è CABLE Input (SBAGLIATO!)")
            print(f"   ⚠️  Il soundboard sta usando le cuffie invece di CABLE!")
    except:
        print(f"   ❌ Dispositivo {saved_device} non più disponibile!")
else:
    print(f"   ⚠️  Nessun dispositivo configurato, usa default")

# 5. Raccomandazione
print(f"\n" + "="*70)
print("RACCOMANDAZIONE:")
print("="*70)

if cable_devices:
    best_device = None
    # Preferisci device con 2 canali
    for dev_id, dev_info in cable_devices:
        if dev_info['max_output_channels'] == 2:
            best_device = dev_id
            break
    
    if not best_device:
        best_device = cable_devices[0][0]
    
    print(f"✅ USA DISPOSITIVO {best_device}:")
    print(f"   {devices[best_device]['name']}")
    print(f"\n💡 COMANDO FIX:")
    print(f"   python -c \"import json; c = json.load(open('soundboard_config.json')); c['audio_output_device'] = {best_device}; json.dump(c, open('soundboard_config.json', 'w'), indent=2)\"")
else:
    print("❌ Nessun CABLE Input disponibile!")
    print("   1. Installa VB-Audio Virtual Cable")
    print("   2. Riavvia Voicemeeter")
