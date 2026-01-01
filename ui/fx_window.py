"""
Finestra Effetti Audio per Canali Mixer
Noise Gate, Compressor, EQ
"""
import customtkinter as ctk
from tkinter import messagebox
from .colors import COLORS


class ChannelFXWindow(ctk.CTkToplevel):
    """Finestra per configurare effetti audio di un canale"""
    
    def __init__(self, parent, pro_mixer, channel_id):
        super().__init__(parent)
        
        self.parent = parent
        self.pro_mixer = pro_mixer
        self.channel_id = channel_id
        self.channel = pro_mixer.channels[channel_id]
        self.processor = self.channel.processor
        
        # Configurazione finestra
        self.title(f"Effetti Audio - {channel_id}")
        self.geometry("500x650")
        self.configure(fg_color=COLORS["bg_primary"])
        
        # Centra la finestra
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.create_ui()
        
        # Modal
        self.transient(parent)
        self.grab_set()
    
    def create_ui(self):
        """Crea l'interfaccia"""
        # Header
        header = ctk.CTkLabel(
            self,
            text=f"🎛️ Effetti Audio: {self.channel_id}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["accent"]
        )
        header.pack(pady=20)
        
        # Container scrollabile
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # NOISE GATE
        self.create_gate_section(container)
        
        # COMPRESSOR
        self.create_compressor_section(container)
        
        # EQUALIZER
        self.create_eq_section(container)
        
        # Pulsanti
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        
        reset_btn = ctk.CTkButton(
            btn_frame,
            text="Reset Tutti",
            command=self.reset_all,
            width=150,
            fg_color=COLORS["danger"]
        )
        reset_btn.pack(side="left", padx=10)
        
        close_btn = ctk.CTkButton(
            btn_frame,
            text="Chiudi",
            command=self.destroy,
            width=150
        )
        close_btn.pack(side="left", padx=10)
    
    def create_gate_section(self, parent):
        """Sezione Noise Gate"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=10)
        frame.pack(fill="x", pady=10, padx=5)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title = ctk.CTkLabel(
            header_frame,
            text="🔇 Noise Gate",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(side="left")
        
        # Toggle
        self.gate_switch = ctk.CTkSwitch(
            header_frame,
            text="Attivo",
            command=self.toggle_gate,
            progress_color=COLORS["success"]
        )
        self.gate_switch.pack(side="right")
        if self.processor.gate_enabled:
            self.gate_switch.select()
        
        # Threshold
        threshold_frame = ctk.CTkFrame(frame, fg_color="transparent")
        threshold_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            threshold_frame,
            text="Threshold (dB):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.gate_threshold_label = ctk.CTkLabel(
            threshold_frame,
            text=f"{self.processor.gate_threshold:.1f} dB",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.gate_threshold_label.pack(side="right")
        
        self.gate_threshold_slider = ctk.CTkSlider(
            frame,
            from_=-80,
            to=-10,
            number_of_steps=70,
            command=self.on_gate_threshold_change,
            progress_color=COLORS["accent"]
        )
        self.gate_threshold_slider.set(self.processor.gate_threshold)
        self.gate_threshold_slider.pack(fill="x", padx=15, pady=(5, 10))
        
        # Gate Meter (indicatore livello)
        meter_frame = ctk.CTkFrame(frame, fg_color="transparent")
        meter_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            meter_frame,
            text="Livello Gate:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.gate_meter_label = ctk.CTkLabel(
            meter_frame,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["success"]
        )
        self.gate_meter_label.pack(side="right")
        
        # Canvas per meter custom (più stabile di CTkProgressBar)
        self.gate_meter_canvas = ctk.CTkCanvas(
            frame,
            height=15,
            bg=COLORS["bg_card"],
            highlightthickness=0
        )
        self.gate_meter_canvas.pack(fill="x", padx=15, pady=(0, 10))
        
        # Avvia aggiornamento meter dopo 100ms
        self.after(100, self.update_gate_meter)
        
        # Info
        info = ctk.CTkLabel(
            frame,
            text="Gate intelligente con hold time (250ms).\nFiltra rumori brevi mantenendo aperta la voce.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            justify="left"
        )
        info.pack(padx=15, pady=(0, 15))
    
    def create_compressor_section(self, parent):
        """Sezione Compressor"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=10)
        frame.pack(fill="x", pady=10, padx=5)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        title = ctk.CTkLabel(
            header_frame,
            text="🎚️ Compressor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(side="left")
        
        # Toggle
        self.comp_switch = ctk.CTkSwitch(
            header_frame,
            text="Attivo",
            command=self.toggle_compressor,
            progress_color=COLORS["success"]
        )
        self.comp_switch.pack(side="right")
        if self.processor.comp_enabled:
            self.comp_switch.select()
        
        # Threshold
        threshold_frame = ctk.CTkFrame(frame, fg_color="transparent")
        threshold_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            threshold_frame,
            text="Threshold (dB):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.comp_threshold_label = ctk.CTkLabel(
            threshold_frame,
            text=f"{self.processor.compressor_threshold:.1f} dB",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.comp_threshold_label.pack(side="right")
        
        self.comp_threshold_slider = ctk.CTkSlider(
            frame,
            from_=-40,
            to=0,
            number_of_steps=40,
            command=self.on_comp_threshold_change,
            progress_color=COLORS["accent"]
        )
        self.comp_threshold_slider.set(self.processor.compressor_threshold)
        self.comp_threshold_slider.pack(fill="x", padx=15, pady=(5, 10))
        
        # Ratio
        ratio_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ratio_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            ratio_frame,
            text="Ratio:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.comp_ratio_label = ctk.CTkLabel(
            ratio_frame,
            text=f"{self.processor.compressor_ratio:.1f}:1",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.comp_ratio_label.pack(side="right")
        
        self.comp_ratio_slider = ctk.CTkSlider(
            frame,
            from_=1,
            to=10,
            number_of_steps=90,
            command=self.on_comp_ratio_change,
            progress_color=COLORS["accent"]
        )
        self.comp_ratio_slider.set(self.processor.compressor_ratio)
        self.comp_ratio_slider.pack(fill="x", padx=15, pady=(5, 15))
        
        # Info
        info = ctk.CTkLabel(
            frame,
            text="Riduce i picchi per un volume più uniforme.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        info.pack(padx=15, pady=(0, 15))
    
    def create_eq_section(self, parent):
        """Sezione Equalizer"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=10)
        frame.pack(fill="x", pady=10, padx=5)
        
        title = ctk.CTkLabel(
            frame,
            text="🎵 Equalizer (3 bande)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        title.pack(padx=15, pady=(15, 10))
        
        # Low
        self.create_eq_band(frame, "Low (80Hz)", "eq_low")
        
        # Mid
        self.create_eq_band(frame, "Mid (1kHz)", "eq_mid")
        
        # High
        self.create_eq_band(frame, "High (8kHz)", "eq_high")
    
    def create_eq_band(self, parent, label, attr):
        """Crea controllo per una banda EQ"""
        band_frame = ctk.CTkFrame(parent, fg_color="transparent")
        band_frame.pack(fill="x", padx=15, pady=5)
        
        label_frame = ctk.CTkFrame(band_frame, fg_color="transparent")
        label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            label_frame,
            text=label,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        value = getattr(self.processor, attr)
        value_label = ctk.CTkLabel(
            label_frame,
            text=f"{value:+.1f} dB",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"]
        )
        value_label.pack(side="right")
        setattr(self, f"{attr}_label", value_label)
        
        slider = ctk.CTkSlider(
            parent,
            from_=-12,
            to=12,
            number_of_steps=48,
            command=lambda v, a=attr: self.on_eq_change(a, v),
            progress_color=COLORS["accent"]
        )
        slider.set(value)
        slider.pack(fill="x", padx=15, pady=(0, 10))
        setattr(self, f"{attr}_slider", slider)
    
    def toggle_gate(self):
        """Toggle noise gate"""
        self.processor.gate_enabled = self.gate_switch.get() == 1
        print(f"Gate {self.channel_id}: {'ON' if self.processor.gate_enabled else 'OFF'}")
        self.parent.save_config()
    
    def toggle_compressor(self):
        """Toggle compressor"""
        self.processor.comp_enabled = self.comp_switch.get() == 1
        print(f"Compressor {self.channel_id}: {'ON' if self.processor.comp_enabled else 'OFF'}")
        self.parent.save_config()
    
    def on_gate_threshold_change(self, value):
        """Cambia threshold del gate"""
        self.processor.gate_threshold = float(value)
        self.gate_threshold_label.configure(text=f"{value:.1f} dB")
    
    def on_comp_threshold_change(self, value):
        """Cambia threshold del compressor"""
        self.processor.compressor_threshold = float(value)
        self.comp_threshold_label.configure(text=f"{value:.1f} dB")
    
    def on_comp_ratio_change(self, value):
        """Cambia ratio del compressor"""
        self.processor.compressor_ratio = float(value)
        self.comp_ratio_label.configure(text=f"{value:.1f}:1")
    
    def on_eq_change(self, attr, value):
        """Cambia valore di una banda EQ"""
        setattr(self.processor, attr, float(value))
        label = getattr(self, f"{attr}_label")
        label.configure(text=f"{value:+.1f} dB")
    
    def update_gate_meter(self):
        """Aggiorna il meter del gate in tempo reale"""
        if not self.winfo_exists():
            return  # Finestra chiusa
            
        try:
            # Leggi envelope corrente (0.0 = chiuso, 1.0 = aperto)
            envelope = getattr(self.processor, 'vad_envelope', 1.0)
            envelope = max(0.0, min(1.0, float(envelope)))  # Clamp 0-1
            
            # Disegna meter su canvas
            width = self.gate_meter_canvas.winfo_width()
            if width > 1:  # Canvas renderizzato
                # Pulisci canvas
                self.gate_meter_canvas.delete("all")
                
                # Determina colore
                if envelope < 0.1:
                    color = COLORS["error"]  # Rosso - gate chiuso
                elif envelope < 0.5:
                    color = COLORS["warning"]  # Giallo - parzialmente aperto
                else:
                    color = COLORS["success"]  # Verde - completamente aperto
                
                # Disegna barra
                bar_width = int(width * envelope)
                self.gate_meter_canvas.create_rectangle(
                    0, 0, bar_width, 15,
                    fill=color,
                    outline=""
                )
                
                # Aggiorna label percentuale
                percentage = int(envelope * 100)
                self.gate_meter_label.configure(text=f"{percentage}%", text_color=color)
            
        except Exception as e:
            print(f"Gate meter error: {e}")
        
        # Aggiorna ogni 50ms per fluidità
        self.after(50, self.update_gate_meter)
    
    def reset_all(self):
        """Reset tutti gli effetti"""
        if messagebox.askyesno("Reset", "Resettare tutti gli effetti ai valori di default?"):
            # Gate
            self.processor.gate_enabled = False
            self.processor.gate_threshold = -40.0
            self.gate_switch.deselect()
            self.gate_threshold_slider.set(-40.0)
            self.gate_threshold_label.configure(text="-40.0 dB")
            
            # Compressor
            self.processor.comp_enabled = False
            self.processor.compressor_threshold = -20.0
            self.processor.compressor_ratio = 4.0
            self.comp_switch.deselect()
            self.comp_threshold_slider.set(-20.0)
            self.comp_threshold_label.configure(text="-20.0 dB")
            self.comp_ratio_slider.set(4.0)
            self.comp_ratio_label.configure(text="4.0:1")
            
            # EQ
            for attr in ['eq_low', 'eq_mid', 'eq_high']:
                setattr(self.processor, attr, 0.0)
                slider = getattr(self, f"{attr}_slider")
                label = getattr(self, f"{attr}_label")
                slider.set(0.0)
                label.configure(text="+0.0 dB")
            
            self.parent.save_config()
            messagebox.showinfo("Reset", "Effetti resettati!")
