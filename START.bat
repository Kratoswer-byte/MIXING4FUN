@echo off
echo ========================================
echo   SOUNDBOARD UNIFICATA - Test Veloce
echo ========================================
echo.
echo Caratteristiche:
echo  - Tab Soundboard (lancia clip con hotkeys)
echo  - Tab YouTube (scarica clip da YouTube)
echo  - Tutto in UN programma!
echo.
echo Premi un tasto per avviare...
pause >nul

set PATH=%PATH%;%~dp0ffmpeg-8.0.1-essentials_build\bin
python main.py
