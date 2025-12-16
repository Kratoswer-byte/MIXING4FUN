# 🚀 START HERE - Guida Veloce

## 🎯 Cosa fa questo progetto?

Una **soundboard per gaming** che ti permette di:
- ✅ Far sentire **clip audio + la tua voce** contemporaneamente in Discord/TeamSpeak
- ✅ Lanciare le clip con **tasti rapidi** (F1, F2, numpad, etc.)
- ✅ **Zero interferenze** con il tuo microfono (rimane sempre attivo)
- ✅ **Facilissimo** da usare durante il gioco

## ⚡ SETUP RAPIDO (5 minuti)

### 1️⃣ Installa VB-Cable
📥 Scarica: https://vb-audio.com/Cable/
- Installa come amministratore
- Riavvia il PC

### 2️⃣ Configura Windows
🔊 **Impostazioni Audio Windows:**
- Output → **CABLE Input (VB-Audio Virtual Cable)**

### 3️⃣ Configura Discord
🎮 **Impostazioni Discord → Voce e Video:**
- Dispositivo Input → **CABLE Output (VB-Audio Virtual Cable)**
- Dispositivo Output → **Le tue cuffie normali**

### 4️⃣ Abilita "Ascolta"
👂 **Per sentire anche tu l'audio:**
- Impostazioni Windows → Audio → Registrazione
- Click destro su "CABLE Output" → Proprietà
- Tab "Ascolta" → Spunta "Ascolta il dispositivo"
- Seleziona le tue cuffie

### 5️⃣ Installa Dipendenze Python
```bash
pip install -r requirements.txt
```

### 6️⃣ AVVIA!
Doppio click su: **`Avvia_Soundboard.bat`** (come amministratore per i tasti)

## 🎮 COME USARE

### Aggiungi Clip
1. Click su "➕ Aggiungi Clip Audio"
2. Scegli il tuo file MP3/WAV
3. FATTO!

### Assegna Tasto
1. Click su "Tasto: -" nella clip
2. Premi il tasto che vuoi (es: F1)
3. FATTO!

### In Gioco
- Premi F1 → Clip parte
- Ripremi F1 → Clip si ferma
- I tuoi amici sentono clip + voce!

## ✂️ TAGLIARE CLIP

Hai bisogno di tagliare una clip?

### Metodo 1: Editor Avanzato (🎬 NUOVO!)
**Doppio click su:** `Editor_Avanzato.bat`

**Funzionalità:**
- 📥 Scarica da YouTube con timestamp
- ✂️ Taglia con precisione
- 🎵 Effetti: Normalizza, Fade, Rimuovi silenzi
- 📦 Batch processing multiplo

### Metodo 2: Clip Cutter Semplice
**Doppio click su:** `Taglia_Clip.bat`

1. Carica file audio
2. Imposta inizio e fine (in secondi)
3. Salva!

📖 **Guida completa editor**: `GUIDA_EDITOR.md`

## 📁 FILE PRINCIPALI

- **`Avvia_Soundboard.bat`** ← CLICCA QUI per avviare
- **`Editor_Avanzato.bat`** ← 🎬 NUOVO! YouTube & Editor
- **`Taglia_Clip.bat`** ← Per tagliare clip (versione semplice)
- **`START_HERE.md`** ← Questa guida veloce
- **`SETUP_GAMING.md`** ← Setup completo passo-passo
- **`GUIDA_EDITOR.md`** ← 🎬 Guida YouTube Downloader & Editor
- **`SETUP_MICROFONO.md`** ← ⚠️ IMPORTANTE: Come far funzionare il microfono
- **`Readme.md`** ← Documentazione completa

## 🆘 PROBLEMI?

### Non funzionano i tasti
→ Esegui `Avvia_Soundboard.bat` come **Amministratore**
  (click destro → "Esegui come amministratore")

### Gli altri non mi sentono
→ Controlla Discord: Input deve essere **CABLE Output**

### Non sento niente io
→ Impostazioni Audio → Registrazione → CABLE Output → Proprietà → Ascolta → Spunta "Ascolta il dispositivo"

### Si sente solo la clip, non la mia voce
→ Volume Microfono nella soundboard al 70-80%

## 💡 CONSIGLI RAPIDI

### Tasti Consigliati
✅ F1-F12 (non interferiscono con i giochi)
✅ Numpad (se hai tastierino numerico)
❌ NON usare: WASD, Spazio, Ctrl, Shift

### Clip Perfette
- **Durata**: 2-5 secondi
- **Volume**: Normalizzato
- **Formato**: WAV (veloce) o MP3 (leggero)

### Dove Trovare Clip
- Taglia da video YouTube
- Registra frasi tue
- Scarica effetti sonori
- Usa `Taglia_Clip.bat` per tagliare

## 🎯 ESEMPI D'USO

### Gaming
- Risate quando vinci
- Airhorn per momenti epici
- "GG EZ" automatizzato
- Musica intro quando entri in party

### Trolling Amici
- Suoni imbarazzanti
- Frasi random
- Effetti comici

### Streaming
- Intro musicale
- Alert per donazioni
- Transizioni

## 📊 CHECKLIST PRE-GAME

Prima di giocare, verifica:
- [ ] VB-Cable installato
- [ ] Windows Output → CABLE Input
- [ ] Discord Input → CABLE Output
- [ ] Ascolta dispositivo attivo
- [ ] Soundboard avviata come admin
- [ ] Clip caricate
- [ ] Tasti assegnati
- [ ] Volume testato

## 🔗 LINK UTILI

**VB-Cable (GRATIS):**
https://vb-audio.com/Cable/

**Tagliare Audio Online:**
https://mp3cut.net/it/

**Audacity (Editor Audio):**
https://www.audacityteam.org/

**Effetti Sonori Gratis:**
- https://freesound.org/
- https://www.zapsplat.com/

## 📚 DOCUMENTAZIONE COMPLETA

Vuoi saperne di più? Leggi:
- **`SETUP_GAMING.md`** - Setup dettagliato passo-passo
- **`Readme.md`** - Documentazione tecnica completa
- **`CONSIGLI.md`** - Personalizzazione avanzata

## 🎉 PRONTO!

Ora sei pronto per diventare la star della chat vocale!

**Ricorda**: Usa con moderazione, i tuoi amici ti ringrazieranno! 😄

---

**Hai problemi?** Leggi `SETUP_GAMING.md` per troubleshooting dettagliato!
