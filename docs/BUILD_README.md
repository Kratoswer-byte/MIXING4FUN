# 🔨 Build Instructions - Gaming Soundboard

## Creare l'Eseguibile (.exe)

### Prerequisiti

Installa PyInstaller:
```powershell
pip install pyinstaller
```

### Metodo 1: Script Automatico (Raccomandato)

Esegui lo script di build:
```powershell
python build_exe.py
```

### Metodo 2: Usa il file .spec

Usa il file di configurazione avanzata:
```powershell
pyinstaller SoundboardMixing4Fun.spec
```

### Metodo 3: Comando Manuale

```powershell
pyinstaller --onefile --windowed --icon=soundbar.ico --name=SoundboardMixing4Fun --add-data="ffmpeg-8.0.1-essentials_build;ffmpeg-8.0.1-essentials_build" --add-data="clips;clips" main.py
```

---

## 📁 Output

Dopo la build, troverai:

```
dist/
└── SoundboardMixing4Fun.exe  ← Eseguibile finale
```

Il file `.exe` include:
- ✅ Icona personalizzata (`soundbar.ico`)
- ✅ FFmpeg integrato
- ✅ Tutte le dipendenze Python
- ✅ Funzionalità system tray
- ✅ Cartella clips

---

## 🚀 Distribuzione

Per distribuire il programma:

1. **Copia i seguenti file/cartelle:**
   ```
   SoundboardMixing4Fun.exe
   clips/  (facoltativo, per clip precaricate)
   ```

2. **L'utente deve avere:**
   - Windows 10/11
   - VB-Audio Virtual Cable (per routing audio)
   - Voicemeeter (opzionale, per mixing avanzato)

---

## 🛠️ Troubleshooting Build

### Errore: "PyInstaller non trovato"
```powershell
pip install pyinstaller
```

### Errore: "ffmpeg not found"
Verifica che la cartella `ffmpeg-8.0.1-essentials_build` esista nel progetto.

### Exe troppo grande
L'exe sarà circa 100-200 MB perché include:
- FFmpeg (50+ MB)
- Python runtime
- Librerie audio (numpy, sounddevice, etc.)

Per ridurre le dimensioni, usa UPX (già abilitato in .spec):
```powershell
pip install pyinstaller[encryption]
```

### Antivirus blocca l'exe
Questo è normale per exe creati con PyInstaller. Soluzioni:
- Aggiungi eccezione nell'antivirus
- Firma digitalmente l'exe (richiede certificato)

---

## 📝 Note

- **Prima build:** Può richiedere 5-10 minuti
- **Build successive:** Più veloci (~2-3 minuti)
- **Dimensione finale:** ~150-250 MB
- **Compatibilità:** Windows 10/11 (64-bit)

---

*Build script by MIXING4FUN*
