@echo off
chcp 65001 >nul
echo ================================================
echo    🎮 GAMING SOUNDBOARD - Avvio Automatico
echo ================================================
echo.

REM Forza configurazione CABLE Input
echo [1/4] Configurazione dispositivo audio...
python force_cable.py
if errorlevel 1 (
    echo ❌ Errore configurazione!
    pause
    exit /b 1
)
echo ✓ CABLE Input configurato (Device 22, 48kHz)
echo.

REM Aggiungi FFmpeg al PATH
echo [2/4] Configurazione FFmpeg...
set PATH=%PATH%;%~dp0ffmpeg-8.0.1-essentials_build\bin
echo ✓ FFmpeg aggiunto al PATH
echo.

REM Controlla se in esecuzione come amministratore
echo [3/4] Verifica permessi amministratore...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Esecuzione come Amministratore
) else (
    echo ⚠️  NON amministratore - hotkeys potrebbero non funzionare
    echo    (Click destro sul file e "Esegui come amministratore")
)
echo.

REM Avvia soundboard
echo [4/4] Avvio soundboard...
echo.
echo ================================================
echo    ✅ SOUNDBOARD PRONTO!
echo ================================================
echo 🔊 Output: CABLE Input (Device 22)
echo 🎵 Sample Rate: 48000 Hz (Discord)
echo ⌨️  Hotkeys: F1-F12, A-Z, Numpad
echo.
echo ⚠️  ASSICURATI CHE VOICEMEETER SIA APERTO!
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Errore durante l'esecuzione!
    pause
)
