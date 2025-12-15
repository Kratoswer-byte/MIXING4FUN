"""
Script per verificare disponibilità driver ASIO e Virtual Cable
"""
import sounddevice as sd

print("=" * 60)
print("VERIFICA DRIVER AUDIO")
print("=" * 60)

devices = sd.query_devices()
host_apis = sd.query_hostapis()

# Cerca ASIO
asio_devices = []
virtual_devices = []
wasapi_devices = []

for i, device in enumerate(devices):
    name = device['name'].lower()
    hostapi_idx = device['hostapi']
    hostapi_name = host_apis[hostapi_idx]['name'] if hostapi_idx < len(host_apis) else 'Unknown'
    
    # Identifica ASIO
    if 'asio' in name or 'ASIO' in hostapi_name:
        asio_devices.append((i, device))
    
    # Identifica Virtual Cable (solo WASAPI per evitare duplicati)
    if 'WASAPI' in hostapi_name:
        if 'cable' in name or 'virtual' in name or 'voicemeeter' in name:
            virtual_devices.append((i, device))
        wasapi_devices.append((i, device))

# Stampa risultati
print("\n✅ DRIVER ASIO TROVATI:")
if asio_devices:
    for idx, dev in asio_devices:
        print(f"   [{idx}] {dev['name']}")
        print(f"       Input: {dev['max_input_channels']} | Output: {dev['max_output_channels']}")
        print(f"       Sample Rate: {dev['default_samplerate']} Hz")
else:
    print("   ❌ Nessun driver ASIO trovato")
    print("   💡 Installa ASIO4ALL: https://www.asio4all.org/")

print("\n✅ DISPOSITIVI VIRTUALI TROVATI:")
if virtual_devices:
    for idx, dev in virtual_devices:
        print(f"   [{idx}] {dev['name']}")
        print(f"       Input: {dev['max_input_channels']} | Output: {dev['max_output_channels']}")
        print(f"       Sample Rate: {dev['default_samplerate']} Hz")
else:
    print("   ❌ Nessun dispositivo virtuale trovato")
    print("   💡 Installa VB-Audio Cable: https://vb-audio.com/Cable/")

print("\n" + "=" * 60)
print("DISPOSITIVI WASAPI (consigliati, senza duplicati):")
print("=" * 60)
for i, device in wasapi_devices:
    if device['max_output_channels'] > 0 or device['max_input_channels'] > 0:
        io = []
        if device['max_input_channels'] > 0:
            io.append(f"IN:{device['max_input_channels']}")
        if device['max_output_channels'] > 0:
            io.append(f"OUT:{device['max_output_channels']}")
        
        default_in = " [DEF_IN]" if i == sd.default.device[0] else ""
        default_out = " [DEF_OUT]" if i == sd.default.device[1] else ""
        
        print(f"[{i:2d}] {device['name']}")
        print(f"     {' / '.join(io)} | {device['default_samplerate']}Hz{default_in}{default_out}")

print("\n✅ Configurazione consigliata per mixer:")
print("=" * 60)

# Suggerisci setup migliore
primary_out = None
secondary_out = None
virtual_in = None

for idx, dev in enumerate(devices):
    name = dev['name'].lower()
    if 'speakers' in name or 'headphones' in name or 'm-audio' in name:
        if primary_out is None and dev['max_output_channels'] > 0:
            primary_out = (idx, dev['name'])
    if 'cable input' in name:
        if secondary_out is None and dev['max_output_channels'] > 0:
            secondary_out = (idx, dev['name'])
    if 'cable output' in name:
        if virtual_in is None and dev['max_input_channels'] > 0:
            virtual_in = (idx, dev['name'])

if primary_out:
    print(f"🔊 Output Primario: [{primary_out[0]}] {primary_out[1]}")
else:
    print("🔊 Output Primario: [Default system]")

if secondary_out:
    print(f"🎧 Virtual Output: [{secondary_out[0]}] {secondary_out[1]}")
    print("   → Usa questo per mandare audio a Discord/OBS")
else:
    print("⚠️  Virtual Output: Non configurato (installa VB-Cable)")

if virtual_in:
    print(f"🎤 Virtual Input: [{virtual_in[0]}] {virtual_in[1]}")
    print("   → Usa questo per catturare il desktop audio")
else:
    print("⚠️  Virtual Input: Non configurato")

print("=" * 60)
