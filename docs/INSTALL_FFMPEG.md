# ⚡ QUICK SETUP - FFmpeg per Windows

## 🎯 Cos'è FFmpeg?
FFmpeg è necessario per:
- ✅ Scaricare audio da YouTube
- ✅ Convertire formati (MP3, OGG, etc.)
- ✅ Editor avanzato

## 🚀 INSTALLAZIONE RAPIDA (3 metodi)

---

### 📦 METODO 1: Scoop (CONSIGLIATO - più facile)

#### Installa Scoop (se non ce l'hai)
Apri PowerShell e esegui:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
```

#### Installa FFmpeg
```powershell
scoop install ffmpeg
```

✅ **FATTO!** FFmpeg è installato e nel PATH.

---

### 🍫 METODO 2: Chocolatey

Se hai Chocolatey installato:
```powershell
choco install ffmpeg
```

---

### 📥 METODO 3: Manuale (se gli altri non funzionano)

#### 1. Scarica FFmpeg
- Vai su: https://www.gyan.dev/ffmpeg/builds/
- Scarica **ffmpeg-release-essentials.zip**
- Estrai in `C:\ffmpeg`

#### 2. Aggiungi al PATH
1. Cerca "Variabili d'ambiente" in Windows
2. Click su "Variabili d'ambiente"
3. Nella sezione "Variabili utente", seleziona "Path"
4. Click "Modifica"
5. Click "Nuovo"
6. Aggiungi: `C:\ffmpeg\bin`
7. Click "OK" su tutto
8. **RIAVVIA il terminale**

---

## ✅ VERIFICA INSTALLAZIONE

Apri PowerShell e esegui:
```powershell
ffmpeg -version
```

**Se vedi la versione di FFmpeg** → ✅ Tutto OK!

**Se vedi "comando non riconosciuto"** → ❌ Ricontrolla il PATH o riavvia PC

---

## 🎬 DOPO L'INSTALLAZIONE

Ora puoi:
1. Lanciare `Editor_Avanzato.bat`
2. Tab "📥 YouTube"
3. Scaricare audio da YouTube!

---

## 🆘 PROBLEMI?

### "ffmpeg non trovato"
→ Riavvia il terminale/PC dopo installazione
→ Verifica PATH: deve contenere la cartella con ffmpeg.exe

### "Access denied"
→ Esegui PowerShell come Amministratore

### Scoop non si installa
→ Verifica ExecutionPolicy:
```powershell
Get-ExecutionPolicy
```
→ Deve essere RemoteSigned o Unrestricted

---

## 💡 RACCOMANDAZIONE

**Usa METODO 1 (Scoop)** perché:
- ✅ Più facile
- ✅ Gestisce automaticamente il PATH
- ✅ Facile da aggiornare: `scoop update ffmpeg`
- ✅ Utile per altri tool in futuro

---

**Una volta installato FFmpeg, potrai scaricare da YouTube! 🎉**
