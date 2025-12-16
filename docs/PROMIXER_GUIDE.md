# 🎛️ ProMixer - Mixer Audio Professionale

**Sostituto completo di Voicemeeter** - Mixer multi-canale standalone con routing avanzato

---

## ✨ Caratteristiche Principali

### 🎚️ **Multi-Channel Mixer**
- **3 Hardware Inputs** - Per microfoni e line-in
- **2 Virtual Inputs** - Per desktop audio e applicazioni
- **5 Output Buses** (A1, A2, A3, B1, B2) - Output simultanei multipli

### 🔀 **Routing Matrix Flessibile**
- Routing libero: ogni canale può andare a qualsiasi bus
- Click sui bottoni A1/A2/A3/B1/B2 per attivare/disattivare routing
- Gestione indipendente per ogni canale

### 🎛️ **Controlli per Canale**
- **Fader** da -60dB a +12dB
- **Mute/Solo** per ogni canale
- **VU Meter** in tempo reale con peak hold
- **Pan** stereo (L-R)

### 🎨 **Processing Audio**
- **EQ 3 bande** (Low/Mid/High) per canale
- **Compressore dinamico** configurabile
- **Noise Gate** con threshold regolabile
- **Limiter** automatico anti-clipping

### 📊 **Metering Professionale**
- VU meters con gradient (verde → giallo → rosso)
- Peak hold con decadimento graduale
- Indicatori separati per RMS e Peak

---

## 🚀 Installazione e Setup

### 1️⃣ **Requisiti Sistema**
```
- Windows 10/11
- Python 3.8 o superiore
- VB-Audio Virtual Cable (per virtual inputs)
```

### 2️⃣ **Installazione Rapida**
Già installato nella tua cartella! Esegui:
```
Avvia_ProMixer.bat
```

### 3️⃣ **Configurazione Dispositivi**
1. Clicca su **⚙️ CONFIG** nella barra superiore
2. Assegna dispositivi agli **Hardware Inputs** (es. microfono)
3. Assegna dispositivi ai **Bus Outputs** (es. cuffie, speakers)
4. Chiudi la finestra di configurazione
5. Clicca su **▶ START** per avviare il mixer

---

## 📋 Guida Rapida

### **Setup Base Gaming/Streaming**

#### Configurazione Consigliata:
```
INPUTS:
├─ HW1 → Microfono fisico
├─ HW2 → (non usato)
├─ HW3 → (non usato)
├─ VIRT1 → CABLE Output (desktop audio)
└─ VIRT2 → (non usato)

OUTPUT BUSES:
├─ Bus A1 → Cuffie (ascolti tutto)
├─ Bus A2 → CABLE Input (per Discord/OBS)
├─ Bus A3-B2 → (non usati)
```

#### Routing:
```
HW1 (Mic):    [A1] [A2] ← Attiva entrambi
VIRT1 (PC):   [A1] [ ] ← Solo A1 (ascolti tu, non va su Discord)
```

### **Uso dei Fader**
- **0 dB** = volume normale (unity gain)
- **-inf dB** = silenzio
- **+12 dB** = boost massimo

### **Mute vs Solo**
- **Mute (M)** = silenzia questo canale
- **Solo (S)** = silenzia tutti gli altri (non ancora implementato fully)

---

## 🎯 Scenari d'Uso

### **Scenario 1: Gaming + Discord**
1. **HW1** (Mic) → A1 (cuffie) + A2 (Discord)
2. **VIRT1** (Game audio) → A1 (solo cuffie)
3. Risultato: ascolti game + Discord, Discord sente solo te

### **Scenario 2: Streaming OBS**
1. **HW1** (Mic) → A1 + A2
2. **VIRT1** (Desktop) → A1 + A2
3. **Bus A2** → OBS come "Audio Input Capture"
4. Risultato: OBS registra voce + desktop audio mixati

### **Scenario 3: Multi-Output (PC + Casse + Registrazione)**
1. **Bus A1** → Cuffie (monitor personale)
2. **Bus A2** → Casse (live output)
3. **Bus B1** → Registratore/Interfaccia
4. Controllo volume indipendente per ogni output!

