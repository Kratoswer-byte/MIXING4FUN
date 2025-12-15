# 🎮 GUIDA SETUP - Soundboard per Gaming con Discord/TeamSpeak

## 🎯 Obiettivo
Far sentire le **clip audio + la tua voce** contemporaneamente ai tuoi amici in chat vocale (Discord, TeamSpeak, etc.)

## ⚙️ SETUP NECESSARIO

### 📥 Passo 1: Installa VB-Audio Virtual Cable

1. **Scarica VB-Cable** (GRATUITO):
   - Vai su: https://vb-audio.com/Cable/
   - Scarica "VB-CABLE Virtual Audio Device"
   - Estrai il file ZIP

2. **Installa come Amministratore**:
   - Click destro su `VBCABLE_Setup_x64.exe` (o x86 se hai Windows 32-bit)
   - "Esegui come amministratore"
   - Clicca "Install Driver"
   - Riavvia il PC se richiesto

### 🔊 Passo 2: Configura l'Audio di Windows

1. **Imposta VB-Cable come Output Predefinito**:
   - Click destro sull'icona audio nella taskbar
   - "Impostazioni audio"
   - In "Output", seleziona **"CABLE Input (VB-Audio Virtual Cable)"**
   - ⚠️ Nota: Non sentirai più l'audio dalle casse! È normale!

2. **Crea un Mix per Sentire Anche Tu**:
   - Cerca "Opzioni audio" nel menu Start
   - Vai su "Impostazioni audio avanzate"
   - Nella scheda "Registrazione":
     - Click destro su "CABLE Output" → "Proprietà"
     - Scheda "Ascolta"
     - Spunta "Ascolta il dispositivo"
     - Seleziona le tue cuffie/casse in "Riproduci tramite questo dispositivo"
     - OK

### 🎤 Passo 3: Configura Discord/TeamSpeak

**Per Discord:**
1. Impostazioni Discord → "Voce e Video"
2. **Dispositivo di input**: Seleziona **"CABLE Output (VB-Audio Virtual Cable)"**
3. **Dispositivo di output**: Seleziona le tue **cuffie normali**
4. Disattiva "Elaborazione avanzata voce" (opzionale, per audio più chiaro)

**Per TeamSpeak:**
1. Impostazioni → Opzioni → Cattura
2. **Dispositivo di cattura**: **"CABLE Output (VB-Audio Virtual Cable)"**
3. **Dispositivo di riproduzione**: Le tue **cuffie normali**

### 🎙️ Passo 4: Configura il Microfono in Windows

1. Impostazioni Windows → Audio
2. **Dispositivo di input**: Seleziona il tuo **microfono vero**
3. Regola il volume del microfono al 70-80%

### 🎮 COME FUNZIONA

```
Il Tuo Microfono → Soundboard
        ↓
Le Tue Clip Audio → Soundboard
        ↓
    MIXER (mescolati insieme)
        ↓
VB-Cable (cavo virtuale)
        ↓
Discord/TeamSpeak → Gli Altri Ti Sentono!
```

## 🚀 USO DELLA SOUNDBOARD

### 1️⃣ Aggiungi Clip Audio
- Clicca "➕ Aggiungi Clip Audio"
- Scegli il tuo file MP3/WAV
- La clip appare nella griglia

### 2️⃣ Assegna Tasti Rapidi
- Clicca sul pulsante **"Tasto: -"** sulla clip
- Premi il tasto che vuoi usare (es: F1, F2, 1, 2, Q, E, etc.)
- Il tasto viene assegnato!

### 3️⃣ Gioca e Divertiti!
- Premi il tasto assegnato per lanciare la clip
- Gli altri sentono la clip + la tua voce contemporaneamente!
- Ripremi il tasto per fermare la clip

### 💡 SUGGERIMENTI

#### Tasti Consigliati
- **F1-F12**: Ideali, non interferiscono con i giochi
- **Numpad (0-9)**: Perfetti se hai una tastiera con numpad
- **Ctrl+Tasto**: Per combinazioni (es: Ctrl+1, Ctrl+2)

