@echo off
echo.
echo ====================================
echo    PROMIXER - Professional Mixer
echo ====================================
echo.
echo Avvio mixer professionale...
echo.

python pro_mixer.py

if errorlevel 1 (
    echo.
    echo ERRORE: Impossibile avviare ProMixer
    echo.
    pause
)
