# 🔄 Sincronizzazione Bus A1/A2 (Soundboard + Mixer)

## 📋 Panoramica

Il sistema integra **Soundboard** e **Mixer Professionale** condividendo i bus di output A1 e A2.

```
┌─────────────────────────────────────────────────────────────┐
│                    MIXING4FUN                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🎮 SOUNDBOARD          🎛️ MIXER PROFESSIONALE              │
│  ├─ Clip Audio          ├─ 5 Input Channels (HW1-3, VIRT1-2)│
│  ├─ Hotkeys             ├─ 5 Output Buses                    │
│  └─ Dual Output         │   ├─ Bus A1 ◄─┐                   │
│      ├─ Primary ───────►│   ├─ Bus A2 ◄─┤ SINCRONIZZATI     │
│      └─ Secondary ─────►│   ├─ Bus A3   │                   │
│                          │   ├─ Bus B1   │                   │
│                          │   └─ Bus B2   │                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Corrispondenze

| Tab Audio (Soundboard) | Tab Mixer | Funzione |
|---|---|---|
| **📤 Bus A1 - Output Primario** | **Bus A1** | Discord / Streaming |
| **🎧 Bus A2 - Output Secondario** | **Bus A2** | Monitor / Cuffie |

---

## ⚙️ Come Configurare

### Metodo 1: Dal Tab 🔊 Audio (Consigliato per principianti)

1. Vai su **🔊 Audio**
2. Configura:
   - **📤 Bus A1 - Output Primario**: Seleziona `CABLE Input (VB-Audio)` per Discord
   - **🎧 Bus A2 - Output Secondario**: Seleziona le tue cuffie per monitoraggio
   - Abilita la checkbox "✓ Abilita secondo output"
3. Clicca **✓ APPLICA CONFIGURAZIONE**

✅ **Risultato**: 
- La soundboard usa questi dispositivi
- Il mixer ProMixer viene automaticamente sincronizzato con gli stessi dispositivi

---

### Metodo 2: Dal Tab 🎛️ Mixer (Avanzato)

1. Vai su **🎛️ Mixer**
2. Clicca **⚙️ CONFIGURA**
3. Nella sezione **OUTPUT BUSES**, configura:
   - **Bus A1**: Seleziona `CABLE Input (VB-Audio)`
   - **Bus A2**: Seleziona `Headphones (Realtek)`
4. Chiudi la finestra

✅ **Risultato**: 
- Il mixer usa questi bus
- La soundboard viene automaticamente sincronizzata per usare gli stessi dispositivi

---

## 🔄 Sincronizzazione Automatica

La sincronizzazione è **bidirezionale**:

### Audio → Mixer
Quando applichi configurazione dal tab **🔊 Audio**:
```python
# Soundboard
mixer.output_device = A1_device_id
mixer.secondary_output_device = A2_device_id

# ProMixer automaticamente sincronizzato
pro_mixer.buses['A1'].device_id = A1_device_id
pro_mixer.buses['A2'].device_id = A2_device_id
```

### Mixer → Audio
Quando configuri **Bus A1** o **Bus A2** dal mixer:
```python
# ProMixer
pro_mixer.set_bus_device('A1', device_id)

# Soundboard automaticamente sincronizzata
mixer.output_device = device_id
# Salvato anche nel config
```

---

## 💾 Persistenza Configurazione

La configurazione viene salvata automaticamente in `soundboard_config.json`:

```json
{
  "audio_output_device": 12,      // Bus A1 - Primary
  "secondary_output_device": 8,   // Bus A2 - Secondary
  "clips": [...]
}
```

Al prossimo avvio, entrambi i sistemi (Soundboard e Mixer) useranno gli stessi dispositivi.

---

## 🎵 Routing Audio

### Esempio: Gaming + Discord + Monitor

```
┌──────────────────┐
│   🎮 CLIP        │
│   (soundboard)   │
└────────┬─────────┘
         ├──────────┐
         │          │
         ▼          ▼
    ┌────────┐ ┌────────┐
    │ Bus A1 │ │ Bus A2 │
    │ CABLE  │ │ Cuffie │
    └───┬────┘ └───┬────┘
        │          │
        ▼          ▼
    Discord     Ascolto
                Diretto
```

### Workflow:

1. **Premi hotkey** → Clip suona
2. **Soundboard invia a**:
   - Bus A1 (CABLE Input) → Voicemeeter/Discord → Amici sentono
   - Bus A2 (Cuffie) → Tu senti direttamente senza latenza

---

## 🎛️ Mixer Avanzato

### Altri Bus (A3, B1, B2)

I bus **A3**, **B1**, **B2** sono **indipendenti** e usati solo dal Mixer Professionale:

- **A3**: Output aggiuntivo (es: registrazione OBS su altra scheda)
- **B1**: Monitor alternativo (es: altoparlanti)
- **B2**: Backup output

Configurali dal tab **🎛️ Mixer** → **⚙️ CONFIGURA** per routing avanzato.

---

## 🔧 Risoluzione Problemi

### ❌ "Le clip non si sentono in Discord"
**Soluzione**: 
- Verifica che Bus A1 sia configurato su `CABLE Input`
- In Voicemeeter, assicurati che CABLE Output → VAIO (Virtual Input)

### ❌ "Non mi sento le clip in cuffia"
**Soluzione**: 
- Verifica che Bus A2 sia configurato sulle tue cuffie
- Abilita la checkbox "✓ Abilita secondo output" nel tab Audio

### ❌ "Mixer e Soundboard usano dispositivi diversi"
**Soluzione**: 
- Vai su **🔊 Audio** → **✓ APPLICA CONFIGURAZIONE**
- Questo forzerà la risincronizzazione

---

## 📖 Documentazione Correlata

- **MIXER_INTEGRATO.md**: Guida completa al mixer
- **PROMIXER_GUIDE.md**: Riferimento tecnico ProMixer
- **GUIDA_SETUP_AUDIO_COMPLETO.md**: Setup completo audio Windows

---

## 🎯 Comandi Rapidi

### Dalla Console Python (Debug)

```python
# Mostra dispositivi configurati
print(f"A1: {app.pro_mixer.buses['A1'].device_id}")
print(f"A2: {app.pro_mixer.buses['A2'].device_id}")
print(f"Soundboard Primary: {app.mixer.output_device}")
print(f"Soundboard Secondary: {app.mixer.secondary_output_device}")

# Forza sincronizzazione manuale
app.pro_mixer.buses['A1'].device_id = app.mixer.output_device
app.pro_mixer.buses['A2'].device_id = app.mixer.secondary_output_device
```

---

**🎉 Buon Mixing!**
