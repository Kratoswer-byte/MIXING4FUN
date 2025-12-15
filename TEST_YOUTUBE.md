# 🧪 TEST YouTube Download

## Test Rapido MP3

1. **Avvia**: `START.bat` o `python main.py`
2. **Tab YouTube**
3. **URL Test**: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
4. **Inizio**: `0`
5. **Fine**: `5`
6. **Formato**: Seleziona **MP3**
7. **Clicca**: "Scarica e Aggiungi alla Soundboard"

### ✅ Cosa Dovrebbe Succedere

1. Progress bar si riempie
2. Status: "📥 Scaricando da YouTube..."
3. Status: "✅ Scaricato: ..."
4. Status: "✂️ Taglio con FFmpeg..." (se hai messo inizio/fine)
5. Status: "💾 Salvataggio..."
6. Status: "✅ Aggiunta alla soundboard..."
7. **Automaticamente passa alla tab Soundboard**
8. **Vedi la clip aggiunta!**

### 🎵 Verifica

- Controlla cartella `clips/` → File MP3 presente
- Tab Soundboard → Clip caricata
- Clicca "Tasto: -" → Assegna F1
- Clicca Play → Senti la clip!

## Test Rapido WAV

Stesso procedimento ma:
- **Formato**: Seleziona **WAV**

WAV usa soundfile per taglio + normalizzazione automatica.

## 🐛 Se Non Funziona

### Errore: "File scaricato non trovato"
→ Verifica che FFmpeg sia nel PATH:
```powershell
ffmpeg -version
```

### Errore: "yt-dlp non installato"
→ Installa:
```powershell
pip install yt-dlp
```

### La clip non si sente
→ Verifica:
1. Volume clip non a zero
2. Master volume alto
3. File nella cartella `clips/` esiste

## 💡 Tips

- **WAV**: Qualità migliore, normalizzazione automatica
- **MP3**: File più piccolo, taglio veloce con FFmpeg
- **Quick buttons**: Usa 3s, 5s, 10s per test rapidi
