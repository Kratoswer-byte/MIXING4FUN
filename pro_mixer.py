"""
ProMixer - Interfaccia Grafica Mixer Professionale
Sostituto completo di Voicemeeter
"""
import customtkinter as ctk
from tkinter import messagebox
import threading
import json
import os
from mixer_engine import ProMixer, MixerChannel, OutputBus
from typing import Dict


# Colori tema professionale
COLORS = {
    "bg_dark": "#0a0a0a",
    "bg_panel": "#1a1a1a",
    "bg_card": "#252525",
    "bg_fader": "#1e1e1e",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "text": "#e5e5e5",
    "text_dim": "#8a8a8a",
    "border": "#333333",
    "meter_green": "#10b981",
    "meter_yellow": "#f59e0b",
    "meter_red": "#ef4444",
    "mute": "#dc2626",
    "solo": "#eab308",
}


class VUMeter(ctk.CTkCanvas):
    """VU Meter verticale professionale"""
    
    def __init__(self, parent, width=30, height=200):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS["bg_fader"],
            highlightthickness=0
        )
        self.width = width
        self.height = height
        self.level = -60  # dB
        self.peak_hold = -60
        self.peak_hold_time = 0
        
        self.draw()
    
    def draw(self):
        """Disegna il meter"""
        self.delete("all")
        
        # Background
        self.create_rectangle(0, 0, self.width, self.height, fill=COLORS["bg_fader"], outline=COLORS["border"])
        
        # Calcola altezza barra
        db_range = 60  # -60dB a 0dB
        if self.level > -60:
            normalized = (self.level + 60) / db_range
            bar_height = int(self.height * normalized)
            
            # Disegna barra con colori graduali
            segments = 20
            seg_height = bar_height / segments
            
            for i in range(segments):
                y_start = self.height - (i * seg_height)
                y_end = self.height - ((i + 1) * seg_height)
                
                # Colore in base al livello
                level_percent = (i / segments)
                if level_percent < 0.7:
                    color = COLORS["meter_green"]
                elif level_percent < 0.9:
                    color = COLORS["meter_yellow"]
                else:
                    color = COLORS["meter_red"]
                
                self.create_rectangle(
                    2, y_start, self.width - 2, y_end,
                    fill=color, outline=""
                )
        
        # Peak hold
        if self.peak_hold > -60:
            normalized = (self.peak_hold + 60) / db_range
            peak_y = self.height - int(self.height * normalized)
            self.create_line(
                0, peak_y, self.width, peak_y,
                fill=COLORS["meter_red"], width=2
            )
    
    def update_level(self, db: float):
        """Aggiorna livello (-60 a +12 dB)"""
        self.level = max(-60, min(12, db))
        
        # Peak hold
        if self.level > self.peak_hold:
            self.peak_hold = self.level
            self.peak_hold_time = 30  # frames
        else:
            self.peak_hold_time -= 1
            if self.peak_hold_time <= 0:
                self.peak_hold -= 0.5  # Decade lentamente
        
        self.draw()


class FaderControl(ctk.CTkFrame):
    """Fader verticale con label dB"""
    
    def __init__(self, parent, label: str, on_change=None):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8)
        
        self.on_change = on_change
        self.value_db = 0.0
        
        # Label
        self.label_widget = ctk.CTkLabel(
            self,
            text=label,
            text_color=COLORS["text"],
            font=("Arial", 10, "bold")
        )
        self.label_widget.pack(pady=(5, 0))
        
        # dB value
        self.db_label = ctk.CTkLabel(
            self,
            text="0.0 dB",
            text_color=COLORS["text_dim"],
            font=("Arial", 9)
        )
        self.db_label.pack()
        
        # Slider verticale
        self.slider = ctk.CTkSlider(
            self,
            from_=12,
            to=-60,
            orientation="vertical",
            height=200,
            command=self._on_slider_change,
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent"]
        )
        self.slider.set(0)
        self.slider.pack(pady=10, padx=15)
    
    def _on_slider_change(self, value):
        """Callback slider"""
        self.value_db = float(value)
        self.db_label.configure(text=f"{self.value_db:.1f} dB")
        
        if self.on_change:
            self.on_change(self.value_db)
    
    def set_value(self, db: float):
        """Imposta valore programmaticamente"""
        self.slider.set(db)
        self._on_slider_change(db)
    
    def get_value(self) -> float:
        """Ottieni valore in dB"""
        return self.value_db


