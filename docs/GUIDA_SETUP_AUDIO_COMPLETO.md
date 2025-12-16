# 🎮 GUIDA SETUP AUDIO COMPLETO
## Soundboard + Voicemeeter + Discord/TeamSpeak

---

## 📋 PREREQUISITI

### Software Necessario:
1. **VB-Audio Virtual Cable** - [Download](https://vb-audio.com/Cable/)
2. **Voicemeeter Banana** (o Potato) - [Download](https://vb-audio.com/Voicemeeter/banana.htm)
3. **Gaming Soundboard** - Il programma (main.py)

---

## ⚙️ SETUP PASSO-PASSO

### **PARTE 1: CONFIGURAZIONE VOICEMEETER**

#### 1.1 Hardware Input (Microfono)
```
Hardware Input 1:
├─ Seleziona: Il tuo microfono fisico
├─ Esempio: "Microfono (Realtek Audio)"
└─ Attiva: A1 (per sentire in cuffia)
```

#### 1.2 Hardware Input (Soundboard)
```
Hardware Input 2:
├─ Seleziona: "CABLE Output (VB-Audio Virtual Cable)"
├─ Questo riceve l'audio dal Soundboard
└─ Attiva: A1 (per sentire in cuffia)
```

#### 1.3 Hardware Output
```
A1 (Hardware Out):
├─ Seleziona: Le tue cuffie/speaker
└─ Esempio: "Cuffie (Realtek Audio)"
```

#### 1.4 Virtual Output (per Discord)
```
Voicemeeter ha un'uscita virtuale chiamata:
"VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)"
└─ Questo verrà usato da Discord come microfono virtuale
```

---

### **PARTE 2: CONFIGURAZIONE SOUNDBOARD**

#### 2.1 Apri il Soundboard
```powershell
# In una PowerShell nella cartella del progetto:
$env:PATH += ";$PWD\ffmpeg-8.0.1-essentials_build\bin"; python main.py
```

#### 2.2 Vai nel Tab 🔊 Audio
1. Apri il tab "🔊 Audio" nel programma
2. Cerca nella lista: **"CABLE Input (VB-Audio Virtual Cable)"**
   - Sarà evidenziato in ROSSO/ARANCIONE
3. Seleziona il **radio button** a destra
4. Clicca **"✓ Applica Configurazione"**

✅ **RISULTATO:** Le clip del soundboard verranno inviate a Voicemeeter (Input 2)

---

### **PARTE 3: CONFIGURAZIONE WINDOWS**

#### 3.1 Dispositivi di Riproduzione
```
Windows Audio Output (Cuffie/Speaker):
├─ Click destro sull'icona volume (barra delle applicazioni)
├─ "Impostazioni audio"
├─ Dispositivo di output: "Le tue cuffie/speaker"
└─ NON usare VoiceMeeter come output di Windows
```

#### 3.2 Dispositivi di Registrazione
```
Windows Microphone:
├─ Mantieni il microfono fisico come predefinito
└─ Voicemeeter gestirà il routing
```

---

### **PARTE 4: CONFIGURAZIONE DISCORD**

#### 4.1 Impostazioni Voce & Video
```
Discord → Impostazioni Utente → Voce e Video

Dispositivo di Input:
├─ Seleziona: "VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)"
└─ Questo riceve MIC + SOUNDBOARD mixati insieme

Dispositivo di Output:
├─ Seleziona: "Le tue cuffie/speaker"
└─ Per sentire gli altri su Discord
```

#### 4.2 Test
1. Attiva "Test Microfono" in Discord
2. Parla nel microfono → dovresti vedere il livello muoversi
3. Premi F1 (o altro hotkey) nel Soundboard → dovresti sentire la clip
4. Su Discord vedrai il livello muoversi anche quando riproduci clip

---

## 🔧 SCHEMA COMPLETO DEL FLUSSO AUDIO

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIGURAZIONE AUDIO                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  MICROFONO       │ ──────┐
│  (Fisico)        │       │
└──────────────────┘       │
                           ▼
                    ┌──────────────────┐
                    │  VOICEMEETER     │
                    │                  │
                    │  Input 1: MIC    │◄────── Microfono fisico
                    │  Input 2: CABLE  │◄────── Soundboard
                    │                  │
                    │  Output: VAIO    │────┐
                    │  A1: Cuffie      │    │
                    └──────────────────┘    │
                           │                │
                           │                │
          ┌────────────────┴───────┐        │
          │                        │        │
          ▼                        ▼        ▼
    ┌──────────┐          ┌──────────────────────┐
    │  CUFFIE  │          │     DISCORD          │
    │          │          │                      │
    │ (ascolti)│          │ Input: VoiceMeeter   │
    └──────────┘          │ Output: Cuffie       │
                          │                      │
                          │ Gli altri ti sentono:│
                          │ MIC + CLIP mixati    │
                          └──────────────────────┘

┌──────────────────┐
│  SOUNDBOARD      │
│                  │
│ Output Device:   │
│ "CABLE Input"    │──────► CABLE ──► Voicemeeter Input 2
└──────────────────┘
```

---

## ✅ VERIFICA FUNZIONAMENTO

### Test 1: Controllo Voicemeeter
1. Apri Voicemeeter
2. Parla nel microfono → vedi il fader di **Input 1** muoversi
3. Premi un hotkey (es: F1) nel Soundboard → vedi il fader di **Input 2** muoversi
4. Entrambi i fader dovrebbero essere attivi contemporaneamente se parli e riproduci

### Test 2: Controllo Discord
1. Apri Discord
2. Vai in Impostazioni → Voce → "Test Microfono"
3. Parla → vedi il livello muoversi
4. Premi F1 nel Soundboard → vedi il livello muoversi
5. ✅ **Funziona!** Gli altri ti sentiranno con entrambi i segnali mixati

### Test 3: Controllo Cuffie
1. Parla nel microfono → ti senti nelle cuffie (sidetone)
2. Premi F1 → senti la clip nelle cuffie
3. Qualcuno parla su Discord → lo senti nelle cuffie
4. ✅ **Perfetto!** Tutto funziona insieme

---

## 🎯 HOTKEYS SOUNDBOARD

| Tasto | Funzione |
|-------|----------|
| **F1-F12** | Hotkey disponibili per clip |
| **Numpad 0-9** | Hotkey numerici |
| **A-Z** | Hotkey lettere |
| **Ctrl+H** | Assegna nuovo hotkey alla clip |

### Come assegnare un Hotkey:
1. Nel tab **🎮 Soundboard**
2. Clicca sul pulsante **"⌨ Imposta Hotkey"** della clip
3. Premi il tasto che vuoi usare (es: F1, J, Numpad 5)
4. ✅ Salvato automaticamente

---

## 🛠️ TROUBLESHOOTING

### ❌ "Non sento le clip nelle cuffie"
**Soluzione:**
- In Voicemeeter, verifica che **Input 2** abbia **A1** attivo (verde)
- Verifica che **A1** sia impostato sulle tue cuffie

### ❌ "Discord non riceve l'audio delle clip"
**Soluzione:**
- Discord Input deve essere: **"VoiceMeeter Output (VAIO)"**
- In Voicemeeter, **Input 2** deve avere **B1** attivo (arancione)

### ❌ "Il fader di Input 2 in Voicemeeter non si muove"
**Soluzione:**
1. Apri il Soundboard → Tab **🔊 Audio**
2. Verifica che sia selezionato **"CABLE Input"**
3. Clicca **"✓ Applica Configurazione"**
4. Riprova a premere un hotkey

### ❌ "Voicemeeter dice 'Hardware Input 2 not connected'"
**Soluzione:**
- Installa **VB-Audio Virtual Cable**
- Riavvia Voicemeeter
- Seleziona "CABLE Output" in Hardware Input 2

### ❌ "Gli altri su Discord mi sentono in eco"
**Soluzione:**
- Discord Output NON deve essere Voicemeeter
- Discord Output → usa le tue cuffie normali
- Solo l'Input di Discord usa Voicemeeter

---

## 💡 TIPS & TRICKS

### Regolare il Volume delle Clip
```
Nel Soundboard:
├─ Ogni clip ha uno slider volume individuale
├─ C'è uno slider "Master Volume" per tutte le clip
└─ In Voicemeeter puoi regolare il fader di Input 2
```

### Usare Effetti Audio
```
Nel Soundboard (Tab Soundboard):
├─ Reverb: Aggiunge riverbero alle clip
├─ Bass Boost: Aumenta i bassi (0-200%)
└─ Gli effetti si applicano a tutte le clip
```

### Salvare le Configurazioni
```
Il Soundboard salva automaticamente:
├─ Clip caricate
├─ Volume di ogni clip
├─ Hotkey assegnati
└─ Dispositivo audio selezionato

File: soundboard_config.json
```

### Download da YouTube
```
Tab 📥 YouTube:
├─ Incolla URL del video
├─ Scegli formato: MP3 o WAV
├─ Imposta Start/End per tagliare
├─ La clip viene scaricata in /clips e caricata automaticamente
```

---

## 📝 RIEPILOGO CONFIGURAZIONE

| Componente | Impostazione | Valore |
|------------|--------------|--------|
| **Soundboard Output** | Tab 🔊 Audio | CABLE Input |
| **Voicemeeter Input 1** | Hardware Input | Microfono fisico |
| **Voicemeeter Input 2** | Hardware Input | CABLE Output |
| **Voicemeeter A1** | Hardware Output | Cuffie/Speaker |
| **Discord Input** | Voce & Video | VoiceMeeter Output (VAIO) |
| **Discord Output** | Voce & Video | Cuffie/Speaker |
| **Windows Output** | Impostazioni | Cuffie/Speaker |

---

## 🎮 PRONTO PER GIOCARE!

Ora puoi:
- ✅ Parlare normalmente su Discord
- ✅ Premere hotkeys per riprodurre clip divertenti
- ✅ Gli altri ti sentono con MIC + CLIP mixati
- ✅ Tu senti tutto nelle cuffie
- ✅ Controllo totale sui volumi

**Buon divertimento! 🎉**

---

*Creato per Gaming Soundboard - MIXING4FUN*
*Ultima revisione: 29/11/2025*
