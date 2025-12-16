# 🎛️ Mixer Integrato - Guida Rapida

Il mixer professionale è ora **integrato direttamente nella soundboard**!

---

## 🚀 Accesso Rapido

1. Avvia la soundboard: `Avvia_Soundboard.bat` o `START.bat`
2. Clicca sulla tab **🎛️ Mixer**
3. Clicca su **⚙️ CONFIGURA** per assegnare dispositivi
4. Clicca su **▶ AVVIA MIXER** per attivarlo

---

## 📋 Configurazione Base

### **Step 1: Assegna Input**
```
⚙️ CONFIGURA → HARDWARE INPUTS
├─ Hardware 1 → Seleziona microfono fisico
├─ Hardware 2 → (opzionale)
└─ Hardware 3 → (opzionale)

⚙️ CONFIGURA → VIRTUAL INPUTS  
├─ Virtual 1 → CABLE Output (desktop audio)
└─ Virtual 2 → (opzionale)
```

### **Step 2: Assegna Output**
```
⚙️ CONFIGURA → OUTPUT BUSES
├─ Bus A1 → Cuffie/Speakers (ascolto personale)
├─ Bus A2 → CABLE Input (per Discord/OBS)
└─ Bus A3-B2 → (opzionali)
```

### **Step 3: Configura Routing**
Clicca sui bottoni **A1/A2/A3/B1/B2** di ogni canale:
```
Hardware 1 (Mic):   [A1✓] [A2✓] ← Attiva entrambi
Virtual 1 (Desktop): [A1✓] [A2 ] ← Solo A1 (non va su Discord)
```

### **Step 4: Avvia**
Clicca **▶ AVVIA MIXER** - Il mixer inizia a processare audio!

---

## 🎚️ Controlli Disponibili

### **Fader Verticali**
- Trascina su/giù per regolare volume (-60dB a +12dB)
- **0 dB** = volume normale
- **-60 dB** = silenzio
- **+12 dB** = boost massimo

### **Routing Matrix**
- **A1/A2/A3/B1/B2** = Bottoni per attivare/disattivare routing
- **Blu** = routing attivo
- **Grigio** = routing disattivato

### **Mute/Solo**
- **M** = Mute canale (silenzio)
- **S** = Solo canale (silenzia tutti gli altri)

### **VU Meters**
- **Verde** = livello normale (-inf a -12dB)
- **Giallo** = livello alto (-12dB a -3dB)
- **Rosso** = clipping (-3dB a 0dB)

---

## 🎯 Setup Comuni

### **Gaming + Discord**
```
INPUT:
├─ HW1 (Mic) → [A1] [A2]
└─ VIRT1 (Game) → [A1]

OUTPUT:
├─ A1 → Cuffie (ascolti game + tua voce)
└─ A2 → CABLE Input → Discord (solo voce)
```

### **Streaming OBS**
```
INPUT:
├─ HW1 (Mic) → [A1] [A2]
├─ VIRT1 (Desktop) → [A1] [A2]
└─ Soundboard clips → [A1] [A2]

OUTPUT:
├─ A1 → Cuffie (monitor)
└─ A2 → OBS Input (stream mix)
```

### **Multi-Output Recording**
```
OUTPUT:
├─ A1 → Cuffie (monitor live)
├─ A2 → Studio Monitors
├─ B1 → Interfaccia Recording
└─ B2 → (backup output)
```

---

## ⚙️ Differenze con Soundboard Base

| Feature | Soundboard Tab | Mixer Tab |
|---------|---------------|-----------|
| Scopo | Riproduce clip audio | Routing multi-canale |
| Input | File audio (MP3/WAV) | Microfono + Desktop |
| Output | 2 output max | 5 bus simultanei |
| Routing | Fisso | Configurabile |
| Hotkeys | ✅ Sì | ❌ No |
| Uso | Gaming/Meme sounds | Audio professionale |

**Puoi usare entrambi insieme!**
- Tab Soundboard: per suoni rapidi con hotkey
- Tab Mixer: per routing audio completo

---

## 🔄 Workflow Tipico

1. **Avvio:**
   - Avvia soundboard normale
   - Vai su tab Mixer
   - Configura dispositivi
   - Avvia mixer

2. **Durante l'uso:**
   - Regola fader per bilanciare volumi
   - Attiva/disattiva routing al volo
   - Usa mute per silenziare rapidamente

3. **Fine sessione:**
   - Clicca **⏹ FERMA MIXER**
   - Chiudi applicazione
   - Configurazione salvata automaticamente

---

## 🆚 Mixer vs Soundboard: Quando usare cosa?

### **Usa TAB SOUNDBOARD quando:**
- Vuoi riprodurre suoni/musica con hotkeys
- Gaming/streaming con meme sounds
- Clip veloci da attivare durante gameplay

### **Usa TAB MIXER quando:**
- Serve routing audio completo (mic + desktop)
- Multi-output verso più dispositivi
- Controllo professionale dei livelli
- Broadcasting/streaming avanzato

### **Usa ENTRAMBI per:**
Setup streaming completo dove:
- Soundboard gestisce effetti sonori
- Mixer gestisce routing voce + desktop

---

## 💡 Tips Utili

1. **Prima configura, poi avvia**: Assegna tutti i dispositivi prima di avviare mixer
2. **Monitor con A1**: Usa sempre A1 per le tue cuffie (monitor personale)
3. **Virtual cable**: VIRT1 = desktop audio via VB-Cable Output
4. **Routing multiplo**: Un canale può andare a più bus contemporaneamente
5. **Fader staging**: Mantieni fader tra -12dB e 0dB per audio pulito

---

## ❓ FAQ

**Q: Posso usare soundboard E mixer insieme?**  
A: Sì! Sono indipendenti. Soundboard usa il suo mixer interno, Mixer tab è separato.

**Q: Il mixer sostituisce Voicemeeter?**  
A: Sì completamente! Non serve Voicemeeter se usi il Mixer tab.

**Q: Quanti dispositivi posso collegare?**  
A: 5 input (3 HW + 2 Virtual) e 5 output (A1-A3, B1-B2).

**Q: Supporta ASIO?**  
A: Non ancora, usa WASAPI (latenza comunque bassa ~10ms).

**Q: Dove salva le impostazioni?**  
A: Nessun salvataggio automatico ancora - devi riconfigurare ad ogni avvio.

---

## 🐛 Troubleshooting

**❌ "Impossibile avviare mixer"**
- Chiudi altre app audio (Discord, OBS)
- Verifica dispositivi assegnati
- Controlla che non ci siano conflitti

**❌ "No audio in output"**
- Verifica routing attivo (bottoni blu)
- Controlla fader non a -60dB
- Verifica bus abbia dispositivo assegnato

**❌ "Audio distorto"**
- Abbassa fader dei canali
- Guarda VU meters (non deve essere rosso)
- Riduci gain input dispositivi

---

## 🎉 Vantaggi Integrazione

✅ **Tutto in un'app**: Non serve aprire mixer separato  
✅ **Stesso tema**: UI coerente con soundboard  
✅ **Configurazione unica**: File config condiviso  
✅ **Switch rapido**: Tab switching istantaneo  
✅ **Sincronizzato**: Tutto sullo stesso audio engine  

---

**Divertiti con il nuovo mixer integrato! 🎛️**
