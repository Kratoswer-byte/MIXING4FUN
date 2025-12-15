import json

config_file = "soundboard_config.json"

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("CLIP CARICATE NEL CONFIG:")
print("="*60)

for i, clip in enumerate(config.get('clips', []), 1):
    print(f"\n[{i}] {clip['name']}")
    print(f"    Path: {clip['path']}")
    print(f"    Hotkey: {clip.get('hotkey', 'NESSUNO')}")
    print(f"    Volume: {clip.get('volume', 1.0)}")

print("\n" + "="*60)
print(f"TOTALE CLIP: {len(config.get('clips', []))}")

if len(config.get('clips', [])) > 1:
    print("\n⚠️  HAI PIÙ CLIP - verifica che abbiano hotkey DIVERSI!")
    hotkeys = [c.get('hotkey') for c in config.get('clips', []) if c.get('hotkey')]
    if len(hotkeys) != len(set(hotkeys)):
        print("❌ PROBLEMA: Ci sono hotkey DUPLICATI!")
        for hk in set(hotkeys):
            count = hotkeys.count(hk)
            if count > 1:
                print(f"   '{hk}' usato {count} volte")
    else:
        print("✅ Tutti gli hotkey sono unici")
