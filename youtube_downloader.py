"""
YouTube Downloader Module - Gestisce il download e la conversione di clip da YouTube
"""
import customtkinter as ctk
from tkinter import messagebox
import os
import tempfile
import soundfile as sf
import numpy as np
from threading import Thread

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class YouTubeDownloader:
    """Gestisce il download da YouTube"""
    
    def __init__(self, parent, on_download_complete, colors, clips_folder=None):
        self.parent = parent
        self.on_download_complete = on_download_complete
        self.colors = colors
        self.is_downloading = False
        self.clips_folder = clips_folder or os.path.join(os.path.dirname(__file__), "clips")
    
    def parse_timestamp(self, timestamp_str):
        """Converte timestamp in formato m:s:ms o s:ms o s in secondi decimali
        
        Formati supportati:
        - "10" = 10 secondi
        - "45.2" = 45.2 secondi (con decimali)
        - "1:30" = 1 minuto e 30 secondi (90s)
        - "45:200" = 45 secondi e 200 millisecondi (45.2s) - se >59 è millisecondi
        - "1:40:500" = 1 minuto, 40 secondi, 500 millisecondi (100.5s)
        """
        if not timestamp_str or timestamp_str.strip() == "":
            return None
        
        timestamp_str = timestamp_str.strip()
        parts = timestamp_str.split(':')
        
        try:
            if len(parts) == 1:
                # Solo secondi: "10" o "10.5"
                return float(parts[0])
            elif len(parts) == 2:
                # Può essere mm:ss o ss:ms
                first = int(parts[0])
                second_str = parts[1]
                second = int(second_str)
                
                # Se il secondo valore è > 59, è millisecondi, altrimenti secondi
                if second >= 60 or len(second_str) >= 3:
                    # ss:ms (millisecondi)
                    ms = second
                    # Normalizza millisecondi a 3 cifre
                    if len(second_str) == 1:
                        ms *= 100  # 5 -> 500ms
                    elif len(second_str) == 2:
                        ms *= 10   # 50 -> 500ms
                    return first + (ms / 1000.0)
                else:
                    # mm:ss (minuti:secondi)
                    return first * 60 + second
            elif len(parts) == 3:
                # mm:ss:ms
                minutes = int(parts[0])
                seconds = int(parts[1])
                ms_str = parts[2]
                
                # Normalizza millisecondi
                ms = int(ms_str)
                if len(ms_str) == 1:
                    ms *= 100
                elif len(ms_str) == 2:
                    ms *= 10
                
                return minutes * 60 + seconds + (ms / 1000.0)
            else:
                raise ValueError("Formato non valido")
        except ValueError:
            raise ValueError(f"Formato timestamp non valido: '{timestamp_str}'\nUsa: 10 | 1:30 | 45:200 | 1:40:500")
    
    def create_youtube_tab(self, tab):
        """Crea l'interfaccia della tab YouTube"""
        frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="📥 Scarica Audio da YouTube",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        if not YT_DLP_AVAILABLE:
            warning = ctk.CTkLabel(
                frame,
                text="⚠️ yt-dlp non installato!\nEsegui: pip install yt-dlp",
                font=ctk.CTkFont(size=14),
                text_color="#ff6b6b"
            )
            warning.pack(pady=20)
        
        # URL Input
        ctk.CTkLabel(
            frame,
            text="🔗 URL Video YouTube:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.url_entry = ctk.CTkEntry(
            frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            width=600,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(pady=(0, 20), fill="x")
        
        # Time controls
        time_frame = ctk.CTkFrame(frame, fg_color=self.colors["bg_card"])
        time_frame.pack(pady=10, fill="x", padx=20)
        
        ctk.CTkLabel(
            time_frame,
            text="⏱️ Taglia Automaticamente (opzionale)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Start time
        ctk.CTkLabel(time_frame, text="Inizio:").grid(row=1, column=0, padx=10, pady=10)
        self.yt_start_entry = ctk.CTkEntry(time_frame, placeholder_text="0 o 1:30", width=120)
        self.yt_start_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # End time
        ctk.CTkLabel(time_frame, text="Fine:").grid(row=1, column=2, padx=10, pady=10)
        self.yt_end_entry = ctk.CTkEntry(time_frame, placeholder_text="5 o 1:40:50", width=120)
        self.yt_end_entry.grid(row=1, column=3, padx=10, pady=10)
        
        # Legenda formati
        ctk.CTkLabel(
            time_frame,
            text="💡 Formati: 10 (sec) | 1:30 (min:sec) | 45:200 (sec:ms) | 1:40:500 (min:sec:ms)",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        ).grid(row=2, column=0, columnspan=4, pady=(0, 10))
        
        # Quick select
        quick_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        quick_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ctk.CTkLabel(quick_frame, text="Quick:").pack(side="left", padx=5)
        
        for text, duration in [("3 sec", 3), ("5 sec", 5), ("10 sec", 10), ("30 sec", 30)]:
            ctk.CTkButton(
                quick_frame,
                text=text,
                command=lambda d=duration: self.quick_select(d),
                width=70,
                height=25,
                fg_color=self.colors["bg_card"]
            ).pack(side="left", padx=5)
        
        # Format selection
        format_frame = ctk.CTkFrame(frame, fg_color="transparent")
        format_frame.pack(pady=10)
        
        ctk.CTkLabel(
            format_frame,
            text="🎵 Formato Output:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=10)
        
        self.format_var = ctk.StringVar(value="wav")
        formats = [("WAV", "wav"), ("MP3", "mp3")]
        
        for text, value in formats:
            ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value
            ).pack(side="left", padx=10)
        
        # Progress
        self.yt_progress = ctk.CTkProgressBar(frame, width=600)
        self.yt_progress.pack(pady=20, fill="x", padx=50)
        self.yt_progress.set(0)
        
        self.yt_status = ctk.CTkLabel(
            frame,
            text="Pronto per scaricare",
            font=ctk.CTkFont(size=12)
        )
        self.yt_status.pack(pady=10)
        
        # Download button
        self.download_btn = ctk.CTkButton(
            frame,
            text="📥 Scarica e Aggiungi alla Soundboard",
            command=self.download_youtube,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"]
        )
        self.download_btn.pack(pady=20)
        
        # Info
        info_text = """
💡 COME FUNZIONA:
1. Incolla l'URL di un video YouTube
2. (Opzionale) Imposta inizio e fine per tagliare
3. Clicca "Scarica e Aggiungi"
4. La clip viene scaricata e aggiunta automaticamente alla soundboard!
5. Vai nella tab Soundboard per assegnare il tasto rapido

⚡ TIPS:
- Lascia vuoti inizio/fine per scaricare tutto l'audio
- Usa i pulsanti "Quick" per selezioni rapide
- Il formato WAV ha qualità migliore ma file più grandi
        """
        
        ctk.CTkLabel(
            frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="#aaa",
            justify="left"
        ).pack(pady=20, padx=20)
    
    def quick_select(self, duration):
        """Imposta rapidamente la durata"""
        self.yt_start_entry.delete(0, 'end')
        self.yt_start_entry.insert(0, "0")
        self.yt_end_entry.delete(0, 'end')
        self.yt_end_entry.insert(0, str(duration))
    
    def download_youtube(self):
        """Avvia il download da YouTube"""
        if not YT_DLP_AVAILABLE:
            messagebox.showerror("Errore", "yt-dlp non installato!\nEsegui: pip install yt-dlp")
            return
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Errore", "Inserisci un URL di YouTube!")
            return
        
        if self.is_downloading:
            messagebox.showwarning("Download", "Download già in corso!")
            return
        
        # Avvia download in thread separato
        thread = Thread(target=self._download_thread, args=(url,), daemon=True)
        thread.start()
    
    def _download_thread(self, url):
        """Thread per il download da YouTube"""
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ Download in corso...")
        
        try:
            # Ottieni parametri di taglio
            start_time = self.yt_start_entry.get().strip()
            end_time = self.yt_end_entry.get().strip()
            
            # Parse timestamp con supporto formati multipli
            try:
                start_sec = self.parse_timestamp(start_time)
                end_sec = self.parse_timestamp(end_time)
            except ValueError as e:
                messagebox.showerror("Errore Formato", str(e))
                self.is_downloading = False
                self.download_btn.configure(state="normal", text="📥 Scarica da YouTube")
                return
            
            # Crea cartella clips se non esiste
            os.makedirs(self.clips_folder, exist_ok=True)
            
            # File temporaneo per download
            temp_dir = tempfile.gettempdir()
            temp_base = f"yt_mixing4fun_{os.getpid()}"
            temp_file = os.path.join(temp_dir, temp_base)
            
            # Opzioni yt-dlp - scarica e converti con FFmpeg
            output_format = self.format_var.get()
            
            postprocessor_opts = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': output_format,
            }
            
            if start_sec is not None or end_sec is not None:
                postprocessor_opts['preferredquality'] = '192'
            
            # Percorso FFmpeg
            ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-essentials_build', 'bin')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_file + '.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._yt_progress_hook],
                'postprocessors': [postprocessor_opts],
                'ffmpeg_location': ffmpeg_path,
            }
            
            # Scarica
            self.yt_status.configure(text="📥 Scaricando da YouTube...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'audio')
                video_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50].strip()
                
                # Trova il file scaricato
                import glob
                possible_files = glob.glob(os.path.join(temp_dir, f"{temp_base}*"))
                
                if not possible_files:
                    raise Exception(f"File scaricato non trovato. Cercato: {temp_file}*")
                
                downloaded_file = possible_files[0]
                self.yt_status.configure(text=f"✅ Scaricato: {os.path.basename(downloaded_file)}")
                
                # Determina il file finale
                output_file = os.path.join(self.clips_folder, f"{video_title}.{output_format}")
                
                counter = 1
                while os.path.exists(output_file):
                    output_file = os.path.join(self.clips_folder, f"{video_title}_{counter}.{output_format}")
                    counter += 1
                
                # Elaborazione basata sul formato e taglio
                if (start_sec is not None or end_sec is not None) and output_format == 'wav':
                    # WAV con taglio: usa soundfile
                    self.yt_status.configure(text="✂️ Taglio clip...")
                    audio_data, sample_rate = sf.read(downloaded_file, always_2d=True)
                    
                    start_sample = int(start_sec * sample_rate) if start_sec else 0
                    end_sample = int(end_sec * sample_rate) if end_sec else len(audio_data)
                    audio_data = audio_data[start_sample:end_sample]
                    
                    self.yt_status.configure(text="🎚️ Normalizzazione...")
                    max_val = np.max(np.abs(audio_data))
                    if max_val > 0:
                        audio_data = audio_data / max_val * 0.95
                    
                    self.yt_status.configure(text=f"💾 Salvataggio...")
                    sf.write(output_file, audio_data, sample_rate)
                    
                elif (start_sec is not None or end_sec is not None):
                    # MP3 con taglio: usa FFmpeg
                    self.yt_status.configure(text="✂️ Taglio con FFmpeg...")
                    import subprocess
                    
                    # Percorso FFmpeg
                    ffmpeg_exe = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-essentials_build', 'bin', 'ffmpeg.exe')
                    
                    start_arg = ['-ss', str(start_sec)] if start_sec else []
                    duration = end_sec - (start_sec or 0) if end_sec else None
                    duration_arg = ['-t', str(duration)] if duration else []
                    
                    cmd = [ffmpeg_exe, '-i', downloaded_file] + start_arg + duration_arg + ['-acodec', 'copy', output_file, '-y']
                    
                    try:
                        subprocess.run(cmd, capture_output=True, check=True)
                    except subprocess.CalledProcessError:
                        cmd = [ffmpeg_exe, '-i', downloaded_file] + start_arg + duration_arg + [output_file, '-y']
                        subprocess.run(cmd, capture_output=True, check=True)
                else:
                    # Nessun taglio: copia diretta
                    self.yt_status.configure(text=f"💾 Salvataggio...")
                    import shutil
                    shutil.copy2(downloaded_file, output_file)
                
                # Rimuovi file temporanei
                try:
                    import glob
                    temp_files = glob.glob(os.path.join(temp_dir, f"{temp_base}*"))
                    for tf in temp_files:
                        try:
                            if os.path.exists(tf):
                                os.remove(tf)
                        except:
                            pass
                except:
                    pass
                
                # Notifica completamento
                self.yt_status.configure(text="✅ Aggiunta alla soundboard...")
                self.parent.after(100, lambda: self.on_download_complete(output_file))
                
                self.yt_progress.set(1.0)
                self.yt_status.configure(text=f"✅ Download completato! File: {os.path.basename(output_file)}")
                
                self.parent.after(2000, lambda: self.yt_progress.set(0))
                
        except Exception as e:
            self.yt_status.configure(text=f"❌ Errore: {str(e)}")
            messagebox.showerror("Errore Download", f"Impossibile scaricare:\n{str(e)}")
        
        finally:
            self.is_downloading = False
            self.download_btn.configure(state="normal", text="📥 Scarica e Aggiungi alla Soundboard")
    
    def _yt_progress_hook(self, d):
        """Hook per aggiornare la progress bar"""
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                percent = float(percent_str) / 100.0
                self.yt_progress.set(percent)
            except:
                pass
