# 📁 Dove Salva i File il Soundboard

## 🗂️ Percorsi di Salvataggio

Quando usi l'eseguibile `SoundboardMixing4Fun.exe`, tutti i file vengono salvati **nella stessa cartella dell'exe**.

### File di Configurazione
```
📂 Stessa cartella dell'exe
├─ 📄 soundboard_config.json    ← Tutte le tue impostazioni
├─ 🔊 soundboard_on.wav          ← Suono attivazione
├─ 🔊 soundboard_off.wav         ← Suono disattivazione
└─ 📂 clips/                     ← Cartella clip (default)
```

### Cosa Salva `soundboard_config.json`
Il file di configurazione contiene:
- ✅ **Tutte le clip caricate** (percorsi file)
- ✅ **Volume di ogni clip** (impostazioni individuali)
- ✅ **Hotkey assegnati** (F1, F2, Numpad, ecc.)
- ✅ **Dispositivo audio primario** (Discord/CABLE)
- ✅ **Dispositivo audio secondario** (Cuffie)
- ✅ **Cartella clips personalizzata** (se modificata)

---

## 🔄 Come Funziona

### All'Avvio
1. Il programma cerca `soundboard_config.json` nella stessa cartella dell'exe
2. Carica tutte le clip salvate
3. Ripristina i volumi e gli hotkey
4. Imposta i dispositivi audio configurati

### Alla Chiusura
1. Salva automaticamente tutte le impostazioni in `soundboard_config.json`
2. Preserva hotkey, volumi, dispositivi audio
3. Salva il percorso della cartella clips personalizzata

---

## 📂 Spostare l'Exe

Se sposti l'exe in un'altra cartella:
1. **Porta con te** il file `soundboard_config.json`
2. **Porta con te** i file `soundboard_on.wav` e `soundboard_off.wav`
3. Le clip possono essere in **qualsiasi cartella** (il config salva i percorsi completi)

### Esempio:
```
Prima:
C:\Programmi\Soundboard\
├─ SoundboardMixing4Fun.exe
├─ soundboard_config.json
├─ soundboard_on.wav
├─ soundboard_off.wav
└─ clips\

Dopo (spostato):
D:\Giochi\Audio\
├─ SoundboardMixing4Fun.exe      ← Spostato
├─ soundboard_config.json        ← Porta con te
├─ soundboard_on.wav             ← Porta con te
├─ soundboard_off.wav            ← Porta con te
└─ clips\                        ← Porta con te (opzionale)
```

---

## 🆕 Cartella Clips Personalizzata

Puoi usare una cartella diversa per le clip:
1. Nel programma vai su **🎮 Soundboard** → **📂 Seleziona Cartella Clips**
2. Scegli una cartella (es: `D:\Audio\ClipsDivertenti\`)
3. Il percorso viene salvato automaticamente in `soundboard_config.json`

### Vantaggi:
- ✅ Clip separate dall'exe
- ✅ Backup più facile
- ✅ Condivisione tra computer (Dropbox, OneDrive)
- ✅ Non perdi le clip se reinstalli il programma

---

## 💾 Backup delle Impostazioni

Per salvare tutto:
```
1. Copia soundboard_config.json
2. Copia la cartella clips/ (o quella personalizzata)
3. Fine! 🎉
```

Per ripristinare:
```
1. Incolla soundboard_config.json nella cartella dell'exe
2. Riavvia il programma
3. Tutto torna come prima! ✅
```

---

## 🔧 Reset Totale

Se vuoi ricominciare da zero:
```
1. Chiudi il programma
2. Elimina soundboard_config.json
3. Riavvia → Come la prima volta
```

---

## ❓ FAQ

### "Non salva le impostazioni!"
- ✅ Verifica che l'exe abbia permessi di scrittura nella cartella
- ✅ Non mettere l'exe in `C:\Program Files\` (protetto)
- ✅ Mettilo in una cartella utente (es: `C:\Users\TuoNome\Soundboard\`)

### "Le clip non si caricano!"
- ✅ Controlla che i file esistano ancora nei percorsi salvati
- ✅ Se hai spostato le clip, ricaricale manualmente
- ✅ Oppure usa "📂 Seleziona Cartella Clips" per cambiarla

### "Gli hotkey non funzionano!"
- ✅ Verifica che non ci siano conflitti con altri programmi
- ✅ Riassegna gli hotkey manualmente se necessario
- ✅ Evita combinazioni già usate da Windows (es: Win+D)

---

**Creato per Gaming Soundboard - MIXING4FUN**  
*Ultima revisione: 30/11/2025*
