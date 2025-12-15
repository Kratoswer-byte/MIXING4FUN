# 🎮 Gaming Soundboard - Mix Voce + Clip Audio

Una soundboard professionale per **far sentire clip audio + la tua voce contemporaneamente** in Discord, TeamSpeak e altre chat vocali durante il gaming!

## ✨ Caratteristiche

### 🎮 Gaming-Focused
- **Hotkeys configurabili** - Assegna tasti (F1-F12, numpad, etc.) per lanciare le clip al volo
- **Mix Mic + Clip** - Gli altri sentono la tua voce E le clip contemporaneamente
- **Zero lag** - Latenza minima per performance in tempo reale
- **Interfaccia semplice** - Progettata per uso rapido durante il gioco

### �️ **NUOVO! MIXER PROFESSIONALE INTEGRATO**
- **5 Canali Input** (3 Hardware + 2 Virtual) - Microfono + Desktop Audio
- **5 Bus Output** (A1-A5) - Multi-output simultaneo verso più dispositivi
- **Routing Matrix** - Routing libero tra qualsiasi input e output
- **VU Meters Real-Time** - Monitoraggio livelli con peak hold
- **Fader -60dB a +12dB** - Controllo preciso volume per canale
- **Sostituisce Voicemeeter** - Non serve software esterno!
- **📖 Guida completa**: `MIXER_INTEGRATO.md`

### 🎬 YouTube Downloader & Editor Avanzato
- **Scarica da YouTube** - Estrai audio direttamente da video YouTube
- **Taglia con timestamp** - Scarica solo la parte che ti serve
- **Editor professionale** - Normalizza, Fade, Rimuovi silenzi
- **Batch processing** - Converti più file contemporaneamente
- **Formato multiplo** - WAV, MP3, OGG

### 🎚️ Controlli Audio
- **Volume indipendente** per ogni clip
- **Controllo microfono** dedicato
- **Master volume** per il mix finale
- **Loop automatico** per clip ripetute

### 🎛️ Effetti Audio
- **Reverb** - Aggiungi profondità
- **Bass Boost** - Equalizzatore bassi
- **Limiter automatico** - Zero distorsione

### 🔴 Registrazione
- **Registra i momenti epici** - Salva il mix in WAV di alta qualità

## 🚀 QUICK START

### 1️⃣ Installa le Dipendenze

```powershell
pip install -r requirements.txt
```

### 2️⃣ Installa VB-Audio Cable (IMPORTANTE!)

**Questo è NECESSARIO per far funzionare tutto:**
1. Scarica da: https://vb-audio.com/Cable/
2. Installa come Amministratore
3. Riavvia il PC

📖 **Leggi le guide complete**: 
- `SETUP_GAMING.md` - Setup generale
- `SETUP_MICROFONO.md` - Setup microfono dettagliato

### 3️⃣ Configura Audio

**Windows:**
- Output → **CABLE Input**

**Discord/TeamSpeak:**
- Input → **CABLE Output**

### 4️⃣ Avvia la Soundboard

```powershell
python main.py
```

## 🎯 COME USARE

### Aggiungi Clip Audio
1. Clicca **"➕ Aggiungi Clip Audio"**
2. Seleziona il tuo file audio
3. La clip appare nella griglia

### 🎬 NUOVO! Scarica da YouTube
1. Click **"🎬 YouTube & Editor"** nella soundboard
2. Incolla URL YouTube
3. (Opzionale) Imposta timestamp inizio/fine
4. Scarica e salva
5. Aggiungi alla soundboard!

📖 **Guida completa**: `GUIDA_EDITOR.md`

### Assegna Tasti Rapidi
1. Clicca su **"Tasto: -"** sulla clip
2. Premi il tasto che vuoi (es: F1, F2, numpad 1, etc.)
3. Il tasto è assegnato!

### Usa in Gioco
- **Premi il tasto** → La clip parte
- **Ripremi il tasto** → La clip si ferma
- Gli altri sentono **clip + la tua voce** contemporaneamente!

## 🎵 Creare/Tagliare Clip Audio

### Audacity (Gratis)
1. Scarica: https://www.audacityteam.org/
2. Apri file → Seleziona parte → Esporta

### Online
- Usa: https://mp3cut.net/it/

### Suggerimenti
- **Durata**: 1-5 secondi
- **Formato**: WAV (veloce) o MP3 (leggero)
- **Nome**: Breve e chiaro

## ⚙️ SCHEMA SETUP

```
Microfono Reale
     ↓
 Soundboard (mixa voce + clip)
     ↓
 VB-Cable (cavo virtuale)
     ↓
 Discord/TeamSpeak
     ↓
 I tuoi amici sentono TUTTO!
```

## 🛠️ Tecnologie

- **CustomTkinter** - Interfaccia moderna
- **SoundDevice** - Audio I/O bassa latenza
- **Keyboard** - Hotkeys globali
- **NumPy + SciPy** - Processamento audio
- **SoundFile** - Gestione file audio

## 🐛 Risoluzione Problemi

### ❌ Gli altri non mi sentono
- Verifica Discord input → CABLE Output
- Verifica Windows output → CABLE Input
- Riavvia Discord

