# ⚠️ IMPORTANTE - Setup Microfono per Gaming

## 🎤 Come Funziona il Microfono

### IL PROBLEMA
Quando configuri l'output di Windows su VB-Cable, **il microfono non viene automaticamente instradato** al cavo virtuale. Questo significa che gli altri NON sentirebbero la tua voce.

### LA SOLUZIONE
Ci sono **2 modi** per far funzionare microfono + clip insieme:

---

## 🔧 METODO 1: VoiceMeeter (CONSIGLIATO)

### Cos'è?
Un mixer audio virtuale più potente di VB-Cable, GRATUITO.

### Download
https://vb-audio.com/Voicemeeter/

### Setup
1. **Installa VoiceMeeter Banana**
2. **Configura Input:**
   - Hardware Input 1 → Il tuo microfono fisico
   - Virtual Input → Soundboard (output del PC)

3. **Configura Output:**
   - A1 → Le tue cuffie (per sentire)
   - B1 → VB-Cable Input (per Discord)

4. **Discord:**
   - Input → VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)

### Pro
✅ Controllo totale su tutto l'audio
✅ Mixer professionale
✅ Funziona perfettamente

### Contro
❌ Setup leggermente più complesso
❌ Richiede un po' di pratica

---

## 🔧 METODO 2: Loopback + VB-Cable (SEMPLICE)

### Setup
1. **VB-Cable già installato**

2. **Abilita Loopback Microfono:**
   - Impostazioni Windows → Audio → Registrazione
   - Click destro sul tuo **Microfono** → Proprietà
   - Tab **"Ascolta"**
   - Spunta **"Ascolta il dispositivo"**
   - Seleziona **"CABLE Input (VB-Audio Virtual Cable)"**
   - ✅ Applica

3. **Output Windows:**
   - Output → CABLE Input (come già configurato)

4. **Discord:**
   - Input → CABLE Output

### Pro
✅ Semplicissimo
✅ Usa solo VB-Cable (già installato)

### Contro
❌ Potrebbe avere latenza maggiore
❌ Meno controllo fine

---

## 🎯 QUALE SCEGLIERE?

### Sei Nuovo? → METODO 2 (Loopback)
- Più semplice
- Funziona subito
- Perfetto per iniziare

### Vuoi Controllo Totale? → METODO 1 (VoiceMeeter)
- Audio professionale
- Zero problemi
- Configurazione più avanzata

---

## 🔍 VERIFICA CHE FUNZIONI

### Test Rapido
1. Avvia la Soundboard
2. Apri Discord
3. Vai in un canale vocale
4. Parla nel microfono → Gli altri ti devono sentire
5. Lancia una clip (tasto F1) → Gli altri devono sentirla
6. Parla MENTRE la clip suona → Gli altri devono sentire ENTRAMBI

### Se Non Funziona

**METODO 2 (Loopback):**
1. Verifica che il loopback del mic sia attivo
2. Controlla che "Ascolta il dispositivo" punti a CABLE Input
3. Aumenta il volume del microfono nella soundboard

**METODO 1 (VoiceMeeter):**
1. Verifica che Hardware Input 1 sia il tuo mic
2. Controlla che B1 sia attivo (click sul pulsante B1)
3. Verifica che Discord usi VoiceMeeter Output

---

## 📊 SCHEMA METODO 2 (Loopback)

```
Microfono Fisico
    ↓ (Loopback attivo)
CABLE Input ← Soundboard (clip + tutto l'audio PC)
    ↓
CABLE Output
    ↓
Discord → I tuoi amici sentono mic + clip!
```

## 📊 SCHEMA METODO 1 (VoiceMeeter)

```
Microfono Fisico → VoiceMeeter (Hardware Input 1)
                         ↓
Soundboard → VoiceMeeter (Virtual Input)
                         ↓
         VoiceMeeter Mixer (mixa tutto)
                         ↓
                    B1 Output
                         ↓
                 VoiceMeeter VAIO
                         ↓
                      Discord
                         ↓
         I tuoi amici sentono tutto!
```

---

## 🎚️ Regolare i Volumi

### METODO 2 (Loopback)
- **Microfono Windows**: 70-80%
- **Soundboard Mic**: 70-80%
- **Soundboard Clip**: 60-80%
- **Master**: 100%

### METODO 1 (VoiceMeeter)
- **Hardware Input 1 (Mic)**: -10dB
- **Virtual Input (Soundboard)**: -5dB
- **B1 Output**: 0dB
- **Soundboard Clip**: 60-80%

---

## 🐛 Troubleshooting Specifico

### Si sente eco/feedback
→ Disabilita "Ascolta il dispositivo" nelle tue cuffie
→ Abbassa il volume delle clip

### Latenza/delay
→ Usa METODO 1 (VoiceMeeter)
→ O riduci il buffer nella soundboard (512 → 256)

### Audio robotico
→ Aumenta il buffer (512 → 1024)
→ Chiudi altre app audio

### Doppia voce
→ Hai loopback attivo su troppi dispositivi
→ Controlla che sia attivo SOLO sul microfono

---

## 💡 Consiglio Finale

**Per iniziare velocemente:**
1. Usa METODO 2 (Loopback)
2. Testa che funzioni tutto
3. Se hai problemi, passa a METODO 1 (VoiceMeeter)

**Per audio professionale:**
1. Installa subito VoiceMeeter
2. Segui tutorial YouTube su VoiceMeeter
3. Vale la pena per il controllo totale!

---

## 🎓 Tutorial Video Consigliati

Cerca su YouTube:
- "VoiceMeeter Banana setup for Discord"
- "How to use VoiceMeeter for streaming"
- "VoiceMeeter soundboard setup"

---

**Buon gaming e buon divertimento! 🎮🎵**