class ChannelStrip(ctk.CTkFrame):
    """Strip completo di un canale mixer"""
    
    def __init__(self, parent, channel_id: str, channel: MixerChannel, mixer: ProMixer):
        super().__init__(parent, fg_color=COLORS["bg_panel"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        
        self.channel_id = channel_id
        self.channel = channel
        self.mixer = mixer
        
        # Nome canale
        name_label = ctk.CTkLabel(
            self,
            text=channel.name,
            text_color=COLORS["text"],
            font=("Arial", 12, "bold")
        )
        name_label.pack(pady=(10, 5))
        
        # VU Meter
        self.vu_meter = VUMeter(self, width=25, height=150)
        self.vu_meter.pack(pady=5)
        
        # Fader
        self.fader = FaderControl(
            self,
            "Volume",
            on_change=lambda db: self.channel.set_fader_db(db)
        )
        self.fader.pack(pady=5, padx=10)
        
        # Routing buttons frame
        routing_frame = ctk.CTkFrame(self, fg_color="transparent")
        routing_frame.pack(pady=10)
        
        ctk.CTkLabel(
            routing_frame,
            text="Routing:",
            text_color=COLORS["text_dim"],
            font=("Arial", 9)
        ).pack()
        
        # Bus routing buttons
        self.routing_buttons = {}
        bus_frame = ctk.CTkFrame(routing_frame, fg_color="transparent")
        bus_frame.pack()
        
        for i, bus_name in enumerate(['A1', 'A2', 'A3', 'B1', 'B2']):
            btn = ctk.CTkButton(
                bus_frame,
                text=bus_name,
                width=40,
                height=25,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["accent_hover"],
                command=lambda b=bus_name: self.toggle_routing(b)
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
            self.routing_buttons[bus_name] = btn
        
        # Mute/Solo
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(pady=5)
        
        self.mute_btn = ctk.CTkButton(
            control_frame,
            text="M",
            width=40,
            height=30,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["mute"],
            command=self.toggle_mute
        )
        self.mute_btn.grid(row=0, column=0, padx=2)
        
        self.solo_btn = ctk.CTkButton(
            control_frame,
            text="S",
            width=40,
            height=30,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["solo"],
            command=self.toggle_solo
        )
        self.solo_btn.grid(row=0, column=1, padx=2)
    
    def toggle_routing(self, bus_name: str):
        """Toggle routing verso un bus"""
        current = self.channel.routing.get(bus_name, False)
        new_state = not current
        
        self.mixer.set_channel_routing(self.channel_id, bus_name, new_state)
        
        # Aggiorna colore bottone
        btn = self.routing_buttons[bus_name]
        if new_state:
            btn.configure(fg_color=COLORS["accent"])
        else:
            btn.configure(fg_color=COLORS["bg_card"])
    
    def toggle_mute(self):
        """Toggle mute"""
        self.channel.mute = not self.channel.mute
        
        if self.channel.mute:
            self.mute_btn.configure(fg_color=COLORS["mute"])
        else:
            self.mute_btn.configure(fg_color=COLORS["bg_card"])
    
    def toggle_solo(self):
        """Toggle solo"""
        self.channel.solo = not self.channel.solo
        
        if self.channel.solo:
            self.solo_btn.configure(fg_color=COLORS["solo"])
        else:
            self.solo_btn.configure(fg_color=COLORS["bg_card"])
    
    def update_meter(self):
        """Aggiorna VU meter"""
        self.vu_meter.update_level(self.channel.peak_level)


class BusStrip(ctk.CTkFrame):
    """Strip di un bus output"""
    
    def __init__(self, parent, bus_name: str, bus: OutputBus):
        super().__init__(parent, fg_color=COLORS["bg_panel"], corner_radius=12, border_width=2, border_color=COLORS["accent"])
        
        self.bus_name = bus_name
        self.bus = bus
        
        # Nome
        name_label = ctk.CTkLabel(
            self,
            text=f"BUS {bus_name}",
            text_color=COLORS["accent"],
            font=("Arial", 13, "bold")
        )
        name_label.pack(pady=(10, 5))
        
        # Device label
        self.device_label = ctk.CTkLabel(
            self,
            text="No Device",
            text_color=COLORS["text_dim"],
            font=("Arial", 8),
            wraplength=120
        )
        self.device_label.pack()
        
        # VU Meter
        self.vu_meter = VUMeter(self, width=30, height=150)
        self.vu_meter.pack(pady=5)
        
        # Master fader
        self.fader = FaderControl(
            self,
            "Master",
            on_change=lambda db: self.bus.set_fader_db(db)
        )
        self.fader.pack(pady=5, padx=10)
        
        # Mute
        self.mute_btn = ctk.CTkButton(
            self,
            text="MUTE",
            width=80,
            height=35,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["mute"],
            command=self.toggle_mute
        )
        self.mute_btn.pack(pady=10)
    
    def set_device_name(self, name: str):
        """Imposta nome dispositivo"""
        self.device_label.configure(text=name)
    
    def toggle_mute(self):
        """Toggle mute"""
        self.bus.mute = not self.bus.mute
        
        if self.bus.mute:
            self.mute_btn.configure(fg_color=COLORS["mute"], text="MUTED")
        else:
            self.mute_btn.configure(fg_color=COLORS["bg_card"], text="MUTE")
    
    def update_meter(self):
        """Aggiorna VU meter"""
        self.vu_meter.update_level(self.bus.peak_level)


class ProMixerGUI(ctk.CTk):
    """Interfaccia grafica principale"""
    
    def __init__(self):
        super().__init__()
        
        self.title("ProMixer - Professional Audio Mixer")
        self.geometry("1400x700")
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Mixer engine
        self.mixer = ProMixer(sample_rate=44100, buffer_size=512)
        self.mixer.metering_callback = self.update_all_meters
        
        # UI Components
        self.channel_strips: Dict[str, ChannelStrip] = {}
        self.bus_strips: Dict[str, BusStrip] = {}
        
        self.setup_ui()
        
        # Metering update loop
        self.is_running = True
        self.meter_thread = threading.Thread(target=self.meter_update_loop, daemon=True)
        self.meter_thread.start()
    
    def setup_ui(self):
        """Crea interfaccia"""
        # Top bar
        top_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], height=60)
        top_frame.pack(fill="x", padx=10, pady=10)
        top_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            top_frame,
            text="🎛️ PROMIXER",
            text_color=COLORS["accent"],
            font=("Arial", 24, "bold")
        )
        title_label.pack(side="left", padx=20)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ START",
            width=100,
            height=40,
            fg_color=COLORS["meter_green"],
            hover_color="#059669",
            command=self.start_mixer
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ STOP",
            width=100,
            height=40,
            fg_color=COLORS["mute"],
            hover_color="#b91c1c",
            command=self.stop_mixer,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        config_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ CONFIG",
            width=100,
            height=40,
            command=self.open_config
        )
        config_btn.pack(side="left", padx=5)
        
        # Main mixer area
        mixer_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            orientation="horizontal"
        )
        mixer_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Channels section
        channels_frame = ctk.CTkFrame(mixer_frame, fg_color="transparent")
        channels_frame.pack(side="left", fill="y", padx=5)
        
        ctk.CTkLabel(
            channels_frame,
            text="INPUT CHANNELS",
            text_color=COLORS["text"],
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        channels_container = ctk.CTkFrame(channels_frame, fg_color="transparent")
        channels_container.pack(fill="both", expand=True)
        
        # Crea channel strips
        for i, (ch_id, channel) in enumerate(self.mixer.channels.items()):
            strip = ChannelStrip(channels_container, ch_id, channel, self.mixer)
            strip.grid(row=0, column=i, padx=5, pady=5, sticky="ns")
            self.channel_strips[ch_id] = strip
        
        # Separator
        sep = ctk.CTkFrame(mixer_frame, width=2, fg_color=COLORS["border"])
        sep.pack(side="left", fill="y", padx=20)
        
        # Buses section
        buses_frame = ctk.CTkFrame(mixer_frame, fg_color="transparent")
        buses_frame.pack(side="left", fill="y", padx=5)
        
        ctk.CTkLabel(
            buses_frame,
            text="OUTPUT BUSES",
            text_color=COLORS["accent"],
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        buses_container = ctk.CTkFrame(buses_frame, fg_color="transparent")
        buses_container.pack(fill="both", expand=True)
        
        # Crea bus strips
        for i, (bus_name, bus) in enumerate(self.mixer.buses.items()):
            strip = BusStrip(buses_container, bus_name, bus)
            strip.grid(row=0, column=i, padx=5, pady=5, sticky="ns")
            self.bus_strips[bus_name] = strip
    
    def open_config(self):
        """Apre finestra di configurazione"""
        ConfigWindow(self, self.mixer)
    
    def start_mixer(self):
        """Avvia il mixer"""
        try:
            self.mixer.start_all()
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            messagebox.showinfo("ProMixer", "Mixer avviato con successo!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare mixer:\n{e}")
    
    def stop_mixer(self):
        """Ferma il mixer"""
        self.mixer.stop_all()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
    
    def update_all_meters(self):
        """Aggiorna tutti i VU meters"""
        pass  # Chiamato dal meter_update_loop
    
    def meter_update_loop(self):
        """Loop aggiornamento meters"""
        import time
        while self.is_running:
            try:
                # Aggiorna channel meters
                for strip in self.channel_strips.values():
                    strip.update_meter()
                
                # Aggiorna bus meters
                for strip in self.bus_strips.values():
                    strip.update_meter()
                
                time.sleep(0.05)  # 20 FPS
            except:
                pass
    
    def on_closing(self):
        """Chiusura applicazione"""
        self.is_running = False
        self.mixer.stop_all()
        self.destroy()


class ConfigWindow(ctk.CTkToplevel):
    """Finestra configurazione dispositivi"""
    
    def __init__(self, parent, mixer: ProMixer):
        super().__init__(parent)
        
        self.mixer = mixer
        self.title("Configurazione Dispositivi")
        self.geometry("800x600")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Devices
        self.devices = mixer.get_available_devices()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Crea UI configurazione"""
        # Title
        ctk.CTkLabel(
            self,
            text="⚙️ Configurazione Routing Audio",
            font=("Arial", 20, "bold"),
            text_color=COLORS["accent"]
        ).pack(pady=20)
        
        # Scroll frame
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_panel"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Hardware Inputs
        ctk.CTkLabel(
            scroll,
            text="🎤 HARDWARE INPUTS",
            font=("Arial", 14, "bold")
        ).pack(pady=10, anchor="w")
        
        for i in range(1, 4):
            self.create_input_config(scroll, f"HW{i}", f"Hardware {i}")
        
        # Virtual Inputs  
        ctk.CTkLabel(
            scroll,
            text="🔌 VIRTUAL INPUTS",
            font=("Arial", 14, "bold")
        ).pack(pady=10, anchor="w")
        
        for i in range(1, 3):
            self.create_input_config(scroll, f"VIRT{i}", f"Virtual {i}")
        
        # Output Buses
        ctk.CTkLabel(
            scroll,
            text="🔊 OUTPUT BUSES",
            font=("Arial", 14, "bold")
        ).pack(pady=10, anchor="w")
        
        for bus_name in ['A1', 'A2', 'A3', 'B1', 'B2']:
            self.create_output_config(scroll, bus_name)
        
        # Close button
        ctk.CTkButton(
            self,
            text="Chiudi",
            command=self.destroy
        ).pack(pady=10)
    
    def create_input_config(self, parent, channel_id: str, label: str):
        """Crea config per input"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"])
        frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)
        
        # Device dropdown
        input_devices = [f"[{d.id}] {d.name}" for d in self.devices if d.input_channels > 0]
        
        dropdown = ctk.CTkOptionMenu(
            frame,
            values=["None"] + input_devices,
            width=400,
            command=lambda val: self.assign_input(channel_id, val)
        )
        dropdown.pack(side="right", padx=10, pady=10)
    
    def create_output_config(self, parent, bus_name: str):
        """Crea config per output bus"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"])
        frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(
            frame,
            text=f"Bus {bus_name}",
            font=("Arial", 12, "bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=10)
        
        # Device dropdown
        output_devices = [f"[{d.id}] {d.name}" for d in self.devices if d.output_channels > 0]
        
        dropdown = ctk.CTkOptionMenu(
            frame,
            values=["None"] + output_devices,
            width=400,
            command=lambda val: self.assign_output(bus_name, val)
        )
        dropdown.pack(side="right", padx=10, pady=10)
    
    def assign_input(self, channel_id: str, device_str: str):
        """Assegna device a input"""
        if device_str == "None":
            return
        
        # Estrai ID
        device_id = int(device_str.split("]")[0].replace("[", ""))
        
        # Avvia input
        success = self.mixer.start_input(channel_id, device_id)
        
        if success:
            messagebox.showinfo("OK", f"{channel_id} → Device {device_id}")
        else:
            messagebox.showerror("Errore", "Impossibile avviare input")
    
    def assign_output(self, bus_name: str, device_str: str):
        """Assegna device a bus"""
        if device_str == "None":
            return
        
        # Estrai ID
        device_id = int(device_str.split("]")[0].replace("[", ""))
        
        # Assegna
        self.mixer.set_bus_device(bus_name, device_id)
        
        # Aggiorna label nella UI principale
        if hasattr(self.master, 'bus_strips'):
            strip = self.master.bus_strips.get(bus_name)
            if strip:
                device = next((d for d in self.devices if d.id == device_id), None)
                if device:
                    strip.set_device_name(device.name)
        
        messagebox.showinfo("OK", f"Bus {bus_name} → Device {device_id}")


# Main
if __name__ == "__main__":
    app = ProMixerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
