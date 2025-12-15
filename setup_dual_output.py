import json

# Configurazione Dual Output
# Output primario: CABLE Input (61) -> Voicemeeter -> Discord
# Output secondario: Cuffie -> Per sentirti le clip

PRIMARY_DEVICE = 61  # CABLE Input 2ch 48kHz
SECONDARY_DEVICE = 105  # Headphones (Realtek HD Audio 2nd output) - CAMBIA SE NECESSARIO

# Device disponibili che potrebbero essere le cuffie:
# 105 - Headphones (Realtek HD Audio 2nd output)
# 106 - Speakers (Realtek HD Audio output)
# 13/39/54 - Altoparlanti (2- USB Audio Device)
# 17/43/56 - Altoparlanti (M-Audio M-Track Solo)

print("=" * 70)
print("CONFIGURAZIONE DUAL OUTPUT")
print("=" * 70)
print(f"\n✓ Output Primario: {PRIMARY_DEVICE} (CABLE Input -> Voicemeeter -> Discord)")
print(f"✓ Output Secondario: {SECONDARY_DEVICE} (Cuffie -> Ascolto diretto)")
print("\n⚠️  Se il device {SECONDARY_DEVICE} non è corretto, modifica SECONDARY_DEVICE nel file")
print()

# Carica config
with open('soundboard_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Imposta dual output
config['audio_output_device'] = PRIMARY_DEVICE
config['secondary_output_device'] = SECONDARY_DEVICE

# Salva
with open('soundboard_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✓ Configurazione salvata!")
print("\nOra avvia la soundboard con: python main.py")
print("L'audio sarà inviato CONTEMPORANEAMENTE a:")
print(f"  1. Device {PRIMARY_DEVICE} (CABLE -> Voicemeeter -> Discord)")
print(f"  2. Device {SECONDARY_DEVICE} (Cuffie)")
