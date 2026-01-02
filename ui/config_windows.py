"""
Finestre di configurazione per mixer e dispositivi audio
"""
import customtkinter as ctk
from tkinter import messagebox
import json

from .colors import COLORS


class MixerConfigWindow(ctk.CTkToplevel):
    """Finestra configurazione dispositivi mixer"""
    
    def __init__(self, parent, pro_mixer, channel_strips, bus_strips):
        super().__init__(parent)
        
        self.pro_mixer = pro_mixer
        self.parent = parent
        self.channel_strips = channel_strips
        self.bus_strips = bus_strips
        
        self.title("⚙️ Configurazione Mixer")
        self.geometry("900x700")
        self.configure(fg_color=COLORS["bg_primary"])
        
        # Imposta finestra sempre in primo piano
        self.attributes('-topmost', True)
        self.lift()
        self.focus_force()
        
        # Get devices
        self.devices = pro_mixer.get_available_devices()
        
        # Dizionari per salvare i dropdown
        self.input_dropdowns = {}
        self.output_dropdowns = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Crea UI configurazione"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Configurazione Routing Audio",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["accent"]
        )
        title.pack(pady=20)
        
        # Scroll frame
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_secondary"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Hardware Inputs
        hw_label = ctk.CTkLabel(
            scroll,
            text="🎤 HARDWARE INPUTS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        hw_label.pack(pady=(10, 5), anchor="w", padx=20)
        
        # Solo HW1 e HW2 configurabili (HW3 è riservato al Media Player)
        for i in range(1, 3):
            self.create_input_config(scroll, f"HW{i}", f"Hardware {i}")
        
        # Info HW3
        hw3_info = ctk.CTkLabel(
            scroll,
            text="🎵 HW3: Riservato al Media Player (non configurabile)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        hw3_info.pack(pady=(5, 0), anchor="w", padx=20)
        
        # Virtual Inputs
        virt_label = ctk.CTkLabel(
            scroll,
            text="🔌 VIRTUAL INPUTS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        )
        virt_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        for i in range(1, 3):
            self.create_input_config(scroll, f"VIRT{i}", f"Virtual {i}")
        
        # Output Buses
        bus_label = ctk.CTkLabel(
            scroll,
            text="🔊 OUTPUT BUSES",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        )
        bus_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        for bus_name in ['A1', 'A2', 'A3', 'B1', 'B2']:
            self.create_output_config(scroll, bus_name)
        
        # Close button
        close_btn = ctk.CTkButton(
            self,
            text="✓ Chiudi",
            width=200,
            height=40,
            command=self.destroy,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        close_btn.pack(pady=20)
    
    def create_input_config(self, parent, channel_id, label):
        """Crea configurazione per input"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=8)
        frame.pack(fill="x", pady=5, padx=20)
        
        label_widget = ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
            width=120,
            anchor="w"
        )
        label_widget.pack(side="left", padx=15, pady=12)
        
        # Device dropdown
        input_devices = [f"[{d.id}] {d.name}" for d in self.devices if d.input_channels > 0]
        
        dropdown = ctk.CTkOptionMenu(
            frame,
            values=["None"] + input_devices,
            width=550,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            command=lambda val, ch=channel_id: self.assign_input(ch, val)
        )
        dropdown.pack(side="right", padx=15, pady=12)
        
        # Salva riferimento al dropdown
        if not hasattr(self, 'input_dropdowns'):
            self.input_dropdowns = {}
        self.input_dropdowns[channel_id] = dropdown
        
        # Imposta valore iniziale se il canale ha già un device configurato
        if channel_id in self.pro_mixer.input_device_map:
            device_id = self.pro_mixer.input_device_map[channel_id]
            # Trova il device nella lista
            for device in self.devices:
                if device.id == device_id and device.input_channels > 0:
                    device_str = f"[{device.id}] {device.name}"
                    dropdown.set(device_str)
                    print(f"✓ Canale {channel_id} preconfigurato: Device {device_id} ({device.name})")
                    break
    
    def create_output_config(self, parent, bus_name):
        """Crea configurazione per output bus"""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["accent"])
        frame.pack(fill="x", pady=5, padx=20)
        
        label_widget = ctk.CTkLabel(
            frame,
            text=f"Bus {bus_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"],
            width=120,
            anchor="w"
        )
        label_widget.pack(side="left", padx=15, pady=12)
        
        # Device dropdown
        output_devices = [f"[{d.id}] {d.name}" for d in self.devices if d.output_channels > 0]
        
        dropdown = ctk.CTkOptionMenu(
            frame,
            values=["None"] + output_devices,
            width=550,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            command=lambda val, b=bus_name: self.assign_output(b, val)
        )
        dropdown.pack(side="right", padx=15, pady=12)
        
        # Salva riferimento al dropdown
        self.output_dropdowns[bus_name] = dropdown
        
        # Imposta valore iniziale se il bus ha già un device configurato
        bus = self.pro_mixer.buses.get(bus_name)
        if bus and bus.device_id is not None:
            # Trova il device nella lista
            for device in self.devices:
                if device.id == bus.device_id and device.output_channels > 0:
                    device_str = f"[{device.id}] {device.name}"
                    dropdown.set(device_str)
                    print(f"✓ Bus {bus_name} preconfigurato: Device {bus.device_id} ({device.name})")
                    break
    
    def assign_input(self, channel_id, device_str):
        """Assegna device a input"""
        if device_str == "None":
            print(f"⚠ Rimozione dispositivo da {channel_id}")
            # TODO: Implementare rimozione device
            return
        
        try:
            # Estrai ID
            device_id = int(device_str.split("]")[0].replace("[", ""))
            print(f"🎤 Configurazione {channel_id} con device {device_id}...")
            
            # Avvia input
            success = self.pro_mixer.start_input(channel_id, device_id)
            
            if success:
                print(f"   ✓ Input {channel_id} avviato con successo")
                
                # Aggiorna UI dei routing buttons se esistono
                if hasattr(self.parent, 'mixer_channel_strips') and channel_id in self.parent.mixer_channel_strips:
                    strip = self.parent.mixer_channel_strips[channel_id]
                    if hasattr(strip, 'routing_buttons'):
                        channel = self.pro_mixer.channels[channel_id]
                        for bus_name, btn in strip.routing_buttons.items():
                            is_active = channel.routing.get(bus_name, False)
                            from .colors import COLORS
                            btn.configure(fg_color=COLORS["accent"] if is_active else COLORS["bg_card"])
                
                # Aggiorna fader UI se esiste
                if hasattr(self.parent, 'mixer_channel_strips') and channel_id in self.parent.mixer_channel_strips:
                    strip = self.parent.mixer_channel_strips[channel_id]
                    if hasattr(strip, 'fader'):
                        strip.fader.set(12.0)  # +12 dB per microfono
                    if hasattr(strip, 'db_label'):
                        strip.db_label.configure(text="+12.0 dB")
                    # Aggiorna nome canale con nome device
                    if hasattr(strip, 'name_label'):
                        channel = self.pro_mixer.channels[channel_id]
                        strip.name_label.configure(text=channel.name)
                        print(f"   ✓ Nome UI aggiornato: {channel.name}")
                
                # Salva configurazione
                self.parent.save_config()
                print(f"   ✓ Configurazione salvata")
                
                # Messaggio di conferma
                msg = f"{channel_id} collegato al dispositivo {device_id}\n\n"
                msg += "✓ Routing automatico attivato verso A1 (Output principale)\n"
                msg += "✓ Fader impostato a +12 dB (puoi abbassarlo se necessario)\n\n"
                msg += "IMPORTANTE: La configurazione è stata salvata automaticamente."
                messagebox.showinfo("✓ Configurato", msg)
            else:
                print(f"   ✗ Errore avvio input {channel_id}")
                messagebox.showerror("✗ Errore", f"Impossibile avviare input su {channel_id}\nVerifica che il dispositivo sia disponibile.")
        except Exception as e:
            print(f"   ✗ Eccezione durante configurazione: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Errore", f"Errore durante la configurazione:\n{str(e)}")
    
    def assign_output(self, bus_name, device_str):
        """Assegna device a bus"""
        if device_str == "None":
            return
        
        try:
            # Estrai ID
            device_id = int(device_str.split("]")[0].replace("[", ""))
            
            # Assegna
            self.pro_mixer.set_bus_device(bus_name, device_id)
            
            # Aggiorna label nella UI
            if bus_name in self.bus_strips:
                strip = self.bus_strips[bus_name]
                device = next((d for d in self.devices if d.id == device_id), None)
                if device:
                    strip.device_label.configure(text=device.name[:25])
            
            # SINCRONIZZAZIONE CON SOUNDBOARD
            # Se si configura A1 o A2, aggiorna anche la soundboard
            if bus_name == 'A1':
                print(f"🔄 Sincronizzazione Bus A1 → Soundboard Primary Output")
                self.parent.mixer.output_device = device_id
                # Salva nel config
                config = self.parent.config_manager.load_config_dict()
                config['audio_output_device'] = device_id
                with open(self.parent.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                print(f"   ✓ Primary Output aggiornato a device {device_id}")
            
            elif bus_name == 'A2':
                print(f"🔄 Sincronizzazione Bus A2 → Soundboard Secondary Output")
                self.parent.mixer.secondary_output_device = device_id
                # Salva nel config
                config = self.parent.config_manager.load_config_dict()
                config['secondary_output_device'] = device_id
                with open(self.parent.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                print(f"   ✓ Secondary Output aggiornato a device {device_id}")
            
            # Salva configurazione
            self.parent.save_config()
            
            msg = f"Bus {bus_name} → Device {device_id}\n\nRicorda di avviare il mixer!"
            if bus_name in ['A1', 'A2']:
                msg += f"\n\n🎯 Soundboard sincronizzata automaticamente!"
            
            messagebox.showinfo("✓ Configurato", msg)
        except Exception as e:
            messagebox.showerror("Errore", str(e))
