# 🚀 Setup Repository Git

## ✅ Repository Locale Creato

Il repository Git è stato inizializzato con successo!

**Commit iniziale fatto**: 52 file, 11.206+ righe di codice

---

## 📤 Push su GitHub

### **Opzione 1: Nuovo Repository GitHub**

1. **Vai su GitHub.com** e crea nuovo repository
   - Nome: `MIXING4FUN` o `soundboard-mixer`
   - Descrizione: "Professional Soundboard with integrated Audio Mixer"
   - **NON** inizializzare con README (hai già i file)

2. **Collega il repository remoto:**
```bash
git remote add origin https://github.com/TUO_USERNAME/MIXING4FUN.git
git branch -M main
git push -u origin main
```

3. **Inserisci credenziali GitHub** quando richiesto

---

### **Opzione 2: Repository Privato GitHub**

Se vuoi mantenerlo privato:

1. Crea repository come **Private** su GitHub
2. Usa gli stessi comandi sopra
3. Solo tu (e chi inviti) potrete accedervi

---

## 🔄 Sincronizzazione tra PC

### **Sul PC Attuale (dopo ogni modifica):**
```bash
cd C:\Users\Francesco_pc\Desktop\MIXING4FUN
git add .
git commit -m "Descrizione modifiche"
git push
```

### **Su Altro PC (prima volta):**
```bash
git clone https://github.com/TUO_USERNAME/MIXING4FUN.git
cd MIXING4FUN
pip install -r requirements.txt
```

### **Su Altro PC (aggiornamenti):**
```bash
cd MIXING4FUN
git pull
```

---

## 📋 File NON nel Repository (per scelta)

### **Esclusi dal .gitignore:**
- `soundboard_config.json` - Config locale con path specifici
- `clips/*.mp3`, `clips/*.wav` - File audio (troppo grandi)
- `build/`, `dist/` - Build temporanei
- `__pycache__/` - Cache Python
- `ffmpeg-*/` - FFmpeg binari (troppo grandi)
- `soundboard.log` - Log locali

### **Come Gestire File Esclusi:**

#### **1. Configurazione:**
Copia manualmente `soundboard_config.json` tra PC, oppure riconfigura dispositivi audio.

#### **2. Clips Audio:**
**Opzione A**: Condividi via cloud (Dropbox, Google Drive)
**Opzione B**: Usa Git LFS per file grandi:
```bash
git lfs install
git lfs track "*.mp3" "*.wav"
git add .gitattributes
git commit -m "Add LFS tracking"
```

#### **3. FFmpeg:**
Scarica su ogni PC da: https://ffmpeg.org/download.html  
Estrai nella cartella del progetto

---

## 🔐 Autenticazione GitHub

### **Token Personale (Consigliato):**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Seleziona `repo` scope
4. Copia token
5. Usa token come password quando fai `git push`

### **GitHub Desktop (Alternativa Facile):**
1. Installa GitHub Desktop
2. File → Add Local Repository
3. Seleziona `MIXING4FUN`
4. Publish repository
5. Sync automatico con click

---

## 📊 Statistiche Repository

```
52 file totali
11.206+ righe di codice
Linguaggi:
  - Python: ~8.000 righe
  - Markdown: ~3.000 righe
  - Batch: ~200 righe
```

---

## 🎯 Branch Strategy (Opzionale)

Se vuoi lavorare in modo più organizzato:

```bash
# Branch principale (stabile)
main

# Branch sviluppo
git checkout -b dev
# Lavora qui, testa
git commit -m "Nuove feature"

# Merge quando stabile
git checkout main
git merge dev
git push
```

---

## ✅ Quick Reference

### **Comandi Base:**
```bash
git status              # Vedi modifiche
git add .               # Aggiungi tutti i file
git commit -m "msg"     # Commit locale
git push                # Carica su GitHub
git pull                # Scarica da GitHub
git log --oneline       # Vedi cronologia
```

### **Comandi Utili:**
```bash
git diff                # Vedi cosa è cambiato
git restore file.py     # Annulla modifiche locali
git reset --hard        # Ripristina tutto
git clone URL           # Clona repository
```

---

## 🆘 Problemi Comuni

### ❌ "failed to push some refs"
```bash
git pull --rebase
git push
```

### ❌ "refusing to merge unrelated histories"
```bash
git pull origin main --allow-unrelated-histories
```

### ❌ File troppo grandi
```bash
# Rimuovi dal tracking
git rm --cached file.mp3
# Aggiungi a .gitignore
echo "file.mp3" >> .gitignore
git commit -m "Remove large file"
```

---

## 📝 Prossimi Step

1. ✅ **Fatto**: Repository locale inizializzato
2. **Ora**: Crea repository su GitHub
3. **Poi**: `git remote add origin URL`
4. **Infine**: `git push -u origin main`

Su altro PC:
1. `git clone URL`
2. `pip install -r requirements.txt`
3. Configura dispositivi audio
4. `python main.py`

---

**Repository pronto per essere condiviso! 🎉**
