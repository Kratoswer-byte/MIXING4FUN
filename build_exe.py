"""
Script per creare l'eseguibile del Gaming Soundboard
Usa PyInstaller per creare un file .exe con icona personalizzata
"""

import os
import subprocess
import sys

def build_exe():
    """Crea l'eseguibile usando PyInstaller"""
    
    print("🔨 Creazione eseguibile Gaming Soundboard...")
    print("=" * 60)
    
    # Parametri PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',                    # Un singolo file exe
        '--windowed',                   # Senza console (GUI)
        '--icon=soundbar.ico',          # Icona personalizzata
        '--name=SoundboardMixing4Fun',  # Nome del file exe
        '--add-data=ffmpeg-8.0.1-essentials_build;ffmpeg-8.0.1-essentials_build',  # Include ffmpeg
        '--add-data=clips;clips',       # Include cartella clips
        '--hidden-import=pystray',      # Importazioni nascoste
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=sounddevice',
        '--hidden-import=soundfile',
        '--hidden-import=numpy',
        '--hidden-import=customtkinter',
        '--hidden-import=yt_dlp',
        'main.py'
    ]
    
    print("Comando PyInstaller:")
    print(" ".join(cmd))
    print("=" * 60)
    
    # Esegui PyInstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        print("\n" + "=" * 60)
        print("✅ Eseguibile creato con successo!")
        print("📁 Percorso: dist/SoundboardMixing4Fun.exe")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print("❌ Errore durante la creazione dell'eseguibile:")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ PyInstaller non trovato!")
        print("\n📦 Installa PyInstaller con:")
        print("   pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