#### Volumi Ottimali
- **Volume Clip**: 60-80% (regola per clip)
- **Volume Microfono**: 70-80%
- **Master Volume**: 100%

#### Organizzazione Clip
1. Crea una cartella con le tue clip favorite
2. Usa "📁 Carica Progetto" per caricarle tutte
3. Assegna i tasti in ordine (F1, F2, F3...)

## 🎵 COME CREARE/TAGLIARE CLIP AUDIO

### Metodo 1: Audacity (GRATIS)
1. Scarica Audacity: https://www.audacityteam.org/
2. Apri il file audio
3. Seleziona la parte che vuoi
4. File → Esporta → Esporta Audio Selezionato
5. Salva come WAV o MP3

### Metodo 2: Online (Veloce)
- Usa: https://mp3cut.net/it/
- Carica file, taglia, scarica

### Suggerimenti per Clip
- **Durata**: 1-5 secondi (massimo impatto)
- **Volume**: Normalizza a -3dB
- **Formato**: WAV per velocità, MP3 per spazio
- **Nome**: Nomi brevi e chiari

## 🛠️ RISOLUZIONE PROBLEMI

### ❌ "Gli altri non mi sentono"
**Soluzione:**
- Verifica che Discord usi "CABLE Output" come input
- Controlla che Windows output sia "CABLE Input"
- Riavvia Discord

### ❌ "Non sento niente io"
**Soluzione:**
- Vai in Impostazioni Audio Windows
- Registrazione → CABLE Output → Proprietà
- Ascolta → Spunta "Ascolta il dispositivo"
- Seleziona le tue cuffie

### ❌ "Si sente solo la clip, non la mia voce"
**Soluzione:**
- Verifica che il microfono sia selezionato in Windows
- Aumenta il volume microfono nello Soundboard
- Controlla che il mixer abbia avviato lo stream audio

### ❌ "I tasti non funzionano"
**Soluzione:**
- Esegui la Soundboard **come Amministratore**
- Riassegna i tasti
- Evita tasti già usati dal gioco

### ❌ "Audio distorto/robotico"
**Soluzione:**
- Aumenta il buffer size (in `main.py` cambia da 512 a 1024)
- Abbassa il volume delle clip
- Chiudi altre app audio

## 🎮 ESEMPI DI USO

### Per Gaming
- **Risate registrate** quando vinci
- **Effetti sonori** (airhorn, applause)
- **Frasi celebri** da film/giochi
- **Musica intro** quando entri in party

### Per Streaming
- **Intro musicale**
- **Transizioni tra sezioni**
- **Effetti comici**
- **Alert per donazioni**

### Per Podcast/Radio
- **Jingle introduttivi**
- **Effetti di transizione**
- **Sottofondo musicale**
- **Campane/sirene**

## 📋 CHECKLIST RAPIDA

Prima di iniziare a giocare, verifica:
- [ ] VB-Cable installato
- [ ] Windows output → CABLE Input
- [ ] Discord input → CABLE Output
- [ ] Microfono selezionato in Windows
- [ ] Ascolta dispositivo attivo per sentire anche tu
- [ ] Clip caricate nella Soundboard
- [ ] Tasti assegnati
- [ ] Volume testato e regolato

## 🆘 SUPPORTO

Se hai ancora problemi:
1. Riavvia il PC dopo aver installato VB-Cable
2. Testa con un amico prima di usarlo in gioco
3. Registra un messaggio vocale per testare l'audio
4. Controlla i driver audio aggiornati

## 💾 BACKUP E CONDIVISIONE

### Salva le tue Clip Preferite
Crea una cartella come:
```
C:\Users\TuoNome\Soundboard\
  ├── Meme\
  ├── Musica\
  ├── Effetti\
  └── Frasi\
```

### Condividi con Amici
- Condividi la cartella delle clip
- Tutti possono usare le stesse clip!

---

## 🎉 PRONTO!

Ora sei pronto per diventare la star della chat vocale! 🎮🎵

**Ricorda**: Usa con moderazione, i tuoi amici ti ringrazieranno! 😄
