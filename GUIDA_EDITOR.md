# 🎬 Guida - Editor Avanzato & YouTube Downloader

## 🌟 Nuove Funzionalità!

L'**Editor Avanzato** aggiunge potenti strumenti per creare e gestire le tue clip audio:

### 📥 **Tab 1: YouTube Downloader**
Scarica audio direttamente da YouTube con un click!

### ✂️ **Tab 2: Editor Clip Avanzato**
Taglia e modifica clip con effetti professionali

### 📦 **Tab 3: Batch Processing**
Converti e normalizza più file contemporaneamente

---

## 🚀 COME USARE

### 🎬 Scaricare da YouTube

1. **Apri Editor Avanzato**
   - Dalla Soundboard: Click su "🎬 YouTube & Editor"
   - Oppure: Doppio click su `Editor_Avanzato.bat`

2. **Tab "📥 YouTube"**
   - Incolla URL YouTube
   - (Opzionale) Imposta timestamp inizio/fine
   - Scegli formato (WAV, MP3, OGG)
   - Click "📥 Scarica e Converti"

3. **Salva la Clip**
   - Il file viene scaricato e convertito
   - Scegli dove salvarlo
   - Pronto per la soundboard!

### ✂️ Modificare Clip Audio

1. **Tab "✂️ Editor Clip"**
   - Click "📂 Carica File Audio"
   - Seleziona il file da modificare

2. **Imposta Tempi**
   - Inizio e Fine in secondi
   - Oppure usa Quick Select (3s, 5s, 10s, 30s)

3. **Aggiungi Effetti** (opzionali):
   - ✅ **Normalizza Volume** - Porta al volume ottimale
   - ✅ **Fade In/Out** - Transizione morbida
   - ✅ **Rimuovi Silenzi** - Taglia parti vuote
   - ✅ **Converti in Mono** - Per risparmiare spazio

4. **Salva**
   - Click "✂️ Taglia e Salva"
   - Scegli nome e formato
   - Fatto!

### 📦 Batch Processing

1. **Tab "📦 Batch"**
   - Click "📁 Aggiungi File"
   - Seleziona tutti i file da convertire

2. **Opzioni**
   - Normalizza tutti
   - Scegli formato output

3. **Processa**
   - Click "⚙️ Processa Tutti i File"
   - Scegli cartella output
   - Attendi completamento

---

## ⚙️ SETUP FFmpeg (IMPORTANTE!)

### Cos'è FFmpeg?
È il tool che converte i formati audio. **Necessario per YouTube download e conversioni MP3/OGG**.

### 📥 Installazione Windows

#### Metodo 1: Scoop (FACILE)
```powershell
# Se non hai Scoop, installalo prima:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Poi installa FFmpeg:
scoop install ffmpeg
```

#### Metodo 2: Chocolatey
```powershell
choco install ffmpeg
```

#### Metodo 3: Manuale
1. Scarica da: https://www.gyan.dev/ffmpeg/builds/
2. Scarica "ffmpeg-release-essentials.zip"
3. Estrai in `C:\ffmpeg`
4. Aggiungi `C:\ffmpeg\bin` al PATH:
   - Cerca "Variabili d'ambiente" in Windows
   - Modifica PATH
   - Aggiungi `C:\ffmpeg\bin`
   - Riavvia il terminale

### ✅ Verifica Installazione
```powershell
ffmpeg -version
```

Se vedi la versione, è installato correttamente!

---

## 💡 CASI D'USO

### 🎮 Clip da Video di Gioco

**Esempio: Vuoi un suono epico da un video YouTube**

1. Trova il video su YouTube
2. Copia URL
3. Editor Avanzato → Tab YouTube
4. Incolla URL
5. Se sai i timestamp:
   - Inizio: 45 (parte da 45 secondi)
   - Fine: 50 (finisce a 50 secondi)
6. Scarica
7. Salva
8. Aggiungi alla soundboard!

### 🎵 Clip Musicale

**Esempio: Vuoi l'intro di una canzone (primi 10 secondi)**

1. YouTube URL della canzone
2. Inizio: 0
3. Fine: 10
4. Formato: WAV (migliore qualità)
5. Scarica
6. Nella soundboard: Assegna a F1!

### 🎤 Clip da Podcast

**Esempio: Momento divertente da un podcast**

1. Scarica episodio completo (senza timestamp)
2. Apri in Editor Avanzato
3. Tab Editor Clip
4. Carica file
5. Trova il momento (es: da 15:30 a 15:37)
   - Inizio: 930 (15 min × 60 + 30 sec)
   - Fine: 937
6. Effetti:
   - ✅ Normalizza
   - ✅ Rimuovi Silenzi
7. Salva!

### 📹 Frase Celebre da Film

**Esempio: "I'll be back" da Terminator**

1. Trova scena su YouTube
2. Usa timestamp precisi
3. Formato: WAV per qualità
4. Aggiungi Fade In/Out per effetto professionale
5. Normalizza per volume ottimale

---

## 🎯 EFFETTI SPIEGATI

### Normalizza Volume
**Cosa fa**: Porta l'audio al volume massimo senza distorsione (95%)

**Quando usare**:
- ✅ Sempre! (consigliato per tutte le clip)
- ✅ Clip troppo basse
- ✅ Per uniformare volume tra clip diverse

**Quando NON usare**:
- ❌ Se l'audio è già perfetto
- ❌ Se vuoi mantenere dinamiche originali

### Fade In/Out
**Cosa fa**: Aumenta gradualmente all'inizio, diminuisce alla fine (0.1 secondi)