---

## ⚙️ Configurazione Avanzata

### **Sample Rate**
Di default: **44100 Hz**
Per cambiare, modifica in `mixer_engine.py`:
```python
mixer = ProMixer(sample_rate=48000, buffer_size=512)
```

### **Buffer Size (Latenza)**
- **256 samples** = latenza bassa (~6ms) ma più CPU
- **512 samples** = default, bilanciato
- **1024 samples** = latenza alta (~23ms) ma stabile

### **Processing Chain**
Per ogni canale:
```
Input → Gate → EQ → Compressor → Fader → Pan → Routing → Output
```

---

## 🔧 Risoluzione Problemi

### ❌ "Impossibile avviare mixer"
**Causa**: Dispositivi occupati da altre app
**Soluzione**: Chiudi Voicemeeter, Discord, OBS e riprova

### ❌ "No audio in uscita"
**Causa**: Routing non configurato
**Soluzione**: 
1. Verifica che i canali abbiano almeno un bus attivo (es. A1)
2. Controlla che il bus abbia un dispositivo assegnato
3. Verifica che il fader non sia a -inf

### ❌ "Audio distorto/clipping"
**Causa**: Volume troppo alto
**Soluzione**: Abbassa i fader dei canali o il master del bus

### ❌ "Latenza alta"
**Causa**: Buffer troppo grande
**Soluzione**: Riduci buffer_size a 256 o installa driver ASIO

---

## 🆚 ProMixer vs Voicemeeter

| Feature | ProMixer | Voicemeeter |
|---------|----------|-------------|
| Open Source | ✅ Sì | ❌ No |
| Multi-output | ✅ 5 bus | ✅ 5 bus |
| Processing | ✅ EQ+Comp+Gate | ✅ EQ+Comp+Gate |
| VU Meters | ✅ Real-time | ✅ Real-time |
| Routing Matrix | ✅ Grafico | ✅ Bottoni |
| ASIO Support | 🔜 In dev | ✅ Sì |
| Preset System | 🔜 In dev | ✅ Sì |
| Remote API | ❌ No | ✅ Sì |

---

## 🔜 Prossime Feature

- [ ] Supporto driver ASIO nativi
- [ ] Sistema preset salvabili/caricabili
- [ ] EQ grafico a 10 bande
- [ ] Effetti audio (Reverb, Delay, Chorus)
- [ ] Recording integrato
- [ ] Integrazione con soundboard esistente
- [ ] Hotkeys per mute/solo/fader
- [ ] API remote per controllo esterno

---

## 🐛 Bug Noti

1. **Solo button** non implementato completamente (mute altri canali)
2. **Pan** non visibile in UI (funziona ma senza controllo)
3. **Metering** può rallentare con molti canali attivi

---

## 📝 Changelog

### v0.1.0 (14 Dicembre 2025)
- ✅ Prima release funzionante
- ✅ 5 canali input (3 HW + 2 Virtual)
- ✅ 5 bus output (A1-A3, B1-B2)
- ✅ Routing matrix grafico
- ✅ VU meters real-time
- ✅ Fader con dB scale
- ✅ Processing chain (EQ, Comp, Gate)
- ✅ Multi-output simultaneo

---

## 💡 Tips & Tricks

1. **Routing veloce**: Clicca più volte sui bottoni bus per toggle rapido
2. **Monitor personale**: Usa sempre A1 per le tue cuffie
3. **Virtual cable**: VIRT1 cattura desktop audio via VB-Cable Output
4. **Gain staging**: Mantieni i fader tra -12dB e 0dB per qualità ottimale
5. **Peak watching**: Se i VU meters diventano rossi, abbassa i volumi

---

## 📧 Supporto

Problemi o domande? Verifica:
1. Il file `PROMIXER_GUIDE.md` (questo file)
2. La documentazione di VB-Audio Cable
3. I log in `soundboard.log`

---

## 🎉 Credits

Sviluppato come sostituto standalone di Voicemeeter  
Engine audio: Python + sounddevice + numpy + scipy  
UI: CustomTkinter  

**ProMixer** © 2025 - MIXING4FUN Project
