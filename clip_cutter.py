"""
Audio Clip Cutter - Tool semplice per tagliare clip audio
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import soundfile as sf
import numpy as np
from pathlib import Path

ctk.set_appearance_mode("dark")

class AudioCutter(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🎵 Audio Clip Cutter")
        self.geometry("600x400")
        
        self.audio_data = None
        self.sample_rate = None
        self.file_path = None
        
        # Header
        title = ctk.CTkLabel(
            self,
            text="✂️ Taglia Clip Audio",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Load button
        self.load_btn = ctk.CTkButton(
            self,
            text="📂 Carica File Audio",
            command=self.load_file,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.load_btn.pack(pady=10)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self,
            text="Nessun file caricato",
            font=ctk.CTkFont(size=12)
        )
        self.info_label.pack(pady=5)
        
        # Time controls frame
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(pady=20, padx=40, fill="x")
        
        # Start time
        ctk.CTkLabel(
            controls_frame,
            text="Inizio (secondi):",
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.start_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="0.0",
            width=100
        )
        self.start_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # End time
        ctk.CTkLabel(
            controls_frame,
            text="Fine (secondi):",
            font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.end_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="5.0",
            width=100
        )
        self.end_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # Duration info
        self.duration_label = ctk.CTkLabel(
            controls_frame,
            text="Durata clip: 0.0s",
            font=ctk.CTkFont(size=11)
        )
        self.duration_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Cut button
        self.cut_btn = ctk.CTkButton(
            self,
            text="✂️ Taglia e Salva",
            command=self.cut_and_save,
            height=40,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.cut_btn.pack(pady=20)
        
        # Tips
        tips = ctk.CTkLabel(
            self,
            text="💡 Suggerimento: Le clip di 2-5 secondi sono perfette per soundboard!",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        tips.pack(pady=10)
        
        # Bind entries to update duration
        self.start_entry.bind("<KeyRelease>", self.update_duration)
        self.end_entry.bind("<KeyRelease>", self.update_duration)
    
    def load_file(self):
        """Carica un file audio"""
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
                    text=f"📁 {filename}\n⏱️ Durata totale: {duration:.2f} secondi"
                )
                
                self.cut_btn.configure(state="normal")
                
                # Set default end time
                self.end_entry.delete(0, "end")
                self.end_entry.insert(0, str(min(5.0, duration)))
                
                self.update_duration()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile caricare il file:\n{str(e)}")
    
    def update_duration(self, event=None):
        """Aggiorna la durata della clip"""
        try:
            start = float(self.start_entry.get() or 0)
            end = float(self.end_entry.get() or 0)
            duration = end - start
            
            if duration > 0:
                self.duration_label.configure(
                    text=f"Durata clip: {duration:.2f}s",
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
    
    def cut_and_save(self):
        """Taglia e salva la clip"""
        if self.audio_data is None:
            return
        
        try:
            start = float(self.start_entry.get() or 0)
            end = float(self.end_entry.get() or 0)
            
            if start >= end:
                messagebox.showerror("Errore", "Il tempo di fine deve essere maggiore dell'inizio!")
                return
            
            # Calcola gli indici
            start_idx = int(start * self.sample_rate)
            end_idx = int(end * self.sample_rate)
            
            # Controlla limiti
            if start_idx < 0 or end_idx > len(self.audio_data):
                messagebox.showerror("Errore", "I tempi specificati sono fuori range!")
                return
            
            # Taglia l'audio
            clip = self.audio_data[start_idx:end_idx]
            
            # Chiedi dove salvare
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
                # Salva la clip
                sf.write(save_path, clip, self.sample_rate)
                
                messagebox.showinfo(
                    "Successo!",
                    f"Clip salvata:\n{Path(save_path).name}\n\n" +
                    f"Durata: {len(clip) / self.sample_rate:.2f}s"
                )
                
        except ValueError:
            messagebox.showerror("Errore", "Inserisci valori numerici validi per inizio e fine!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il taglio:\n{str(e)}")


if __name__ == "__main__":
    app = AudioCutter()
    app.mainloop()