### ❌ Non sento niente io
- Impostazioni Audio → Registrazione
- CABLE Output → Proprietà → Ascolta
- Spunta "Ascolta il dispositivo"

### ❌ Si sente solo la clip, non la mia voce
- Controlla che il microfono sia selezionato in Windows Input
- Aumenta il volume microfono nella Soundboard

### ❌ I tasti non funzionano
- **Esegui come Amministratore**
- Riassegna i tasti
- Evita tasti già usati dal gioco

## 💡 Consigli

### Tasti Consigliati
- **F1-F12**: Non interferiscono con i giochi
- **Numpad**: Perfetti se hai tastierino numerico
- **Evita**: WASD, Spazio, Ctrl, Shift

### Volumi Ottimali
- Clip: 60-80%
- Microfono: 70-80%
- Master: 100%

### Organizzazione
1. Crea cartella con clip favorite
2. "Carica Progetto" per importarle
3. Assegna F1, F2, F3... in ordine

## 🎮 Esempi d'Uso

- **Risate** quando vinci
- **Airhorn** per momenti epici
- **Frasi celebri** da film
- **Effetti sonori** divertenti
- **Musica intro** quando entri in party

## 📝 TODO Future

- [ ] Salvataggio configurazioni hotkeys
- [ ] Fade in/out automatici
- [ ] Visualizzazione waveform
- [ ] Più effetti (Delay, Compressor)
- [ ] Modalità compatta per gaming

## 📄 File del Progetto

- `main.py` - Applicazione principale
- `audio_engine.py` - Engine audio
- `advanced_editor.py` - 🎬 Editor avanzato & YouTube downloader
- `clip_cutter.py` - Tool per tagliare clip semplice
- `SETUP_GAMING.md` - **Guida completa setup**
- `GUIDA_EDITOR.md` - 🎬 **Guida YouTube & Editor**
- `CONSIGLI.md` - Personalizzazione avanzata

## 🆘 Serve Aiuto?

Leggi **`SETUP_GAMING.md`** per la guida dettagliata passo-passo!

---

**Buon gaming! 🎮🎵**

## 🎯 Casi d'Uso

### 🎤 Podcaster
Mixa musica di sottofondo, jingle ed effetti sonori mentre registri il tuo podcast

### 🎮 Streamer
Crea una soundboard professionale per il tuo stream con effetti e musica

### 🎵 Musicisti
Usa come backing track player con loop e controlli live

### 🎙️ Radio/DJ
Prepara mix con transizioni e effetti in tempo reale

## ⚙️ Configurazione Audio

### Latenza
Il buffer è impostato a 512 samples per bilanciare qualità e latenza. Modifica in `main.py`:

```python
self.mixer = AudioMixer(sample_rate=44100, buffer_size=512)
```

- **Buffer più piccolo** (256) = latenza minore, ma richiede più CPU
- **Buffer più grande** (1024) = più stabile, ma latenza maggiore

### Sample Rate
Di default 44100 Hz (CD quality). Per audio professionale usa 48000 Hz.

## 🛠️ Tecnologie Utilizzate

- **CustomTkinter** - Interfaccia grafica moderna
- **SoundDevice** - Audio I/O a bassa latenza
- **NumPy** - Processamento audio efficiente
- **Pydub** - Gestione file audio
- **SciPy** - Filtri ed effetti DSP

## 💡 Consigli e Trucchi

### Performance Ottimali
1. **Chiudi applicazioni audio inutilizzate** per evitare conflitti
2. **Usa file WAV** invece di MP3 per latenza minore
3. **Normalizza l'audio** delle clip prima dell'import
4. **Testa il setup audio** prima di performance live

### Workflow Efficiente
1. **Prepara le clip** in anticipo e salvale in una cartella
2. **Usa "Carica Progetto"** per importarle tutte insieme
3. **Testa i volumi** prima di registrare
4. **Salva regolarmente** le registrazioni

### Hotkeys (Futura Implementazione)
Nella prossima versione sarà possibile assegnare tasti della tastiera a ogni clip!

## 🐛 Risoluzione Problemi

### L'audio va a scatti
- Aumenta il buffer size in `main.py`
- Chiudi altre applicazioni audio
- Verifica driver audio aggiornati

### Non sento il microfono
- Controlla che il microfono sia selezionato come input di default
- Verifica le impostazioni privacy del sistema
- Aumenta il volume microfono nell'app

### Errore nel caricare file
- Verifica che il formato sia supportato (MP3, WAV, OGG, FLAC)
- Controlla che il file non sia corrotto
- Prova a convertire il file in WAV

## 📝 Prossimi Sviluppi

- [ ] Hotkeys configurabili per ogni clip
- [ ] Visualizzazione waveform in tempo reale
- [ ] Crossfade tra clip
- [ ] Più effetti audio (Delay, Chorus, Compressor)
- [ ] Supporto MIDI controller
- [ ] Salvataggio/caricamento configurazioni
- [ ] Skin personalizzabili
- [ ] VST plugin support

## 📄 Licenza

Progetto open source per uso personale e educativo.

## 🤝 Contributi

Suggerimenti e miglioramenti sono benvenuti!

---

**Buon mixing! 🎶**
