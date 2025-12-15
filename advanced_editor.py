"""
YouTube Downloader e Clip Editor Avanzato
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import soundfile as sf
import numpy as np
from pathlib import Path
import threading
import os
import tempfile

# Try to import yt-dlp
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False

ctk.set_appearance_mode("dark")

COLORS = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "success": "#00d9ff",
    "text": "#eaeaea"
}


class AdvancedClipEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🎬 YouTube Downloader & Clip Editor Avanzato")
        self.geometry("900x700")
        
        self.audio_data = None
        self.sample_rate = None
        self.file_path = None
        self.is_downloading = False
        
        self.create_ui()
    
    def create_ui(self):
        # Notebook per tab
        self.tabview = ctk.CTkTabview(self, width=850)
        self.tabview.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Tab 1: YouTube Downloader
        self.tab_youtube = self.tabview.add("📥 YouTube")
        self.create_youtube_tab()
        
        # Tab 2: Clip Editor
        self.tab_editor = self.tabview.add("✂️ Editor Clip")
        self.create_editor_tab()
        
        # Tab 3: Batch Processing
        self.tab_batch = self.tabview.add("📦 Batch")
        self.create_batch_tab()
    
    def create_youtube_tab(self):
        """Tab per scaricare da YouTube"""
        frame = ctk.CTkFrame(self.tab_youtube, fg_color="transparent")
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
        self.url_entry.pack(pady=(0, 20))
        
        # Time controls
        time_frame = ctk.CTkFrame(frame, fg_color=COLORS["bg_card"])
        time_frame.pack(pady=10, fill="x", padx=20)
        
        ctk.CTkLabel(
            time_frame,
            text="⏱️ Taglia Automaticamente (opzionale)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Start time
        ctk.CTkLabel(time_frame, text="Inizio (sec):").grid(row=1, column=0, padx=10, pady=10)
        self.yt_start_entry = ctk.CTkEntry(time_frame, placeholder_text="0", width=100)
        self.yt_start_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # End time
        ctk.CTkLabel(time_frame, text="Fine (sec):").grid(row=1, column=2, padx=10, pady=10)
        self.yt_end_entry = ctk.CTkEntry(time_frame, placeholder_text="5", width=100)
        self.yt_end_entry.grid(row=1, column=3, padx=10, pady=10)
        
        # Format selection
        format_frame = ctk.CTkFrame(frame, fg_color="transparent")
        format_frame.pack(pady=10)
        
        ctk.CTkLabel(
            format_frame,
            text="🎵 Formato Output:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=10)
        
        self.format_var = ctk.StringVar(value="wav")
        formats = [("WAV (migliore qualità)", "wav"), ("MP3 (file piccolo)", "mp3"), ("OGG", "ogg")]
        
        for text, value in formats:
            ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value
            ).pack(side="left", padx=10)
        
        # Progress
        self.yt_progress = ctk.CTkProgressBar(frame, width=600)
        self.yt_progress.pack(pady=20)
        self.yt_progress.set(0)
        
        self.yt_status = ctk.CTkLabel(
            frame,
            text="Pronto per scaricare",
            font=ctk.CTkFont(size=12)
        )
        self.yt_status.pack()
        
        # Download button
        self.download_btn = ctk.CTkButton(
            frame,
            text="📥 Scarica e Converti",
            command=self.download_youtube,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            width=300
        )
        self.download_btn.pack(pady=20)
        
        # Tips
        tips = ctk.CTkLabel(
            frame,
            text="💡 Suggerimenti:\n" +
                 "• Usa timestamp per scaricare solo la parte che ti serve\n" +
                 "• WAV per qualità massima, MP3 per risparmiare spazio\n" +
                 "• Funziona con video musicali, gameplay, podcast, etc.",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
            justify="left"
        )
        tips.pack(pady=10)
    
    def create_editor_tab(self):
        """Tab per editing avanzato"""
        frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="✂️ Editor Clip Avanzato",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # Load button
        self.load_btn = ctk.CTkButton(
            frame,
            text="📂 Carica File Audio",
            command=self.load_file,
            height=40,
            font=ctk.CTkFont(size=14),
            width=250
        )
        self.load_btn.pack(pady=10)
        
        # Info
        self.info_label = ctk.CTkLabel(
            frame,
            text="Nessun file caricato",
            font=ctk.CTkFont(size=12)
        )
        self.info_label.pack(pady=5)
        
        # Waveform placeholder (basic visualization)
        self.waveform_frame = ctk.CTkFrame(frame, height=150, fg_color=COLORS["bg_card"])
        self.waveform_frame.pack(pady=10, fill="x", padx=20)
        
        self.waveform_label = ctk.CTkLabel(
            self.waveform_frame,
            text="Waveform verrà mostrato qui dopo il caricamento",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.waveform_label.pack(pady=60)
        
        # Controls frame
        controls = ctk.CTkFrame(frame, fg_color=COLORS["bg_secondary"])
        controls.pack(pady=20, fill="x", padx=20)
        
        # Time controls
        ctk.CTkLabel(
            controls,
            text="⏱️ Selezione Temporale",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Start
        ctk.CTkLabel(controls, text="Inizio:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.start_entry = ctk.CTkEntry(controls, placeholder_text="0.0", width=100)
        self.start_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # End
        ctk.CTkLabel(controls, text="Fine:").grid(row=1, column=2, padx=10, pady=5, sticky="e")
        self.end_entry = ctk.CTkEntry(controls, placeholder_text="5.0", width=100)
        self.end_entry.grid(row=1, column=3, padx=10, pady=5)
        
        # Quick buttons
        quick_frame = ctk.CTkFrame(controls, fg_color="transparent")
        quick_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ctk.CTkLabel(
            quick_frame,
            text="Quick Select:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)
        
        quick_times = [("3 sec", 3), ("5 sec", 5), ("10 sec", 10), ("30 sec", 30)]
        for text, duration in quick_times:
            ctk.CTkButton(
                quick_frame,
                text=text,
                command=lambda d=duration: self.quick_select(d),
                width=70,
                height=25,
                fg_color=COLORS["bg_card"]
            ).pack(side="left", padx=5)
        
        # Duration display
        self.duration_label = ctk.CTkLabel(
            controls,
            text="Durata clip: 0.0s",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["success"]
        )
        self.duration_label.grid(row=3, column=0, columnspan=4, pady=10)
        
        # Effects
        effects_frame = ctk.CTkFrame(frame, fg_color=COLORS["bg_secondary"])
        effects_frame.pack(pady=10, fill="x", padx=20)
        
        ctk.CTkLabel(
            effects_frame,
            text="🎛️ Effetti e Modifiche",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Normalize
        self.normalize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            effects_frame,
            text="Normalizza Volume",
            variable=self.normalize_var
        ).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        # Fade in/out
        self.fade_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            effects_frame,
            text="Fade In/Out (0.1s)",
            variable=self.fade_var
        ).grid(row=1, column=1, padx=20, pady=5, sticky="w")
        
        # Remove silence
        self.silence_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            effects_frame,
            text="Rimuovi Silenzi",
            variable=self.silence_var
        ).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        # Mono/Stereo
        self.mono_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            effects_frame,
            text="Converti in Mono",
            variable=self.mono_var
        ).grid(row=2, column=1, padx=20, pady=5, sticky="w")
        
        # Action buttons
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(pady=20)
        
        ctk.CTkButton(
            action_frame,
            text="👂 Anteprima",
            command=self.preview_clip,
            width=150,
            height=40,
            fg_color=COLORS["success"]
        ).pack(side="left", padx=10)
        
        self.cut_btn = ctk.CTkButton(
            action_frame,
            text="✂️ Taglia e Salva",
            command=self.cut_and_save,
            width=150,
            height=40,
            state="disabled",
            fg_color=COLORS["accent"]
        )
        self.cut_btn.pack(side="left", padx=10)
        
        # Bind entries
        self.start_entry.bind("<KeyRelease>", self.update_duration)
        self.end_entry.bind("<KeyRelease>", self.update_duration)
    
    def create_batch_tab(self):
        """Tab per processing multiplo"""
        frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        title = ctk.CTkLabel(
            frame,
            text="📦 Batch Processing",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="Converti più file contemporaneamente",
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)
        
        # File list
        self.batch_files = []
        
        ctk.CTkButton(
            frame,
            text="📁 Aggiungi File",
            command=self.add_batch_files,
            height=40,
            width=200
        ).pack(pady=10)
        
        # Files display
        self.batch_list = ctk.CTkTextbox(frame, height=300, width=700)
        self.batch_list.pack(pady=10)
        
        # Batch options
        batch_opts = ctk.CTkFrame(frame, fg_color=COLORS["bg_card"])
        batch_opts.pack(pady=10, fill="x", padx=50)
        
        self.batch_normalize = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            batch_opts,
            text="Normalizza tutti",
            variable=self.batch_normalize
        ).pack(pady=5)
        
        self.batch_format = ctk.StringVar(value="wav")
        ctk.CTkLabel(batch_opts, text="Formato output:").pack()
        
        format_frame = ctk.CTkFrame(batch_opts, fg_color="transparent")
        format_frame.pack(pady=5)
        
        for fmt in ["wav", "mp3", "ogg"]:
            ctk.CTkRadioButton(
                format_frame,
                text=fmt.upper(),
                variable=self.batch_format,
                value=fmt
            ).pack(side="left", padx=10)
        
        # Process button
        ctk.CTkButton(
            frame,
            text="⚙️ Processa Tutti i File",
            command=self.process_batch,
            height=50,
            width=250,
            fg_color=COLORS["accent"],
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20)
    
    def download_youtube(self):
        """Scarica audio da YouTube"""
        if not YT_DLP_AVAILABLE:
            messagebox.showerror("Errore", "yt-dlp non installato!\nEsegui: pip install yt-dlp")
            return
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Errore", "Inserisci un URL YouTube valido!")
            return
        
        if self.is_downloading:
            messagebox.showwarning("Attenzione", "Download già in corso!")
            return
        
        # Start download in thread
        thread = threading.Thread(target=self._download_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url):
        """Thread per download"""
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ Scaricando...")
        
        try:
            # Parse time
            start_time = float(self.yt_start_entry.get() or 0)
            end_time = float(self.yt_end_entry.get() or 0) if self.yt_end_entry.get() else None
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            output_format = self.format_var.get()
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        percent = d.get('_percent_str', '0%').replace('%', '')
                        self.yt_progress.set(float(percent) / 100)
                        self.yt_status.configure(text=f"Scaricando... {percent}%")
                    except:
                        pass
                elif d['status'] == 'finished':
                    self.yt_status.configure(text="Conversione in corso...")
            
            # yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            # Add postprocessor for format conversion
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': output_format,
                'preferredquality': '192' if output_format == 'mp3' else '0',
            }]
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'audio')
                
            # Find downloaded file
            downloaded_file = None
            for f in os.listdir(temp_dir):
                if f.endswith(f'.{output_format}'):
                    downloaded_file = os.path.join(temp_dir, f)
                    break
            
            if not downloaded_file:
                raise Exception("File scaricato non trovato!")
            
            # Cut if needed
            if end_time and end_time > start_time:
                self.yt_status.configure(text="Tagliando clip...")
                audio, sr = sf.read(downloaded_file)
                
                start_idx = int(start_time * sr)
                end_idx = int(end_time * sr)
                
                if end_idx > len(audio):
                    end_idx = len(audio)
                
                audio = audio[start_idx:end_idx]
                
                # Save cut version
                cut_file = downloaded_file.replace(f'.{output_format}', f'_cut.{output_format}')
                sf.write(cut_file, audio, sr)
                downloaded_file = cut_file
            
            # Ask where to save
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            default_name = f"{safe_title}.{output_format}"
            
            save_path = filedialog.asksaveasfilename(
                defaultextension=f".{output_format}",
                initialfile=default_name,
                filetypes=[
                    (f"{output_format.upper()} files", f"*.{output_format}"),
                    ("All Files", "*.*")
                ]
            )
            
            if save_path:
                # Copy to destination
                import shutil
                shutil.copy2(downloaded_file, save_path)
                
                self.yt_progress.set(1)
                self.yt_status.configure(text="✅ Download completato!")
                
                messagebox.showinfo(
                    "Successo!",
                    f"Audio salvato:\n{Path(save_path).name}\n\n" +
                    f"Pronto per essere usato nella soundboard!"
                )
            else:
                self.yt_status.configure(text="Download annullato")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            self.yt_status.configure(text="❌ Errore!")
            messagebox.showerror("Errore", f"Errore durante il download:\n{str(e)}")
        
        finally:
            self.is_downloading = False
            self.download_btn.configure(state="normal", text="📥 Scarica e Converti")
            self.yt_progress.set(0)
    
    def load_file(self):
        """Carica file audio"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.audio_data, self.sample_rate = sf.read(file_path, dtype='float32')
                self.file_path = file_path
                
                duration = len(self.audio_data) / self.sample_rate
                filename = Path(file_path).name
                
                self.info_label.configure(
                    text=f"📁 {filename}\n⏱️ Durata: {duration:.2f}s | Sample Rate: {self.sample_rate}Hz"
                )
                
                self.cut_btn.configure(state="normal")
                
                # Set default end time
                self.end_entry.delete(0, "end")
                self.end_entry.insert(0, str(min(5.0, duration)))
                
                self.update_duration()
                self.draw_waveform()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile caricare il file:\n{str(e)}")
    
    def draw_waveform(self):
        """Disegna una rappresentazione semplice della waveform"""
        if self.audio_data is None:
            return
        
        # Simple text representation
        duration = len(self.audio_data) / self.sample_rate
        channels = "Stereo" if len(self.audio_data.shape) > 1 and self.audio_data.shape[1] == 2 else "Mono"
        
        self.waveform_label.configure(
            text=f"Audio caricato: {duration:.2f}s | {channels} | {self.sample_rate}Hz\n" +
                 "Usa i controlli sotto per tagliare la clip"
        )
    
    def quick_select(self, duration):
        """Selezione rapida durata"""
        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, "0")
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, str(duration))
        self.update_duration()
    
    def update_duration(self, event=None):
        """Aggiorna durata"""
        try:
            start = float(self.start_entry.get() or 0)
            end = float(self.end_entry.get() or 0)
            duration = end - start
            
            if duration > 0:
                self.duration_label.configure(
                    text=f"Durata clip: {duration:.2f}s ✓",
                    text_color="#00ff00"
                )
            else:
                self.duration_label.configure(
                    text="⚠️ Fine deve essere > Inizio",
                    text_color="#ff0000"
                )
        except:
            self.duration_label.configure(
                text="Durata clip: -",
                text_color="#888888"
            )
    
    def preview_clip(self):
        """Anteprima della clip"""
        messagebox.showinfo(
            "Anteprima",
            "Funzione anteprima in sviluppo!\n\n" +
            "Per ora, taglia e salva la clip,\n" +
            "poi ascoltala con un player audio."
        )
    
    def cut_and_save(self):
        """Taglia e salva con effetti"""
        if self.audio_data is None:
            return
        
        try:
            start = float(self.start_entry.get() or 0)
            end = float(self.end_entry.get() or 0)
            
            if start >= end:
                messagebox.showerror("Errore", "Il tempo di fine deve essere maggiore dell'inizio!")
                return
            
            # Calculate indices
            start_idx = int(start * self.sample_rate)
            end_idx = int(end * self.sample_rate)
            
            if start_idx < 0 or end_idx > len(self.audio_data):
                messagebox.showerror("Errore", "I tempi specificati sono fuori range!")
                return
            
            # Cut audio
            clip = self.audio_data[start_idx:end_idx].copy()
            
            # Apply effects
            if self.normalize_var.get():
                # Normalize
                max_val = np.max(np.abs(clip))
                if max_val > 0:
                    clip = clip / max_val * 0.95
            
            if self.fade_var.get():
                # Fade in/out
                fade_samples = int(0.1 * self.sample_rate)
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                
                if len(clip) > fade_samples * 2:
                    if len(clip.shape) == 1:
                        clip[:fade_samples] *= fade_in
                        clip[-fade_samples:] *= fade_out
                    else:
                        clip[:fade_samples] *= fade_in[:, np.newaxis]
                        clip[-fade_samples:] *= fade_out[:, np.newaxis]
            
            if self.mono_var.get() and len(clip.shape) > 1:
                # Convert to mono
                clip = np.mean(clip, axis=1)
            
            if self.silence_var.get():
                # Remove leading/trailing silence (basic)
                threshold = 0.01
                if len(clip.shape) == 1:
                    mask = np.abs(clip) > threshold
                else:
                    mask = np.any(np.abs(clip) > threshold, axis=1)
                
                if np.any(mask):
                    indices = np.where(mask)[0]
                    clip = clip[indices[0]:indices[-1]+1]
            
            # Ask where to save
            original_name = Path(self.file_path).stem
            save_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                initialfile=f"{original_name}_clip.wav",
                filetypes=[
                    ("WAV files", "*.wav"),
                    ("MP3 files", "*.mp3"),
                    ("OGG files", "*.ogg")
                ]
            )
            
            if save_path:
                sf.write(save_path, clip, self.sample_rate)
                
                effects_applied = []
                if self.normalize_var.get():
                    effects_applied.append("Normalizzato")
                if self.fade_var.get():
                    effects_applied.append("Fade")
                if self.mono_var.get():
                    effects_applied.append("Mono")
                if self.silence_var.get():
                    effects_applied.append("Silenzi rimossi")
                
                effects_text = "\n".join(f"✓ {e}" for e in effects_applied) if effects_applied else "Nessuno"
                
                messagebox.showinfo(
                    "Successo!",
                    f"Clip salvata:\n{Path(save_path).name}\n\n" +
                    f"Durata: {len(clip) / self.sample_rate:.2f}s\n\n" +
                    f"Effetti applicati:\n{effects_text}"
                )
                
        except ValueError:
            messagebox.showerror("Errore", "Inserisci valori numerici validi!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il taglio:\n{str(e)}")
    
    def add_batch_files(self):
        """Aggiungi file per batch processing"""
        files = filedialog.askopenfilenames(
            title="Seleziona file audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("All Files", "*.*")
            ]
        )
        
        if files:
            self.batch_files.extend(files)
            self.update_batch_list()
    
    def update_batch_list(self):
        """Aggiorna lista file batch"""
        self.batch_list.delete("1.0", "end")
        for i, f in enumerate(self.batch_files, 1):
            self.batch_list.insert("end", f"{i}. {Path(f).name}\n")
    
    def process_batch(self):
        """Processa file in batch"""
        if not self.batch_files:
            messagebox.showwarning("Attenzione", "Nessun file da processare!")
            return
        
        output_dir = filedialog.askdirectory(title="Seleziona cartella output")
        if not output_dir:
            return
        
        format_out = self.batch_format.get()
        normalize = self.batch_normalize.get()
        
        success = 0
        failed = 0
        
        for file_path in self.batch_files:
            try:
                audio, sr = sf.read(file_path)
                
                if normalize:
                    max_val = np.max(np.abs(audio))
                    if max_val > 0:
                        audio = audio / max_val * 0.95
                
                filename = Path(file_path).stem
                output_path = os.path.join(output_dir, f"{filename}_converted.{format_out}")
                
                sf.write(output_path, audio, sr)
                success += 1
                
            except Exception as e:
                print(f"Errore con {file_path}: {e}")
                failed += 1
        
        messagebox.showinfo(
            "Batch Completato",
            f"Processati: {success}\nFalliti: {failed}\n\nFile salvati in:\n{output_dir}"
        )
        
        self.batch_files.clear()
        self.update_batch_list()


if __name__ == "__main__":
    app = AdvancedClipEditor()
    app.mainloop()
