# 🐛 DEBUG HOTKEYS - Guida alla Risoluzione Problemi

## 📋 Se le Hotkeys non Funzionano

### 1️⃣ Controlla il File di Log

Quando esegui `SoundboardMixing4Fun.exe`, viene creato automaticamente un file di log:

```
📂 Stessa cartella dell'exe
└─ 📄 soundboard.log    ← File di log con tutti i dettagli
```

### 2️⃣ Apri il File di Log

1. Apri `soundboard.log` con Notepad o qualsiasi editor di testo
2. Cerca questi messaggi:

```
✅ TUTTO OK:
INFO - Hotkey globale registrato: Scroll Lock = Toggle Soundboard
INFO - Hotkey 'f1' assegnato a 'clip_name'
INFO - Toggle soundboard chiamato!
DEBUG - Hotkey premuto per: clip_name

❌ PROBLEMI:
ERROR - Errore registrazione hotkey globale: ...
ERROR - ERRORE in toggle_soundboard: ...
ERROR - ERRORE in trigger_clip_hotkey: ...
```

---

## 🔍 Problemi Comuni

### ❌ "Hotkey non si registrano"

**Sintomo nel log:**
```
ERROR - Errore registrazione hotkey globale: Access denied
```

**Causa:** L'exe potrebbe non avere i permessi necessari su Windows.

**Soluzione:**
1. **Chiudi** il programma
2. Click destro su `SoundboardMixing4Fun.exe`
3. **Esegui come amministratore**
4. Verifica nel log se ora funziona

---

### ❌ "Scroll Lock non funziona"

**Sintomo:** Premi Scroll Lock ma non succede nulla.

**Verifica nel log:**
```
# Se vedi questo = hotkey registrato:
INFO - Hotkey globale registrato: Scroll Lock = Toggle Soundboard

# Se premi Scroll Lock dovresti vedere:
INFO - Toggle soundboard chiamato!
INFO - SOUNDBOARD DISABILITATA ✗
# oppure
INFO - SOUNDBOARD ABILITATA ✓
```

**Se non vedi "Toggle soundboard chiamato!":**
- La libreria `keyboard` potrebbe avere problemi
- Prova a eseguire come **amministratore**
- Verifica che nessun altro programma usi Scroll Lock (es: AutoHotkey, altri macro software)

---

### ❌ "Hotkey clip non funzionano (F1, F2, etc.)"

**Sintomo:** Premi F1 ma la clip non si avvia.

**Verifica nel log:**
```
# Se vedi questo = hotkey assegnato:
INFO - Hotkey 'f1' assegnato a 'nome_clip'

# Se premi F1 dovresti vedere:
DEBUG - Hotkey premuto per: nome_clip (enabled: True)

# Se la soundboard è disabilitata vedrai:
DEBUG - Soundboard disabilitata, ignoro hotkey
```

**Soluzioni:**
1. **Abilita la soundboard:** Premi **Scroll Lock** finché non vedi nel log:
   ```
   INFO - SOUNDBOARD ABILITATA ✓
   ```
2. **Verifica conflitti:** Chiudi altri programmi che usano F1-F12 (Discord overlay, OBS, etc.)
3. **Riassegna hotkey:** Nel programma, usa tasti diversi (es: Numpad 1-9)

---

## 🛠️ Soluzioni Avanzate

### Esegui come Amministratore (Permanente)

1. Click destro su `SoundboardMixing4Fun.exe`
2. **Proprietà** → Tab **Compatibilità**
3. Spunta: **☑ Esegui questo programma come amministratore**
4. **Applica** → **OK**

Ora l'exe avrà sempre i permessi necessari per le hotkeys globali.

---

### Verifica Conflitti con Altri Programmi

Programmi che potrebbero interferire:
- ❌ **AutoHotkey** (script in esecuzione)
- ❌ **Discord** (overlay con hotkeys)
- ❌ **OBS Studio** (hotkeys globali)
- ❌ **GeForce Experience** (Shadowplay)
- ❌ **Software RGB** (Logitech G Hub, Razer Synapse)

**Soluzione:** Chiudi temporaneamente questi programmi e riprova.

---

### Reset Completo Hotkeys

Se nulla funziona:

1. Chiudi il programma
2. Elimina `soundboard_config.json`
3. Riavvia il programma
4. Riassegna manualmente gli hotkey

---

## 📊 Interpretare il Log

### Log di Successo (Tutto OK)
```
2025-11-30 01:00:00 - INFO - Hotkey globale registrato: Scroll Lock = Toggle Soundboard
2025-11-30 01:00:05 - INFO - Toggle soundboard chiamato! (attuale: True)
2025-11-30 01:00:05 - INFO - SOUNDBOARD ABILITATA ✓
2025-11-30 01:00:10 - INFO - Hotkey 'f1' assegnato a 'risata'
2025-11-30 01:00:15 - DEBUG - Hotkey premuto per: risata (enabled: True)
```
✅ **TUTTO FUNZIONA!**

### Log con Errori
```
2025-11-30 01:00:00 - ERROR - Errore registrazione hotkey globale: Access is denied
2025-11-30 01:00:05 - ERROR - ERRORE in toggle_soundboard: 'NoneType' object has no attribute 'configure'
```
❌ **PROBLEMI:** Esegui come amministratore

---

## 💡 Tips

### Usa Tasti Alternativi

Se F1-F12 danno problemi, usa:
- **Numpad 0-9** (tastierino numerico)
- **Home, End, Page Up, Page Down**
- **Insert, Delete**

Evita:
- ❌ Ctrl+qualcosa (già usato da Windows/programmi)
- ❌ Alt+qualcosa (menù applicazioni)
- ❌ Win+qualcosa (shortcuts Windows)

### Testa Prima con lo Script Python

Se hai Python installato:
```powershell
python main.py
```

Se funziona con lo script ma non con l'exe → problema di permessi → esegui exe come amministratore.

---

## 📞 Se Ancora Non Funziona

Invia il file `soundboard.log` per analisi dettagliata!

Il log contiene tutte le informazioni necessarie per capire:
- ✅ Quali hotkey sono stati registrati
- ❌ Quali errori si sono verificati
- 🔍 Cosa succede quando premi i tasti

---

**Creato per Gaming Soundboard - MIXING4FUN**  
*Ultima revisione: 30/11/2025*