**Quando usare**:
- ✅ Clip musicali
- ✅ Per evitare "click" o "pop" all'inizio/fine
- ✅ Transizioni smooth

**Quando NON usare**:
- ❌ Effetti sonori improvvisi (airhorn, etc.)
- ❌ Se vuoi impatto immediato

### Rimuovi Silenzi
**Cosa fa**: Taglia spazi vuoti all'inizio e alla fine

**Quando usare**:
- ✅ Clip vocali
- ✅ Per ridurre dimensione file
- ✅ Clip da video con pause

**Quando NON usare**:
- ❌ Se il silenzio è intenzionale
- ❌ Musica con intro/outro silenziose

### Converti in Mono
**Cosa fa**: Da stereo (2 canali) a mono (1 canale)

**Quando usare**:
- ✅ Per risparmiare spazio (file 50% più piccolo)
- ✅ Clip vocali (non serve stereo)
- ✅ Effetti sonori semplici

**Quando NON usare**:
- ❌ Musica (perde qualità)
- ❌ Effetti stereo spaziali

---

## 📊 FORMATI AUDIO

### WAV
- **Pro**: Qualità massima, nessuna compressione
- **Contro**: File grandi
- **Usa per**: Clip importanti, effetti sonori, qualità massima

### MP3
- **Pro**: File piccoli (10x più piccolo di WAV)
- **Contro**: Compressione con perdita
- **Usa per**: Libreria grande, musica, spazio limitato

### OGG
- **Pro**: Buona qualità, file medio-piccoli
- **Contro**: Meno compatibile
- **Usa per**: Alternativa a MP3

### 💡 Consiglio
- **Gaming/Soundboard**: WAV o MP3 a 192kbps
- **Streaming**: MP3 o OGG
- **Archivio**: WAV

---

## 🔥 WORKFLOW CONSIGLIATI

### Workflow 1: Da YouTube a Soundboard
```
1. YouTube URL → Editor Avanzato
2. Imposta timestamp
3. Scarica in WAV
4. (Se serve) Apri in Editor Clip
5. Normalizza + Fade
6. Salva
7. Aggiungi a Soundboard
8. Assegna hotkey!
```

### Workflow 2: Taglia File Lungo
```
1. File lungo → Editor Clip
2. Trova momento interessante
3. Imposta inizio/fine
4. Normalizza + Rimuovi silenzi
5. Salva clip corta
6. Aggiungi a Soundboard
```

### Workflow 3: Batch Conversion
```
1. Tanti file da convertire → Tab Batch
2. Aggiungi tutti
3. Normalizza: ON
4. Formato: MP3 (per risparmiare spazio)
5. Processa
6. Carica tutte nella soundboard!
```

---

## 🛠️ TROUBLESHOOTING

### ❌ "yt-dlp non installato"
→ Esegui: `pip install yt-dlp`

### ❌ "Errore durante il download"
→ Verifica FFmpeg installato: `ffmpeg -version`
→ URL YouTube valido?
→ Video disponibile nella tua regione?

### ❌ "Errore conversione formato"
→ FFmpeg non installato o non nel PATH
→ Segui sezione "Setup FFmpeg" sopra

### ❌ Download lento
→ Normale per video lunghi
→ Usa timestamp per scaricare solo la parte necessaria

### ❌ File troppo grande
→ Usa formato MP3 invece di WAV
→ O taglia solo la parte che serve

---

## 💡 TIPS & TRICKS

### Trovare Timestamp YouTube
1. Avvia il video
2. Metti in pausa al punto che ti interessa
3. Guarda il tempo (es: 2:45)
4. Converti in secondi: 2×60 + 45 = 165

### Organizzazione File
```
📁 Soundboard_Clips/
  ├── 📁 Originali/        ← File scaricati da YouTube
  ├── 📁 Pronti/           ← Clip tagliate e pronte
  └── 📁 Archivio/         ← Backup
```

### Qualità vs Dimensione
- **Clip importante**: WAV
- **Uso frequente**: MP3 192kbps
- **Libreria grande**: MP3 128kbps
- **Effetti veloci**: MP3 96kbps (OK per soundboard)

### Batch Processing Intelligente
1. Scarica tanti file da YouTube
2. Salvali in una cartella
3. Batch → Normalizza tutti
4. Converti in MP3
5. Libreria pronta!

---

## 🎓 ESEMPI PRATICI

### Esempio 1: Meme Sound
```
URL: https://youtube.com/watch?v=...
Inizio: 10
Fine: 13
Formato: WAV
Effetti: Normalizza
Risultato: Clip 3 secondi pronta per F1
```

### Esempio 2: Intro Musicale
```
URL: https://youtube.com/watch?v=...
Inizio: 0
Fine: 15
Formato: MP3
Effetti: Normalizza + Fade Out
Risultato: Intro 15 secondi per entrare in party
```

### Esempio 3: Victory Sound
```
File esistente: victory_long.wav
Editor Clip: 2.5 → 7.8 secondi
Effetti: Normalizza + Fade In/Out + Rimuovi Silenzi
Risultato: Clip perfetta 5.3 secondi
```

---

## 🎉 PRONTO!

Ora hai tutto per:
- ✅ Scaricare da YouTube
- ✅ Tagliare con precisione
- ✅ Applicare effetti professionali
- ✅ Batch processing
- ✅ Creare libreria perfetta!

**Divertiti a creare le tue clip! 🎬🎵**

---

## 📖 Vedi Anche

- `START_HERE.md` - Guida generale
- `SETUP_GAMING.md` - Setup soundboard
- `CONSIGLI.md` - Tips avanzati
