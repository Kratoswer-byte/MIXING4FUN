"""
Audio Mixer - Interfaccia Grafica Moderna con Hotkeys per Gaming
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import os
import sys
import logging
from audio_engine import AudioMixer, AudioClip
from youtube_downloader import YouTubeDownloader
from mixer_engine import ProMixer, MixerChannel, OutputBus
from threading import Thread
from typing import Dict, Optional
import numpy as np
import keyboard
import json
import sounddevice as sd
from functools import partial
from PIL import Image, ImageDraw
try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Configura logging
if getattr(sys, 'frozen', False):
    # Se è un exe, log nella stessa cartella
    log_file = os.path.join(os.path.dirname(sys.executable), "soundboard.log")
else:
    # Se è script, log nella cartella corrente
    log_file = os.path.join(os.path.dirname(__file__), "soundboard.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Tema e colori moderni (palette più morbida)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg_primary": "#0d1117",      # Nero più morbido
    "bg_secondary": "#161b22",    # Grigio scuro
    "bg_card": "#1f2937",         # Card background
    "accent": "#3b82f6",          # Blu moderno
    "accent_hover": "#2563eb",    # Blu hover
    "text": "#f3f4f6",            # Testo chiaro
    "text_muted": "#9ca3af",      # Testo secondario
    "text_secondary": "#6b7280",  # Testo terziario
    "success": "#10b981",         # Verde
    "warning": "#f59e0b",         # Arancione
    "danger": "#ef4444",          # Rosso
    "error": "#dc2626",           # Rosso errore
    "border": "#374151"           # Bordi
}


class ClipButton(ctk.CTkFrame):
    """Widget personalizzato per una clip audio (compatto ed espandibile)"""
    
    def __init__(self, parent, clip_name: str, on_play, on_stop, on_remove, on_volume_change, on_hotkey_change, app=None):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        
        self.clip_name = clip_name
        self.on_play = on_play
        self.on_stop = on_stop
        self.on_remove = on_remove
        self.on_volume_change = on_volume_change
        self.on_hotkey_change = on_hotkey_change
        self.app = app  # Riferimento diretto all'app principale
        self.is_playing = False
        self.hotkey = None
        self.is_expanded = False
        self._is_destroyed = False  # Flag per prevenire aggiornamenti dopo destroy
        
        self.grid_columnconfigure(0, weight=1)
        
        # Menu contestuale per cambio pagina rapido
        self.context_menu = None
        
        # ===== VERSIONE COMPATTA (sempre visibile) =====
        compact_frame = ctk.CTkFrame(self, fg_color="transparent")
        compact_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        compact_frame.grid_columnconfigure(1, weight=1)
        
        # Bind tasto destro per menu contestuale
        self.bind("<Button-3>", self.show_context_menu)
        compact_frame.bind("<Button-3>", self.show_context_menu)
        
        # Pulsante Play/Stop (piccolo)
        self.play_button = ctk.CTkButton(
            compact_frame,
            text="▶",
            width=40,
            height=40,
            command=self.toggle_play,
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            corner_radius=10
        )
        self.play_button.grid(row=0, column=0, padx=(0, 10))
        self.play_button.bind("<Button-3>", self.show_context_menu)
        
        # Info clip (nome + hotkey)
        info_frame = ctk.CTkFrame(compact_frame, fg_color="transparent")
        info_frame.bind("<Button-3>", self.show_context_menu)
        info_frame.grid(row=0, column=1, sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        self.name_label = ctk.CTkLabel(
            info_frame, 
            text=clip_name[:30] + "..." if len(clip_name) > 30 else clip_name,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text"],
            anchor="w"
        )
        self.name_label.grid(row=0, column=0, sticky="w")
        self.name_label.bind("<Button-3>", self.show_context_menu)
        
        self.hotkey_label = ctk.CTkLabel(
            info_frame,
            text="No hotkey",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"],
            anchor="w"
        )
        self.hotkey_label.grid(row=1, column=0, sticky="w")
        self.hotkey_label.bind("<Button-3>", self.show_context_menu)
        
        # Pulsante Espandi/Comprimi
        self.expand_button = ctk.CTkButton(
            compact_frame,
            text="▼",
            width=40,
            height=40,
            command=self.toggle_expand,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            corner_radius=10
        )
        self.expand_button.grid(row=0, column=2, padx=(10, 0))
        self.expand_button.bind("<Button-3>", self.show_context_menu)
        
        # ===== VERSIONE ESPANSA (nascosta di default) =====
        self.expanded_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.expanded_frame.grid_columnconfigure(0, weight=1)
        
        # Volume slider
        vol_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        vol_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(5, 5))
        vol_frame.grid_columnconfigure(1, weight=1)
        
        self.volume_label = ctk.CTkLabel(
            vol_frame,
            text="🔊 Volume: 100%",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text"]
        )
        self.volume_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.volume_slider = ctk.CTkSlider(
            vol_frame,
            from_=0,
            to=100,
            command=self.on_volume_changed,
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent"],
            height=16
        )
        self.volume_slider.set(100)
        self.volume_slider.grid(row=0, column=1, sticky="ew")
        
        # Hotkey assignment
        hotkey_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        hotkey_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 5))
        
        ctk.CTkLabel(
            hotkey_frame,
            text="⌨️ Hotkey:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.hotkey_button = ctk.CTkButton(
            hotkey_frame,
            text="Assegna tasto",
            height=28,
            command=self.assign_hotkey,
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=8
        )
        self.hotkey_button.grid(row=0, column=1, sticky="w")
        
        # Selettore pagina
        page_frame = ctk.CTkFrame(self.expanded_frame, fg_color="transparent")
        page_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 5))
        
        ctk.CTkLabel(
            page_frame,
            text="📑 Pagina:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.page_selector = ctk.CTkOptionMenu(
            page_frame,
            values=["F1", "F2", "F3", "F4", "F5"],
            height=28,
            command=self.on_page_changed,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.page_selector.set("F1")
        self.page_selector.grid(row=0, column=1, sticky="w")
        
        # Pulsante Rimuovi
        self.remove_button = ctk.CTkButton(
            self.expanded_frame,
            text="🗑️ Rimuovi clip",
            height=32,
            command=self.confirm_remove,
            fg_color=COLORS["danger"],
            hover_color="#b91c1c",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8
        )
        self.remove_button.grid(row=2, column=0, sticky="ew", padx=8, pady=(5, 8))
    
    def toggle_expand(self):
        """Espandi/Comprimi pannello controlli"""
        if self._is_destroyed:
            return
        try:
            if self.is_expanded:
                # Comprimi
                self.expanded_frame.grid_forget()
                self.expand_button.configure(text="▼")
                self.is_expanded = False
            else:
                # Espandi
                self.expanded_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
                self.expand_button.configure(text="▲")
                self.is_expanded = True
        except Exception:
            pass  # Widget già distrutto, ignora l'errore
    
    def toggle_play(self):
        """Toggle play/stop"""
        if self._is_destroyed:
            return
        if self.is_playing:
            self.stop()
        else:
            self.play()
    
    def play(self):
        """Avvia la riproduzione"""
        if self._is_destroyed:
            return
        
        # Verifica che la clip sia nella pagina corrente
        if self.app:
            try:
                clip_page = self.app.clip_pages.get(self.clip_name, 1)
                current_page = self.app.current_page
                if clip_page != current_page:
                    logger.warning(f"Impossibile riprodurre clip '{self.clip_name}': non nella pagina corrente")
                    return
            except Exception as e:
                logger.error(f"Errore verifica pagina: {e}")
        
        self.is_playing = True
        try:
            self.play_button.configure(text="⏸", fg_color=COLORS["warning"], hover_color="#d97706")
        except Exception:
            pass
        self.on_play(self.clip_name)
    
    def stop(self):
        """Ferma la riproduzione"""
        if self._is_destroyed:
            return
        self.is_playing = False
        try:
            self.play_button.configure(text="▶", fg_color=COLORS["success"], hover_color="#059669")
        except Exception:
            pass
        self.on_stop(self.clip_name)
    
    def on_volume_changed(self, value):
        """Callback per cambio volume"""
        if self._is_destroyed:
            return
        volume_pct = int(value)
        try:
            self.volume_label.configure(text=f"🔊 Volume: {volume_pct}%")
        except Exception:
            pass
        self.on_volume_change(self.clip_name, value / 100.0)
    
    def on_page_changed(self, page_str):
        """Callback quando cambia la pagina della clip"""
        page_num = int(page_str[1])  # "F1" -> 1
        # Notifica il parent (SoundboardApp) del cambio pagina
        if self.app:
            self.app.clip_pages[self.clip_name] = page_num
            self.app.save_config()
            self.app.update_clips_visibility()
            logger.info(f"Clip '{self.clip_name}' spostata su pagina {page_num}")
    
    def set_page(self, page_num):
        """Imposta la pagina corrente della clip"""
        self.page_selector.set(f"F{page_num}")
    
    def show_context_menu(self, event):
        """Mostra menu contestuale per spostare clip tra pagine"""
        try:
            import tkinter as tk
            if self.context_menu:
                self.context_menu.destroy()
            
            self.context_menu = tk.Menu(self, tearoff=0, bg=COLORS["bg_secondary"], fg=COLORS["text"],
                                        activebackground=COLORS["accent"], activeforeground="white",
                                        font=("Segoe UI", 10))
            
            # Ottieni pagina corrente
            current_page = self.master.master.master.master.master.clip_pages.get(self.clip_name, 1)
            
            self.context_menu.add_command(label="📑 Sposta in pagina:", state="disabled")
            self.context_menu.add_separator()
            
            for page_num in range(1, 6):
                label = f"  F{page_num} (Pagina {page_num})"
                if page_num == current_page:
                    label += " ✓"
                self.context_menu.add_command(
                    label=label,
                    command=lambda p=page_num: self.move_to_page(p)
                )
            
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Errore nel menu contestuale: {e}")
        finally:
            if self.context_menu:
                self.context_menu.grab_release()
    
    def move_to_page(self, page_num):
        """Sposta la clip in una pagina specifica"""
        self.page_selector.set(f"F{page_num}")
        self.on_page_changed(f"F{page_num}")
    
    def show_context_menu(self, event):
        """Mostra menu contestuale per spostare clip tra pagine"""
        if not self.app:
            return
        
        try:
            import tkinter as tk
            if self.context_menu:
                self.context_menu.destroy()
            
            self.context_menu = tk.Menu(self, tearoff=0, bg=COLORS["bg_secondary"], fg=COLORS["text"],
                                        activebackground=COLORS["accent"], activeforeground="white",
                                        font=("Segoe UI", 10))
            
            # Ottieni pagina corrente
            current_page = self.app.clip_pages.get(self.clip_name, 1)
            
            self.context_menu.add_command(label="📑 Sposta in pagina:", state="disabled")
            self.context_menu.add_separator()
            
            for page_num in range(1, 6):
                label = f"  F{page_num} (Pagina {page_num})"
                if page_num == current_page:
                    label += " ✓"
                self.context_menu.add_command(
                    label=label,
                    command=lambda p=page_num: self.move_to_page(p)
                )
            
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Errore nel menu contestuale: {e}")
        finally:
            if self.context_menu:
                self.context_menu.grab_release()
    
    def move_to_page(self, page_num):
        """Sposta la clip in una pagina specifica"""
        self.page_selector.set(f"F{page_num}")
        self.on_page_changed(f"F{page_num}")
    
    def assign_hotkey(self):
        """Assegna una hotkey alla clip"""
        if self._is_destroyed:
            return
        try:
            self.hotkey_button.configure(text="Premi un tasto...")
        except Exception:
            pass
        self.on_hotkey_change(self.clip_name, self)
    
    def set_hotkey(self, key: str):
        """Imposta la hotkey visualizzata"""
        if self._is_destroyed:
            return
        self.hotkey = key
        try:
            self.hotkey_button.configure(text=f"Tasto: {key.upper()}")
            self.hotkey_label.configure(text=f"⌨️ {key.upper()}")
        except Exception:
            pass
    
    def confirm_remove(self):
        """Mostra dialog di conferma prima di rimuovere"""
        if self._is_destroyed:
            return
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "Conferma Rimozione",
            f"Vuoi rimuovere la clip '{self.clip_name}'?\n\n"
            "⚠️ ATTENZIONE: Questa azione:\n"
            "• Rimuoverà la clip dalla soundboard\n"
            "• Rimuoverà l'hotkey assegnato\n"
            "• ELIMINERÀ il file dalla cartella clips/\n\n"
            "Continuare?",
            icon='warning'
        )
        
        if result:
            self.on_remove(self.clip_name)
    
    def destroy(self):
        """Override destroy per prevenire errori durante la pulizia"""
        self._is_destroyed = True
        try:
            super().destroy()
        except Exception:
            pass


class AudioMixerApp(ctk.CTk):
    """Applicazione principale"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🎮 Gaming Soundboard - Mix Mic + Clip")
        self.geometry("1200x800")
        
        # System Tray
        self.tray_icon = None
        self.is_minimized_to_tray = False
        
        # Determina la directory base (funziona sia con .py che con .exe)
        if getattr(sys, 'frozen', False):
            # Se è un exe compilato con PyInstaller
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Se è eseguito come script Python
            self.base_dir = os.path.dirname(__file__)
        
        # File configurazione
        self.config_file = os.path.join(self.base_dir, "soundboard_config.json")
        
        # Carica dispositivo audio configurato
        saved_config = self.load_config_dict()
        output_device = saved_config.get('audio_output_device', None)
        secondary_output_device = saved_config.get('secondary_output_device', None)
        
        # Cartella clips (default o personalizzata)
        self.clips_folder = saved_config.get('clips_folder', os.path.join(self.base_dir, "clips"))
        if not os.path.exists(self.clips_folder):
            os.makedirs(self.clips_folder)
        
        print(f"📂 Caricamento configurazione all'avvio:")
        print(f"   Config file: {self.config_file}")
        print(f"   Primary device dal config: {output_device}")
        print(f"   Secondary device dal config: {secondary_output_device}")
        
        # Verifica che il dispositivo esista
        if output_device is not None:
            try:
                devices = sd.query_devices()
                if output_device >= len(devices) or devices[output_device]['max_output_channels'] == 0:
                    print(f"⚠ Dispositivo {output_device} non più disponibile, uso default")
                    output_device = None
                else:
                    print(f"✓ Dispositivo primario {output_device} validato: {devices[output_device]['name']}")
            except Exception as e:
                print(f"⚠ Errore validazione device: {e}")
                output_device = None
        
        # Mixer audio (soundboard)
        print(f"🎛️ Inizializzazione mixer con:")
        print(f"   Primary: {output_device}")
        print(f"   Secondary: {secondary_output_device}")
        self.mixer = AudioMixer(sample_rate=48000, buffer_size=512, output_device=output_device, secondary_output_device=secondary_output_device)  # 48kHz per Discord
        self.clip_widgets: Dict[str, ClipButton] = {}
        self.waiting_for_hotkey = None
        self.hotkey_bindings = {}
        self.hotkey_hooks = {}  # Salva i riferimenti agli hook per rimuoverli correttamente
        self.soundboard_enabled = True  # Stato abilitazione soundboard
        self.loop_enabled = False  # Stato loop globale
        self.temp_listener = None  # Listener temporaneo per assegnazione hotkey
        
        # ProMixer (mixer professionale multi-canale)
        self.pro_mixer = ProMixer(sample_rate=48000, buffer_size=512)
        self.pro_mixer_widgets = {}  # Widgets mixer tab
        self.pro_mixer_running = False
        
        # Sistema pagine soundboard
        self.current_page = 1
        self.total_pages = 5  # F1-F5
        self.clip_pages = {}  # {clip_name: page_number}
        
        # Recording state
        self.is_recording = False
        
        # YouTube Downloader
        self.youtube_downloader = YouTubeDownloader(self, self._add_downloaded_clip, COLORS, self.clips_folder)
        
        # Configurazione griglia
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create tabview for main content
        self.tabview = ctk.CTkTabview(self, width=900)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Tab 1: Soundboard
        self.tab_soundboard = self.tabview.add("🎮 Soundboard")
        
        # Tab 2: YouTube Downloader
        self.tab_youtube = self.tabview.add("📥 YouTube")
        
        # Tab 3: Mixer Professionale
        self.tab_mixer = self.tabview.add("🎛️ Mixer")
        
        # Tab 4: Impostazioni Audio
        self.tab_audio_settings = self.tabview.add("🔊 Audio")
        
        self.create_sidebar()
        self.create_soundboard_tab()
        self.youtube_downloader.create_youtube_tab(self.tab_youtube)
        self.create_mixer_tab()
        self.create_audio_settings_tab()
        self.create_control_panel()
        
        # Avvia mixer
        self.mixer.start()
        
        # Carica configurazione salvata
        self.load_config()
        
        # Registra hotkey globale per toggle soundboard (Scroll Lock)
        # Usa hook_key per compatibilità con i giochi
        try:
            def scroll_lock_callback(e):
                if e.event_type == 'down':
                    self.toggle_soundboard()
            keyboard.hook_key('scroll lock', scroll_lock_callback, suppress=False)
            logger.info("Hotkey globale registrato: Scroll Lock = Toggle Soundboard")
            logger.info("Premi Scroll Lock per abilitare/disabilitare la soundboard")
        except Exception as e:
            logger.error(f"Errore registrazione hotkey globale: {e}", exc_info=True)
        
        # Registra hotkey per toggle loop (Pause)
        # Usa hook_key per compatibilità con i giochi
        try:
            def pause_callback(e):
                if e.event_type == 'down':
                    self.toggle_loop()
            keyboard.hook_key('pause', pause_callback, suppress=False)
            logger.info("Hotkey loop registrato: Pause = Toggle Loop Globale")
        except Exception as e:
            logger.error(f"Errore registrazione hotkey loop: {e}", exc_info=True)
        
        # Registra hotkeys per cambio pagina (F1-F5)
        try:
            for page_num in range(1, 6):
                key = f'f{page_num}'
                keyboard.hook_key(key, lambda e, p=page_num: self.switch_page(p) if e.event_type == 'down' else None, suppress=False)
            logger.info("Hotkeys pagine registrate: F1-F5 per cambio pagina")
        except Exception as e:
            logger.error(f"Errore registrazione hotkeys pagine: {e}", exc_info=True)
        
        # Intercepta chiusura finestra per chiudere direttamente
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # Inizializza system tray se disponibile
        if TRAY_AVAILABLE:
            self.setup_system_tray()
    
    def create_sidebar(self):
        """Crea la sidebar sinistra"""
        self.sidebar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], width=250)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        # Logo/Titolo
        title = ctk.CTkLabel(
            self.sidebar,
            text="🎮 SOUNDBOARD",
            font=ctk.CTkFont(family="Segoe UI", size=48, weight="bold"),
            text_color=COLORS["accent"]
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Gaming Audio Mixer",
            font=ctk.CTkFont(family="Segoe UI", size=20),
            text_color=COLORS["text"]
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Pulsante Aggiungi Clip
        self.add_clip_btn = ctk.CTkButton(
            self.sidebar,
            text="➕ Aggiungi Clip Audio",
            command=self.add_clip,
            height=50,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        )
        self.add_clip_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Pulsante Seleziona Cartella Clips
        self.select_folder_btn = ctk.CTkButton(
            self.sidebar,
            text="📁 Cartella Clips",
            command=self.select_clips_folder,
            height=35,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=14)
        )
        self.select_folder_btn.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        # Label percorso cartella
        self.folder_label = ctk.CTkLabel(
            self.sidebar,
            text=f"📂 {os.path.basename(self.clips_folder)}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_muted"],
            wraplength=210
        )
        self.folder_label.grid(row=4, column=0, padx=20, pady=(0, 5))
        
        # Pulsante Carica Progetto
        self.load_project_btn = ctk.CTkButton(
            self.sidebar,
            text="💾 Carica Progetto",
            command=self.load_project,
            height=35,
            fg_color=COLORS["bg_card"]
        )
        self.load_project_btn.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        # Indicatore stato soundboard
        status_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["bg_card"], corner_radius=10)
        status_frame.grid(row=6, column=0, padx=20, pady=15, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🎮 SOUNDBOARD ATTIVA",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["success"]
        )
        self.status_label.pack(pady=10)
        
        ctk.CTkLabel(
            status_frame,
            text="Premi Scroll Lock per on/off",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text"]
        ).pack(pady=(0, 5))
        
        # Indicatore loop
        self.loop_label = ctk.CTkLabel(
            status_frame,
            text="🔁 Loop: OFF",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_muted"]
        )
        self.loop_label.pack(pady=(0, 10))
        
        ctk.CTkLabel(
            status_frame,
            text="Premi Pause per toggle loop",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 10))
        
        # Info
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="s")
        
        info = ctk.CTkLabel(
            info_frame,
            text="⚠️ SETUP RICHIESTO:\n" +
                 "1. Installa VB-Audio Cable\n" +
                 "2. Output PC → VB-Cable\n" +
                 "3. Discord input → VB-Cable\n" +
                 "\nUsa i tasti per le clip!",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#ffaa00",
            justify="left"
        )
        info.pack()
        
        # Selettore pagine soundboard
        pages_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        pages_frame.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            pages_frame,
            text="📑 Pagine (F1-F5)",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"]
        ).pack(pady=(0, 10))
        
        # Grid di pulsanti pagina
        page_buttons_grid = ctk.CTkFrame(pages_frame, fg_color="transparent")
        page_buttons_grid.pack()
        
        self.page_buttons = []
        for i in range(1, 6):  # F1-F5
            btn = ctk.CTkButton(
                page_buttons_grid,
                text=f"F{i}",
                command=lambda p=i: self.switch_page(p),
                width=45,
                height=45,
                fg_color=COLORS["accent"] if i == 1 else COLORS["bg_card"],
                hover_color=COLORS["accent"],
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
            )
            btn.grid(row=0, column=i-1, padx=2)
            self.page_buttons.append(btn)
        
        # Label pagina corrente
        self.page_label = ctk.CTkLabel(
            pages_frame,
            text=f"Pagina 1/5",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_secondary"]
        )
        self.page_label.pack(pady=(10, 0))
        
        # Pulsanti controllo finestra
        window_controls_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        window_controls_frame.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")
        window_controls_frame.grid_columnconfigure(0, weight=1)
        window_controls_frame.grid_columnconfigure(1, weight=1)
        
        # Pulsante Minimizza
        self.minimize_btn = ctk.CTkButton(
            window_controls_frame,
            text="➖ Tray",
            command=self.minimize_to_tray,
            height=35,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=14)
        )
        self.minimize_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Pulsante Chiudi
        self.close_btn = ctk.CTkButton(
            window_controls_frame,
            text="❌ Esci",
            command=self.quit_app,
            height=35,
            fg_color=COLORS["error"],
            hover_color="#b91c1c",
            font=ctk.CTkFont(family="Segoe UI", size=14)
        )
        self.close_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def switch_page(self, page_number):
        """Cambia la pagina corrente della soundboard"""
        self.current_page = page_number
        logger.info(f"Passaggio a pagina {page_number}")
        
        # Aggiorna colore pulsanti
        for i, btn in enumerate(self.page_buttons, 1):
            if i == page_number:
                btn.configure(fg_color=COLORS["accent"])
            else:
                btn.configure(fg_color=COLORS["bg_card"])
        
        # Aggiorna label
        self.page_label.configure(text=f"Pagina {page_number}/5")
        
        # Mostra/nascondi clip in base alla pagina
        self.update_clips_visibility()
    
    def update_clips_visibility(self):
        """Aggiorna la visibilità delle clip in base alla pagina corrente"""
        for clip_name, widget in self.clip_widgets.items():
            clip_page = self.clip_pages.get(clip_name, 1)  # Default pagina 1
            if clip_page == self.current_page:
                widget.grid()  # Mostra
            else:
                widget.grid_remove()  # Nascondi
    
    def refresh_clips(self):
        """Ricarica le clip dalla cartella clips"""
        logger.info("Aggiornamento clips dalla cartella...")
        clips_dir = self.clips_folder
        
        if not os.path.exists(clips_dir):
            logger.warning(f"Cartella clips non trovata: {clips_dir}")
            return
        
        try:
            # Lista dei file già caricati
            existing_files = set()
            for clip_name in self.clip_widgets.keys():
                if clip_name in self.mixer.clips:
                    existing_files.add(self.mixer.clips[clip_name].file_path)
            
            # Cerca nuovi file nella cartella
            new_clips_count = 0
            for filename in os.listdir(clips_dir):
                if filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    file_path = os.path.join(clips_dir, filename)
                    
                    # Salta se già caricato
                    if file_path in existing_files:
                        continue
                    
                    # Aggiungi nuova clip
                    try:
                        clip = AudioClip(file_path, filename)
                        self.mixer.add_clip(clip)
                        
                        # Crea widget
                        row = len(self.clip_widgets) // 3
                        col = len(self.clip_widgets) % 3
                        
                        clip_widget = ClipButton(
                            self.clips_container,
                            filename,
                            on_play=self.play_clip,
                            on_stop=self.stop_clip,
                            on_remove=self.remove_clip,
                            on_volume_change=self.set_clip_volume,
                            on_hotkey_change=self.start_hotkey_assignment,
                            app=self
                        )
                        clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                        
                        self.clip_widgets[filename] = clip_widget
                        
                        # Imposta pagina corrente per nuova clip
                        self.clip_pages[filename] = self.current_page
                        
                        new_clips_count += 1
                        logger.info(f"Nuova clip aggiunta: {filename}")
                        
                    except Exception as e:
                        logger.error(f"Errore caricamento clip {filename}: {e}")
            
            # Aggiorna visibilità
            self.update_clips_visibility()
            
            # Salva configurazione
            if new_clips_count > 0:
                self.save_config()
                logger.info(f"✓ Aggiunte {new_clips_count} nuove clip")
            else:
                logger.info("Nessuna nuova clip trovata")
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento clips: {e}", exc_info=True)
    
    def reorder_clips(self):
        """Riordina le clip nella griglia rimuovendo spazi vuoti"""
        logger.info("Riordinamento clips nella pagina corrente...")
        
        try:
            # Ottieni tutte le clip della pagina corrente
            current_page_clips = []
            for clip_name, widget in self.clip_widgets.items():
                clip_page = self.clip_pages.get(clip_name, 1)
                if clip_page == self.current_page:
                    current_page_clips.append((clip_name, widget))
            
            # Riposiziona le clip in modo compatto
            for index, (clip_name, widget) in enumerate(current_page_clips):
                row = index // 3
                col = index % 3
                widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            logger.info(f"✓ Riordinate {len(current_page_clips)} clip nella pagina {self.current_page}")
            
        except Exception as e:
            logger.error(f"Errore nel riordinamento clips: {e}", exc_info=True)
    
    def create_soundboard_tab(self):
        """Crea la tab principale con le clip"""
        # Container superiore per header e pulsanti
        top_frame = ctk.CTkFrame(self.tab_soundboard, fg_color="transparent")
        top_frame.pack(padx=20, pady=(20, 10), fill="x")
        top_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(
            top_frame,
            text="Audio Clips",
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color=COLORS["text"]
        )
        header.grid(row=0, column=0, sticky="w")
        
        # Frame per i pulsanti
        buttons_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="e")
        
        # Pulsante Riordina
        reorder_btn = ctk.CTkButton(
            buttons_frame,
            text="📐 Riordina",
            command=self.reorder_clips,
            height=40,
            width=130,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=10
        )
        reorder_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Pulsante Aggiorna
        refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Aggiorna",
            command=self.refresh_clips,
            height=40,
            width=130,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=10
        )
        refresh_btn.grid(row=0, column=1)
        
        # Scrollable frame per le clip
        self.clips_container = ctk.CTkScrollableFrame(
            self.tab_soundboard,
            fg_color="transparent"
        )
        self.clips_container.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.clips_container.grid_columnconfigure((0, 1, 2), weight=1)
    
    def create_control_panel(self):
        """Crea il pannello di controllo in basso"""
        self.control_panel = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=150)
        self.control_panel.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        self.control_panel.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Volume Microfono
        mic_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        mic_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            mic_frame,
            text="🎤 Microfono",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.mic_volume_label = ctk.CTkLabel(mic_frame, text="Volume: 80%", font=ctk.CTkFont(family="Segoe UI", size=16))
        self.mic_volume_label.pack(anchor="w", pady=(5, 0))
        
        self.mic_slider = ctk.CTkSlider(
            mic_frame,
            from_=0,
            to=100,
            command=self.on_mic_volume_changed
        )
        self.mic_slider.set(80)
        self.mic_slider.pack(fill="x", pady=(5, 0))
        
        # Master Volume (Output Discord/CABLE)
        master_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        master_frame.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            master_frame,
            text="🔊 Master (Discord)",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.master_volume_label = ctk.CTkLabel(master_frame, text="Volume: 100%", font=ctk.CTkFont(family="Segoe UI", size=16))
        self.master_volume_label.pack(anchor="w", pady=(5, 0))
        
        self.master_slider = ctk.CTkSlider(
            master_frame,
            from_=0,
            to=100,
            command=self.on_master_volume_changed
        )
        self.master_slider.set(100)
        self.master_slider.pack(fill="x", pady=(5, 0))
        
        # Secondary Volume (Cuffie)
        secondary_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        secondary_frame.grid(row=0, column=2, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            secondary_frame,
            text="🎧 Cuffie",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.secondary_volume_label = ctk.CTkLabel(secondary_frame, text="Volume: 100%", font=ctk.CTkFont(family="Segoe UI", size=16))
        self.secondary_volume_label.pack(anchor="w", pady=(5, 0))
        
        self.secondary_slider = ctk.CTkSlider(
            secondary_frame,
            from_=0,
            to=100,
            command=self.on_secondary_volume_changed
        )
        self.secondary_slider.set(100)
        self.secondary_slider.pack(fill="x", pady=(5, 0))
        
        # Effetti
        effects_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        effects_frame.grid(row=0, column=3, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            effects_frame,
            text="🎛 Effetti",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.reverb_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            effects_frame,
            text="Reverb",
            variable=self.reverb_var,
            command=self.toggle_reverb,
            font=ctk.CTkFont(family="Segoe UI", size=16)
        ).pack(anchor="w", pady=(5, 2))
        
        self.bass_label = ctk.CTkLabel(effects_frame, text="Bass Boost: 0%", font=ctk.CTkFont(family="Segoe UI", size=16))
        self.bass_label.pack(anchor="w", pady=(5, 0))
        
        self.bass_slider = ctk.CTkSlider(
            effects_frame,
            from_=0,
            to=200,
            command=self.on_bass_changed
        )
        self.bass_slider.set(100)
        self.bass_slider.pack(fill="x", pady=(2, 0))
        
        # Registrazione
        rec_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        rec_frame.grid(row=0, column=4, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            rec_frame,
            text="🔴 Registrazione",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.record_btn = ctk.CTkButton(
            rec_frame,
            text="⏺ Avvia Registrazione",
            command=self.toggle_recording,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=40
        )
        self.record_btn.pack(fill="x", pady=(10, 0))
        
        self.is_recording = False
    
    def add_clip(self):
        """Aggiunge una nuova clip audio"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                clip_name = os.path.basename(file_path)
                
                # Crea clip
                clip = AudioClip(file_path, clip_name)
                self.mixer.add_clip(clip)
                
                # Crea widget
                row = len(self.clip_widgets) // 3
                col = len(self.clip_widgets) % 3
                
                clip_widget = ClipButton(
                    self.clips_container,
                    clip_name,
                    on_play=self.play_clip,
                    on_stop=self.stop_clip,
                    on_remove=self.remove_clip,
                    on_volume_change=self.set_clip_volume,
                    on_hotkey_change=self.start_hotkey_assignment,
                    app=self
                )
                clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                self.clip_widgets[clip_name] = clip_widget
                
                # Salva configurazione
                self.save_config()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile caricare il file:\n{str(e)}")
    
    def play_clip(self, clip_name: str):
        """Avvia la riproduzione di una clip"""
        # Verifica che la clip sia nella pagina corrente
        clip_page = self.clip_pages.get(clip_name, 1)
        if clip_page != self.current_page:
            logger.warning(f"Clip '{clip_name}' non è nella pagina corrente ({self.current_page})")
            return
        
        if clip_name in self.mixer.clips:
            clip = self.mixer.clips[clip_name]
            clip.is_looping = False  # Loop non più supportato nel design compatto
            clip.play()
    
    def stop_clip(self, clip_name: str):
        """Ferma la riproduzione di una clip"""
        if clip_name in self.mixer.clips:
            self.mixer.clips[clip_name].stop()
    
    def remove_clip(self, clip_name: str):
        """Rimuove una clip e elimina il file se è nella cartella clips/"""
        if clip_name in self.mixer.clips:
            # Ottieni il percorso del file
            clip = self.mixer.clips[clip_name]
            file_path = clip.file_path
            
            # Rimuovi hotkey se presente
            if clip_name in self.hotkey_bindings:
                try:
                    keyboard.remove_hotkey(self.hotkey_bindings[clip_name])
                except:
                    pass
                del self.hotkey_bindings[clip_name]
            
            # Rimuovi dalla soundboard
            self.mixer.remove_clip(clip_name)
            self.clip_widgets[clip_name].destroy()
            del self.clip_widgets[clip_name]
            
            # Elimina il file se è nella cartella clips configurata
            try:
                # Verifica se il file è nella cartella clips
                if os.path.exists(file_path) and os.path.dirname(file_path) == self.clips_folder:
                    os.remove(file_path)
                    print(f"File eliminato: {file_path}")
            except Exception as e:
                print(f"Errore nell'eliminazione del file: {e}")
            
            # Riorganizza griglia
            for i, (name, widget) in enumerate(self.clip_widgets.items()):
                row = i // 3
                col = i % 3
                widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Salva configurazione
            self.save_config()
    
    def set_clip_volume(self, clip_name: str, volume: float):
        """Imposta il volume di una clip"""
        if clip_name in self.mixer.clips:
            self.mixer.clips[clip_name].volume = volume
            # Salva configurazione quando cambia il volume
            self.save_config()
    
    def on_mic_volume_changed(self, value):
        """Callback per volume microfono"""
        volume_pct = int(value)
        self.mic_volume_label.configure(text=f"Volume: {volume_pct}%")
        self.mixer.mic_volume = value / 100.0
    
    def on_master_volume_changed(self, value):
        """Callback per master volume"""
        volume_pct = int(value)
        self.master_volume_label.configure(text=f"Volume: {volume_pct}%")
        self.mixer.master_volume = value / 100.0
    
    def on_secondary_volume_changed(self, value):
        """Callback per secondary volume (cuffie)"""
        volume_pct = int(value)
        self.secondary_volume_label.configure(text=f"Volume: {volume_pct}%")
        self.mixer.secondary_volume = value / 100.0
    
    def toggle_reverb(self):
        """Attiva/disattiva reverb"""
        self.mixer.reverb_enabled = self.reverb_var.get()
    
    def on_bass_changed(self, value):
        """Callback per bass boost"""
        bass_pct = int(value - 100)
        self.bass_label.configure(text=f"Bass Boost: {bass_pct:+d}%")
        self.mixer.bass_boost = value / 100.0
    
    def toggle_recording(self):
        """Avvia/ferma la registrazione"""
        if not self.is_recording:
            self.mixer.start_recording()
            self.is_recording = True
            self.record_btn.configure(
                text="⏹ Ferma Registrazione",
                fg_color="#ff0000"
            )
        else:
            output_file = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            
            if output_file:
                self.mixer.stop_recording(output_file)
                messagebox.showinfo("Registrazione", f"File salvato:\n{output_file}")
            else:
                self.mixer.stop_recording("recording.wav")
            
            self.is_recording = False
            self.record_btn.configure(
                text="⏺ Avvia Registrazione",
                fg_color=COLORS["accent"]
            )
    
    def load_project(self):
        """Carica un progetto esistente"""
        folder = filedialog.askdirectory(title="Seleziona cartella con file audio")
        
        if folder:
            files = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
            
            for file in files[:9]:  # Max 9 clip
                file_path = os.path.join(folder, file)
                try:
                    clip = AudioClip(file_path, file)
                    self.mixer.add_clip(clip)
                    
                    row = len(self.clip_widgets) // 3
                    col = len(self.clip_widgets) % 3
                    
                    clip_widget = ClipButton(
                        self.clips_container,
                        file,
                        on_play=self.play_clip,
                        on_stop=self.stop_clip,
                        on_remove=self.remove_clip,
                        on_volume_change=self.set_clip_volume,
                        on_hotkey_change=self.start_hotkey_assignment,
                        app=self
                    )
                    clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    
                    self.clip_widgets[file] = clip_widget
                except:
                    pass
    
    def create_audio_settings_tab(self):
        """Crea il tab per le impostazioni audio con dual output"""
        self.tab_audio_settings.grid_columnconfigure(0, weight=1)
        self.tab_audio_settings.grid_rowconfigure(1, weight=1)
        
        # Intestazione
        header = ctk.CTkLabel(
            self.tab_audio_settings,
            text="🔊 Configurazione Dispositivi Audio (Dual Output)",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        
        # Container principale
        main_container = ctk.CTkScrollableFrame(self.tab_audio_settings, fg_color="transparent")
        main_container.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        
        # ===== OUTPUT PRIMARIO =====
        primary_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        primary_frame.grid(row=0, column=0, pady=10, sticky="ew")
        primary_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            primary_frame,
            text="📤 Output Primario (Discord via Voicemeeter)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        ).grid(row=0, column=0, columnspan=2, pady=(15, 10), padx=15, sticky="w")
        
        ctk.CTkLabel(
            primary_frame,
            text="Seleziona dispositivo:",
            font=ctk.CTkFont(size=13)
        ).grid(row=1, column=0, pady=10, padx=15, sticky="w")
        
        # Dropdown output primario
        self.primary_output_var = ctk.StringVar(value="Nessuno")
        self.primary_output_menu = ctk.CTkOptionMenu(
            primary_frame,
            variable=self.primary_output_var,
            values=["Caricamento..."],
            command=self.on_primary_output_changed,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            width=400
        )
        self.primary_output_menu.grid(row=1, column=1, pady=10, padx=15, sticky="ew")
        
        # ===== OUTPUT SECONDARIO =====
        secondary_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        secondary_frame.grid(row=1, column=0, pady=10, sticky="ew")
        secondary_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            secondary_frame,
            text="🎧 Output Secondario (Ascolto Diretto - Cuffie)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["success"]
        ).grid(row=0, column=0, columnspan=2, pady=(15, 10), padx=15, sticky="w")
        
        ctk.CTkLabel(
            secondary_frame,
            text="Seleziona dispositivo:",
            font=ctk.CTkFont(size=13)
        ).grid(row=1, column=0, pady=10, padx=15, sticky="w")
        
        # Dropdown output secondario
        self.secondary_output_var = ctk.StringVar(value="Nessuno")
        self.secondary_output_menu = ctk.CTkOptionMenu(
            secondary_frame,
            variable=self.secondary_output_var,
            values=["Caricamento..."],
            command=self.on_secondary_output_changed,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["success"],
            button_hover_color="#00b8d4",
            width=400
        )
        self.secondary_output_menu.grid(row=1, column=1, pady=10, padx=15, sticky="ew")
        
        # Checkbox "Abilita secondo output"
        self.enable_secondary_var = ctk.BooleanVar(value=False)
        self.enable_secondary_check = ctk.CTkCheckBox(
            secondary_frame,
            text="✓ Abilita secondo output (senti le clip direttamente)",
            variable=self.enable_secondary_var,
            command=self.on_secondary_enabled_changed,
            font=ctk.CTkFont(size=13)
        )
        self.enable_secondary_check.grid(row=2, column=0, columnspan=2, pady=(0, 15), padx=15, sticky="w")
        
        # Pulsante applica
        self.apply_btn = ctk.CTkButton(
            main_container,
            text="✓ APPLICA CONFIGURAZIONE",
            command=self.apply_audio_settings,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.apply_btn.grid(row=2, column=0, pady=20, sticky="ew")
        
        # Info box
        info_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        info_frame.grid(row=3, column=0, pady=10, sticky="ew")
        
        info_text = """💡 CONFIGURAZIONE DUAL OUTPUT:

📤 Output Primario (obbligatorio):
   • Seleziona "CABLE Input" per inviare a Voicemeeter → Discord
   • L'audio viene mixato con microfono e inviato a Discord

🎧 Output Secondario (opzionale):
   • Seleziona le tue cuffie per sentirti le clip direttamente
   • Utile se Voicemeeter è configurato solo per Discord
   • L'audio sarà inviato CONTEMPORANEAMENTE a entrambi gli output

⚡ Raccomandazione:
   • Primary: CABLE Input (VB-Audio Virtual Cable) 48kHz
   • Secondary: Headphones (Realtek HD Audio) o le tue cuffie"""
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="w"
        ).pack(pady=15, padx=15, fill="both")
        
        # Carica dispositivi disponibili
        self.load_available_devices()
    
    def load_available_devices(self):
        """Carica la lista di dispositivi audio disponibili"""
        try:
            devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            
            # Mostra SOLO dispositivi WASAPI (API moderna di Windows)
            self.device_list = []
            
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    hostapi_idx = device['hostapi']
                    hostapi_name = host_apis[hostapi_idx]['name'] if hostapi_idx < len(host_apis) else 'Unknown'
                    
                    # Filtra solo WASAPI
                    if 'WASAPI' in hostapi_name:
                        name = device['name']
                        channels = device['max_output_channels']
                        display_name = f"{name} ({channels}ch)"
                        self.device_list.append((i, f"[{i}] {display_name}"))
            
            # Ordina alfabeticamente
            self.device_list.sort(key=lambda x: x[1].lower())
            
            # Crea liste per i menu
            device_names = ["Nessuno"] + [name for _, name in self.device_list]
            
            # Aggiorna menu
            self.primary_output_menu.configure(values=device_names)
            self.secondary_output_menu.configure(values=device_names)
            
            # Carica configurazione salvata
            config = self.load_config_dict()
            primary_device = config.get('audio_output_device', None)
            secondary_device = config.get('secondary_output_device', None)
            
            # Imposta valori salvati
            if primary_device is not None:
                for dev_id, dev_name in self.device_list:
                    if dev_id == primary_device:
                        self.primary_output_var.set(dev_name)
                        break
            
            if secondary_device is not None:
                self.enable_secondary_var.set(True)
                for dev_id, dev_name in self.device_list:
                    if dev_id == secondary_device:
                        self.secondary_output_var.set(dev_name)
                        break
            
            print(f"✓ Caricati {len(self.device_list)} dispositivi audio")
            
        except Exception as e:
            print(f"❌ Errore caricamento dispositivi: {e}")
            messagebox.showerror("Errore", f"Impossibile caricare dispositivi audio:\n{str(e)}")
    
    def on_primary_output_changed(self, choice):
        """Callback cambio output primario"""
        print(f"Output primario selezionato: {choice}")
    
    def on_secondary_output_changed(self, choice):
        """Callback cambio output secondario"""
        print(f"Output secondario selezionato: {choice}")
    
    def on_secondary_enabled_changed(self):
        """Callback abilitazione/disabilitazione secondo output"""
        enabled = self.enable_secondary_var.get()
        print(f"Secondo output {'abilitato' if enabled else 'disabilitato'}")
    
    def apply_audio_settings(self):
        """Applica le impostazioni audio selezionate"""
        # Ottieni device ID da selezione
        primary_choice = self.primary_output_var.get()
        secondary_choice = self.secondary_output_var.get()
        
        primary_device = None
        secondary_device = None
        
        # Estrai ID da stringa "[ID] Nome (Xch)"
        if primary_choice != "Nessuno":
            try:
                primary_device = int(primary_choice.split(']')[0][1:])
            except:
                messagebox.showwarning("Attenzione", "Dispositivo primario non valido!")
                return
        else:
            messagebox.showwarning("Attenzione", "Devi selezionare almeno un output primario!")
            return
        
        if self.enable_secondary_var.get() and secondary_choice != "Nessuno":
            try:
                secondary_device = int(secondary_choice.split(']')[0][1:])
            except:
                print("⚠ Device secondario non valido, ignorato")
                secondary_device = None
        
        try:
            # Salva configurazione
            config = self.load_config_dict()
            config['audio_output_device'] = primary_device
            config['secondary_output_device'] = secondary_device
            
            print(f"💾 Salvataggio configurazione:")
            print(f"   Primary device: {primary_device}")
            print(f"   Secondary device: {secondary_device}")
            print(f"   File: {self.config_file}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print("✓ Configurazione salvata su disco")
            
            # Riavvia mixer con nuovi dispositivi
            self.mixer.stop()
            self.mixer.output_device = primary_device
            self.mixer.secondary_output_device = secondary_device
            
            print(f"🔄 Riavvio mixer:")
            print(f"   Primary: {primary_device}")
            print(f"   Secondary: {secondary_device}")
            
            self.mixer.start()
            
            # Messaggio conferma
            devices = sd.query_devices()
            primary_name = devices[primary_device]['name']
            msg = f"✓ Output Primario:\n{primary_name}"
            
            if secondary_device is not None:
                secondary_name = devices[secondary_device]['name']
                msg += f"\n\n✓ Output Secondario:\n{secondary_name}"
            
            messagebox.showinfo("Configurazione Applicata", msg + "\n\nIl mixer è stato riavviato.")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile applicare configurazione:\n{str(e)}")
            print(f"❌ Errore apply: {e}")
    
    def load_config_dict(self):
        """Carica il dizionario di configurazione"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"clips": []}
    
    def create_mixer_tab(self):
        """Crea il tab del mixer professionale"""
        self.tab_mixer.grid_columnconfigure(0, weight=1)
        self.tab_mixer.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self.tab_mixer, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="🎛️ MIXER PROFESSIONALE",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["accent"]
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Control buttons
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        self.mixer_start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ AVVIA MIXER",
            width=140,
            height=40,
            fg_color=COLORS["success"],
            hover_color="#059669",
            command=self.start_pro_mixer,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mixer_start_btn.grid(row=0, column=0, padx=5)
        
        self.mixer_stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ FERMA MIXER",
            width=140,
            height=40,
            fg_color=COLORS["danger"],
            hover_color="#b91c1c",
            command=self.stop_pro_mixer,
            state="disabled",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mixer_stop_btn.grid(row=0, column=1, padx=5)
        
        config_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ CONFIGURA",
            width=140,
            height=40,
            command=self.open_mixer_config,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        config_btn.grid(row=0, column=2, padx=5)
        
        # Main mixer container
        mixer_container = ctk.CTkScrollableFrame(
            self.tab_mixer,
            fg_color=COLORS["bg_primary"],
            orientation="horizontal"
        )
        mixer_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Input Channels Section
        input_frame = ctk.CTkFrame(mixer_container, fg_color="transparent")
        input_frame.pack(side="left", fill="y", padx=10)
        
        ctk.CTkLabel(
            input_frame,
            text="INPUT CHANNELS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        ).pack(pady=10)
        
        channels_grid = ctk.CTkFrame(input_frame, fg_color="transparent")
        channels_grid.pack(fill="both", expand=True)
        
        # Create channel strips
        self.mixer_channel_strips = {}
        for i, (ch_id, channel) in enumerate(self.pro_mixer.channels.items()):
            strip = self.create_channel_strip(channels_grid, ch_id, channel)
            strip.grid(row=0, column=i, padx=5, pady=5, sticky="ns")
            self.mixer_channel_strips[ch_id] = strip
        
        # Separator
        sep = ctk.CTkFrame(mixer_container, width=3, fg_color=COLORS["border"])
        sep.pack(side="left", fill="y", padx=20)
        
        # Output Buses Section
        output_frame = ctk.CTkFrame(mixer_container, fg_color="transparent")
        output_frame.pack(side="left", fill="y", padx=10)
        
        ctk.CTkLabel(
            output_frame,
            text="OUTPUT BUSES",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=10)
        
        buses_grid = ctk.CTkFrame(output_frame, fg_color="transparent")
        buses_grid.pack(fill="both", expand=True)
        
        # Create bus strips
        self.mixer_bus_strips = {}
        for i, (bus_name, bus) in enumerate(self.pro_mixer.buses.items()):
            strip = self.create_bus_strip(buses_grid, bus_name, bus)
            strip.grid(row=0, column=i, padx=5, pady=5, sticky="ns")
            self.mixer_bus_strips[bus_name] = strip
    
    def create_channel_strip(self, parent, channel_id, channel):
        """Crea uno strip per un canale input"""
        strip_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            width=120
        )
        
        # Nome canale
        name_label = ctk.CTkLabel(
            strip_frame,
            text=channel.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        )
        name_label.pack(pady=(10, 5))
        
        # VU Meter placeholder (Canvas)
        meter = Canvas(
            strip_frame,
            width=30,
            height=100,
            bg=COLORS["bg_card"],
            highlightthickness=0
        )
        meter.pack(pady=5)
        meter.create_rectangle(2, 2, 28, 98, fill=COLORS["bg_card"], outline=COLORS["border"])
        strip_frame.meter = meter  # Salva riferimento
        
        # Fader vertical
        fader = ctk.CTkSlider(
            strip_frame,
            from_=12,
            to=-60,
            orientation="vertical",
            height=150,
            width=20,
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent"],
            command=lambda v: self.on_channel_fader_change(channel_id, v)
        )
        fader.set(0)
        fader.pack(pady=10)
        
        # dB Label
        db_label = ctk.CTkLabel(
            strip_frame,
            text="0.0 dB",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        db_label.pack()
        strip_frame.db_label = db_label
        
        # Routing buttons
        routing_frame = ctk.CTkFrame(strip_frame, fg_color="transparent")
        routing_frame.pack(pady=10)
        
        ctk.CTkLabel(
            routing_frame,
            text="Routing:",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"]
        ).pack()
        
        buttons_grid = ctk.CTkFrame(routing_frame, fg_color="transparent")
        buttons_grid.pack()
        
        strip_frame.routing_buttons = {}
        for i, bus_name in enumerate(['A1', 'A2', 'A3', 'B1', 'B2']):
            btn = ctk.CTkButton(
                buttons_grid,
                text=bus_name,
                width=35,
                height=22,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["accent_hover"],
                font=ctk.CTkFont(size=9),
                command=lambda ch=channel_id, b=bus_name: self.toggle_routing(ch, b)
            )
            btn.grid(row=i//3, column=i%3, padx=1, pady=1)
            strip_frame.routing_buttons[bus_name] = btn
        
        # Mute/Solo
        controls = ctk.CTkFrame(strip_frame, fg_color="transparent")
        controls.pack(pady=5)
        
        mute_btn = ctk.CTkButton(
            controls,
            text="M",
            width=40,
            height=28,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self.toggle_channel_mute(channel_id)
        )
        mute_btn.grid(row=0, column=0, padx=2)
        strip_frame.mute_btn = mute_btn
        
        solo_btn = ctk.CTkButton(
            controls,
            text="S",
            width=40,
            height=28,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["warning"],
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self.toggle_channel_solo(channel_id)
        )
        solo_btn.grid(row=0, column=1, padx=2)
        strip_frame.solo_btn = solo_btn
        
        return strip_frame
    
    def create_bus_strip(self, parent, bus_name, bus):
        """Crea uno strip per un bus output"""
        strip_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=10,
            border_width=2,
            border_color=COLORS["accent"],
            width=120
        )
        
        # Nome bus
        name_label = ctk.CTkLabel(
            strip_frame,
            text=f"BUS {bus_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"]
        )
        name_label.pack(pady=(10, 5))
        
        # Device label
        device_label = ctk.CTkLabel(
            strip_frame,
            text="No Device",
            font=ctk.CTkFont(size=8),
            text_color=COLORS["text_muted"],
            wraplength=100
        )
        device_label.pack()
        strip_frame.device_label = device_label
        
        # VU Meter
        meter = Canvas(
            strip_frame,
            width=35,
            height=100,
            bg=COLORS["bg_card"],
            highlightthickness=0
        )
        meter.pack(pady=5)
        meter.create_rectangle(2, 2, 33, 98, fill=COLORS["bg_card"], outline=COLORS["border"])
        strip_frame.meter = meter
        
        # Master fader
        fader = ctk.CTkSlider(
            strip_frame,
            from_=12,
            to=-60,
            orientation="vertical",
            height=150,
            width=25,
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent"],
            command=lambda v: self.on_bus_fader_change(bus_name, v)
        )
        fader.set(0)
        fader.pack(pady=10)
        
        # dB Label
        db_label = ctk.CTkLabel(
            strip_frame,
            text="0.0 dB",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        db_label.pack()
        strip_frame.db_label = db_label
        
        # Mute button
        mute_btn = ctk.CTkButton(
            strip_frame,
            text="MUTE",
            width=80,
            height=35,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.toggle_bus_mute(bus_name)
        )
        mute_btn.pack(pady=10)
        strip_frame.mute_btn = mute_btn
        
        return strip_frame
    
    def on_channel_fader_change(self, channel_id, value):
        """Callback fader canale"""
        db = float(value)
        if channel_id in self.pro_mixer.channels:
            self.pro_mixer.channels[channel_id].set_fader_db(db)
            if channel_id in self.mixer_channel_strips:
                self.mixer_channel_strips[channel_id].db_label.configure(text=f"{db:.1f} dB")
    
    def on_bus_fader_change(self, bus_name, value):
        """Callback fader bus"""
        db = float(value)
        if bus_name in self.pro_mixer.buses:
            self.pro_mixer.buses[bus_name].set_fader_db(db)
            if bus_name in self.mixer_bus_strips:
                self.mixer_bus_strips[bus_name].db_label.configure(text=f"{db:.1f} dB")
    
    def toggle_routing(self, channel_id, bus_name):
        """Toggle routing di un canale verso un bus"""
        if channel_id in self.pro_mixer.channels:
            current = self.pro_mixer.channels[channel_id].routing.get(bus_name, False)
            new_state = not current
            self.pro_mixer.set_channel_routing(channel_id, bus_name, new_state)
            
            # Aggiorna UI
            if channel_id in self.mixer_channel_strips:
                btn = self.mixer_channel_strips[channel_id].routing_buttons[bus_name]
                btn.configure(fg_color=COLORS["accent"] if new_state else COLORS["bg_card"])
    
    def toggle_channel_mute(self, channel_id):
        """Toggle mute canale"""
        if channel_id in self.pro_mixer.channels:
            channel = self.pro_mixer.channels[channel_id]
            channel.mute = not channel.mute
            
            if channel_id in self.mixer_channel_strips:
                btn = self.mixer_channel_strips[channel_id].mute_btn
                btn.configure(fg_color=COLORS["danger"] if channel.mute else COLORS["bg_card"])
    
    def toggle_channel_solo(self, channel_id):
        """Toggle solo canale"""
        if channel_id in self.pro_mixer.channels:
            channel = self.pro_mixer.channels[channel_id]
            channel.solo = not channel.solo
            
            if channel_id in self.mixer_channel_strips:
                btn = self.mixer_channel_strips[channel_id].solo_btn
                btn.configure(fg_color=COLORS["warning"] if channel.solo else COLORS["bg_card"])
    
    def toggle_bus_mute(self, bus_name):
        """Toggle mute bus"""
        if bus_name in self.pro_mixer.buses:
            bus = self.pro_mixer.buses[bus_name]
            bus.mute = not bus.mute
            
            if bus_name in self.mixer_bus_strips:
                btn = self.mixer_bus_strips[bus_name].mute_btn
                btn.configure(
                    fg_color=COLORS["danger"] if bus.mute else COLORS["bg_card"],
                    text="MUTED" if bus.mute else "MUTE"
                )
    
    def start_pro_mixer(self):
        """Avvia il mixer professionale"""
        try:
            self.pro_mixer.start_all()
            self.pro_mixer_running = True
            self.mixer_start_btn.configure(state="disabled")
            self.mixer_stop_btn.configure(state="normal")
            messagebox.showinfo("ProMixer", "Mixer professionale avviato!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare mixer:\n{e}")
    
    def stop_pro_mixer(self):
        """Ferma il mixer professionale"""
        self.pro_mixer.stop_all()
        self.pro_mixer_running = False
        self.mixer_start_btn.configure(state="normal")
        self.mixer_stop_btn.configure(state="disabled")
    
    def open_mixer_config(self):
        """Apre finestra configurazione mixer"""
        MixerConfigWindow(self, self.pro_mixer, self.mixer_channel_strips, self.mixer_bus_strips)
    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        # Salva configurazione
        self.save_config()
        
        # Ferma ProMixer se attivo
        if self.pro_mixer_running:
            self.pro_mixer.stop_all()
        
        # Rimuovi hotkey globali
        try:
            keyboard.remove_hotkey('scroll lock')
            keyboard.remove_hotkey('pause')
        except:
            pass
        
        # Rimuovi tutti gli hotkey bindings delle clip usando i riferimenti salvati
        for clip_name in list(self.hotkey_bindings.keys()):
            try:
                if clip_name in self.hotkey_hooks:
                    hook_ref = self.hotkey_hooks[clip_name]
                    # Se è una stringa, è un add_hotkey
                    if isinstance(hook_ref, str):
                        keyboard.remove_hotkey(hook_ref)
                    else:
                        # Altrimenti è un hook reference
                        keyboard.unhook(hook_ref)
                    logger.debug(f"Rimosso hotkey per {clip_name}")
            except Exception as e:
                logger.debug(f"Errore rimozione hotkey per {clip_name}: {e}")
        
        # Chiudi tray icon se presente
        if TRAY_AVAILABLE and self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        self.mixer.stop()
        self.destroy()
    
    def start_hotkey_assignment(self, clip_name: str, widget: ClipButton):
        """Inizia l'assegnazione di una hotkey"""
        self.waiting_for_hotkey = (clip_name, widget)
        widget.set_hotkey("Premi un tasto...")
        
        # Usa keyboard.on_press per catturare anche il scan_code (per numpad)
        self.captured_keys = []
        self.modifier_keys = set()
        self.assignment_timer = None
        
        def on_key_capture(event):
            if event.event_type != 'down':
                return
            
            # Se è un modificatore, aggiungilo e avvia un timer di attesa
            if event.name in ['shift', 'ctrl', 'alt', 'windows', 'cmd']:
                self.modifier_keys.add(event.name)
                logger.debug(f"Modificatore {event.name} premuto, attendo tasto principale...")
                
                # Cancella timer precedente se esiste
                if self.assignment_timer:
                    self.after_cancel(self.assignment_timer)
                
                # Aspetta 1.5 secondi: se non arriva un tasto principale, ignora
                def modifier_timeout():
                    if self.temp_listener:
                        keyboard.unhook(self.temp_listener)
                        self.temp_listener = None
                    widget.set_hotkey("Solo modificatori - riprova")
                    logger.debug("Solo modificatori premuti, operazione annullata")
                    self.waiting_for_hotkey = None
                    self.modifier_keys = set()
                
                self.assignment_timer = self.after(1500, modifier_timeout)
                return
            
            # È un tasto normale/numpad - cattura IMMEDIATAMENTE
            logger.debug(f"Tasto principale: {event.name} (scan: {event.scan_code}), modificatori: {list(self.modifier_keys)}")
            
            # Cancella il timer se esisteva
            if self.assignment_timer:
                self.after_cancel(self.assignment_timer)
                self.assignment_timer = None
            
            self.captured_keys.append({
                'name': event.name,
                'scan_code': event.scan_code,
                'modifiers': list(self.modifier_keys)
            })
            
            # Rimuovi il listener IMMEDIATAMENTE
            if self.temp_listener:
                keyboard.unhook(self.temp_listener)
                self.temp_listener = None
            
            # Processa SUBITO (nessun delay)
            self.after(0, lambda: self._process_captured_hotkey(clip_name, widget))
        
        # Registra listener temporaneo
        self.temp_listener = keyboard.hook(on_key_capture)
    
    def _process_captured_hotkey(self, clip_name, widget):
        """Processa il tasto catturato e determina se è numpad o tastiera"""
        if not self.captured_keys:
            widget.set_hotkey("Errore")
            return
        
        key_info = self.captured_keys[0]
        scan_code = key_info['scan_code']
        key_name = key_info['name']
        modifiers = key_info.get('modifiers', [])
        
        # Scan codes per numpad su Windows
        numpad_scancodes = {
            71: 'Numpad 7', 72: 'Numpad 8', 73: 'Numpad 9',
            75: 'Numpad 4', 76: 'Numpad 5', 77: 'Numpad 6',
            79: 'Numpad 1', 80: 'Numpad 2', 81: 'Numpad 3',
            82: 'Numpad 0', 83: 'Numpad .',
            78: 'Numpad +', 74: 'Numpad -', 55: 'Numpad *', 53: 'Numpad /'
        }
        
        # Determina il formato della hotkey
        is_numpad = scan_code in numpad_scancodes
        
        if is_numpad:
            display_name = numpad_scancodes[scan_code]
            if modifiers:
                # Combinazione con numpad (es: shift+numpad 7)
                combo = '+'.join(modifiers + [display_name.lower()])
                storage_key = f"combo_scan_{scan_code}_{'_'.join(modifiers)}"
                self._assign_combo_with_numpad(clip_name, widget, combo, storage_key, scan_code, modifiers)
            else:
                # Numpad singolo
                storage_key = f"scan_{scan_code}"
                self._assign_single_numpad(clip_name, widget, storage_key, display_name, scan_code)
        else:
            # Tasto normale (non numpad)
            if modifiers:
                # Combinazione normale (es: shift+f1)
                combo = '+'.join(modifiers + [key_name])
                self._assign_combo_normal(clip_name, widget, combo)
            else:
                # Tasto singolo normale
                storage_key = f"key_{key_name}"
                self._assign_single_key(clip_name, widget, storage_key, key_name)
        
        self.captured_keys = []
        self.modifier_keys = set()
        self.waiting_for_hotkey = None
    
    def _remove_old_hotkey(self, clip_name):
        """Rimuove un vecchio hotkey se esiste"""
        if clip_name not in self.hotkey_bindings:
            return
        
        old_key = self.hotkey_bindings[clip_name]
        
        # Rimuovi usando il riferimento all'hook salvato
        if clip_name in self.hotkey_hooks:
            try:
                hook_ref = self.hotkey_hooks[clip_name]
                keyboard.unhook(hook_ref)
                logger.debug(f"Rimosso hook per {clip_name} (key: {old_key})")
                del self.hotkey_hooks[clip_name]
            except Exception as e:
                logger.debug(f"Errore rimozione hook {old_key}: {e}")
        
        # Rimuovi dalla lista bindings
        if clip_name in self.hotkey_bindings:
            del self.hotkey_bindings[clip_name]
    
    def _assign_single_numpad(self, clip_name, widget, storage_key, display_name, scan_code):
        """Assegna un tasto numpad singolo"""
        try:
            self._remove_old_hotkey(clip_name)
            
            # Registra con hook_key sul scan_code (funziona nei giochi)
            def callback(e, name=clip_name):
                if e.event_type == 'down':
                    # Non triggerare se ci sono modificatori premuti (potrebbero essere combinazioni)
                    if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                        self.trigger_clip_hotkey(name)
            
            hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(display_name)
            
            logger.info(f"Hotkey numpad '{display_name}' (scan {scan_code}) assegnato a '{clip_name}'")
            self.save_config()
        except Exception as e:
            logger.error(f"Errore assegnazione numpad: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _assign_single_key(self, clip_name, widget, storage_key, key_name):
        """Assegna un tasto singolo normale"""
        try:
            self._remove_old_hotkey(clip_name)
            
            # Registra con hook_key (funziona nei giochi)
            def callback(e, name=clip_name):
                if e.event_type == 'down':
                    # Non triggerare se ci sono modificatori premuti (potrebbero essere combinazioni)
                    if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                        self.trigger_clip_hotkey(name)
            
            hook_ref = keyboard.hook_key(key_name, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(key_name)
            
            logger.info(f"Hotkey '{key_name}' assegnato a '{clip_name}'")
            self.save_config()
        except Exception as e:
            logger.error(f"Errore assegnazione tasto: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    def _assign_combo_normal(self, clip_name, widget, combo):
        """Assegna una combinazione normale (es: shift+f1)"""
        try:
            self._remove_old_hotkey(clip_name)
            
            # Usa add_hotkey per combinazioni (non funziona sempre nei giochi, ma è l'unico modo)
            keyboard.add_hotkey(combo, lambda name=clip_name: self.trigger_clip_hotkey(name), suppress=False)
            self.hotkey_bindings[clip_name] = combo
            # Per add_hotkey non abbiamo un riferimento hook diretto, usiamo la stringa combo
            self.hotkey_hooks[clip_name] = combo
            widget.set_hotkey(combo)
            
            logger.info(f"Hotkey combinazione '{combo}' assegnato a '{clip_name}'")
            logger.warning("Le combinazioni potrebbero non funzionare in alcuni giochi")
            self.save_config()
        except Exception as e:
            logger.error(f"Errore assegnazione combinazione: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _assign_combo_with_numpad(self, clip_name, widget, combo, storage_key, scan_code, modifiers):
        """Assegna una combinazione con numpad (es: shift+numpad 7)"""
        try:
            self._remove_old_hotkey(clip_name)
            
            # Per combinazioni con numpad, dobbiamo usare hook e controllare i modificatori manualmente
            def callback(e, name=clip_name, mods=modifiers):
                if e.event_type == 'down':
                    # Verifica che tutti i modificatori siano premuti
                    all_pressed = all(keyboard.is_pressed(mod) for mod in mods)
                    if all_pressed:
                        self.trigger_clip_hotkey(name)
            
            hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(combo)
            
            logger.info(f"Hotkey combinazione numpad '{combo}' assegnato a '{clip_name}'")
            self.save_config()
        except Exception as e:
            logger.error(f"Errore assegnazione combinazione numpad: {e}", exc_info=True)
            widget.set_hotkey("Errore")
            logger.error(f"Errore assegnazione combinazione numpad: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _get_numpad_display_name(self, scan_code):
        """Restituisce il nome display per un scan_code numpad"""
        numpad_names = {
            71: 'Numpad 7', 72: 'Numpad 8', 73: 'Numpad 9',
            75: 'Numpad 4', 76: 'Numpad 5', 77: 'Numpad 6',
            79: 'Numpad 1', 80: 'Numpad 2', 81: 'Numpad 3',
            82: 'Numpad 0', 83: 'Numpad .',
            78: 'Numpad +', 74: 'Numpad -', 55: 'Numpad *', 53: 'Numpad /'
        }
        return numpad_names.get(scan_code, f'Scan {scan_code}')
    
    def _on_numpad_hotkey(self, event, clip_name):
        """Callback per hotkey numpad"""
        if event.event_type == 'down':
            self.trigger_clip_hotkey(clip_name)
    
    def _make_hotkey_callback(self, clip_name: str):
        """Crea una callback per hotkey con closure corretta"""
        def callback():
            self.trigger_clip_hotkey(clip_name)
        return callback
    
    def trigger_clip_hotkey(self, clip_name: str):
        """Triggera una clip tramite hotkey"""
        try:
            # Non triggerare se siamo in modalità assegnazione
            if self.waiting_for_hotkey is not None:
                logger.debug(f"In modalità assegnazione, ignoro trigger per {clip_name}")
                return
            
            logger.debug(f"Hotkey premuto per: {clip_name} (enabled: {self.soundboard_enabled})")
            if not self.soundboard_enabled:
                logger.debug("Soundboard disabilitata, ignoro hotkey")
                return  # Soundboard disabilitata
            if clip_name in self.clip_widgets:
                widget = self.clip_widgets[clip_name]
                if widget.is_playing:
                    self.stop_clip(clip_name)
                    widget.stop()
                else:
                    self.play_clip(clip_name)
                    widget.play()
        except Exception as e:
            logger.error(f"ERRORE in trigger_clip_hotkey: {e}", exc_info=True)
    
    def play_notification_sound(self, sound_type: str):
        """Riproduce un suono di notifica (on/off)"""
        try:
            sound_file = os.path.join(self.base_dir, f"soundboard_{sound_type}.wav")
            if os.path.exists(sound_file):
                import soundfile as sf
                import sounddevice as sd
                
                # Carica il suono
                data, samplerate = sf.read(sound_file)
                
                # Riproduci sul dispositivo secondario (cuffie) se disponibile
                device = self.mixer.secondary_output_device if self.mixer.secondary_output_device else self.mixer.output_device
                
                # Riproduci e attendi il completamento
                sd.play(data, samplerate, device=device)
                sd.wait()  # Attendi che il suono finisca
            else:
                logger.warning(f"File suono notifica non trovato: {sound_file}")
        except Exception as e:
            logger.error(f"Errore riproduzione suono notifica: {e}", exc_info=True)
    
    def toggle_soundboard(self):
        """Abilita/Disabilita la soundboard (hotkey globale: Scroll Lock)"""
        try:
            logger.info(f"Toggle soundboard chiamato! (attuale: {self.soundboard_enabled})")
            self.soundboard_enabled = not self.soundboard_enabled
            status = "ABILITATA ✓" if self.soundboard_enabled else "DISABILITATA ✗"
            logger.info(f"SOUNDBOARD {status}")
            
            # Riproduci suono notifica
            if self.soundboard_enabled:
                self.play_notification_sound("on")
            else:
                self.play_notification_sound("off")
        except Exception as e:
            logger.error(f"ERRORE in toggle_soundboard: {e}", exc_info=True)
        
        # Aggiorna titolo finestra
        if self.soundboard_enabled:
            self.title("🎮 Gaming Soundboard - ATTIVA")
            self.status_label.configure(
                text="🎮 SOUNDBOARD ATTIVA",
                text_color=COLORS["success"]
            )
        else:
            self.title("🎮 Gaming Soundboard - DISATTIVATA")
            self.status_label.configure(
                text="⛔ SOUNDBOARD DISATTIVATA",
                text_color=COLORS["accent"]
            )
    
    def toggle_loop(self):
        """Toggle loop globale per tutte le clip (Pause)"""
        try:
            self.loop_enabled = not self.loop_enabled
            logger.info(f"Loop globale: {'ATTIVO' if self.loop_enabled else 'DISATTIVO'}")
            
            # Aggiorna tutte le clip nel mixer
            for clip in self.mixer.clips.values():
                clip.loop = self.loop_enabled
            
            # Aggiorna UI
            if self.loop_enabled:
                self.loop_label.configure(
                    text="🔁 Loop: ON",
                    text_color=COLORS["success"]
                )
                self.play_notification_sound("on")
            else:
                self.loop_label.configure(
                    text="🔁 Loop: OFF",
                    text_color=COLORS["text_muted"]
                )
                self.play_notification_sound("off")
            
            # Log
            status = "ATTIVO ✓" if self.loop_enabled else "DISATTIVO ✗"
            logger.info(f"🔁 LOOP {status}")
        except Exception as e:
            logger.error(f"ERRORE in toggle_loop: {e}", exc_info=True)
    
    def minimize_to_tray(self):
        """Minimizza l'applicazione nel system tray"""
        if TRAY_AVAILABLE and self.tray_icon:
            self.withdraw()  # Nasconde la finestra
            self.is_minimized_to_tray = True
            logger.info("Applicazione minimizzata nel system tray")
        else:
            self.iconify()  # Fallback: minimizza normalmente
    
    def quit_app(self):
        """Chiude completamente l'applicazione"""
        logger.info("Chiusura applicazione richiesta dall'utente")
        self.on_closing()
    
    def select_clips_folder(self):
        """Seleziona una cartella personalizzata per le clip"""
        folder = filedialog.askdirectory(
            title="Seleziona la cartella delle clip audio",
            initialdir=self.clips_folder
        )
        
        if folder:
            self.clips_folder = folder
            self.folder_label.configure(text=f"📂 {os.path.basename(folder)}")
            
            # Salva nella configurazione
            config = self.load_config_dict()
            config['clips_folder'] = folder
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo(
                "Cartella Aggiornata",
                f"Cartella clips impostata su:\n{folder}\n\n"
                "Le nuove clip scaricate da YouTube verranno salvate qui."
            )
    
    def setup_system_tray(self):
        """Configura l'icona nella system tray"""
        if not TRAY_AVAILABLE:
            return
        
        from PIL import Image, ImageDraw
        
        # Crea icona semplice (cerchio colorato)
        image = Image.new('RGB', (64, 64), color=COLORS["accent"])
        draw = ImageDraw.Draw(image)
        draw.ellipse([4, 4, 60, 60], fill=COLORS["success"], outline=COLORS["text"])
        
        # Menu tray
        menu = pystray.Menu(
            pystray.MenuItem("Mostra/Nascondi", self.toggle_window_visibility),
            pystray.MenuItem("Toggle Soundboard (Scroll Lock)", self.toggle_soundboard),
            pystray.MenuItem("Esci", self.quit_app)
        )
        
        # Crea icona
        self.tray_icon = pystray.Icon("soundboard", image, "Gaming Soundboard", menu)
        
        # Avvia tray in thread separato
        import threading
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        print("✓ System tray inizializzato")
    
    def toggle_window_visibility(self):
        """Mostra/Nascondi finestra"""
        if self.is_minimized_to_tray:
            self.deiconify()
            self.is_minimized_to_tray = False
        else:
            self.withdraw()
            self.is_minimized_to_tray = True
    
    def on_closing(self):
        """Gestisce la chiusura della finestra - minimizza a tray invece di chiudere"""
        if TRAY_AVAILABLE:
            self.withdraw()
            self.is_minimized_to_tray = True
            print("✓ Minimizzato a system tray (usa 'Esci' dal menu tray per chiudere)")
        else:
            self.quit_app()
    
    def quit_app(self):
        """Chiude completamente l'applicazione"""
        print("🛑 Chiusura applicazione...")
        
        # Ferma mixer
        if hasattr(self, 'mixer'):
            self.mixer.stop()
        
        # Ferma system tray
        if TRAY_AVAILABLE and self.tray_icon is not None:
            self.tray_icon.stop()
        
        # Chiudi finestra
        self.destroy()
    
    def _add_downloaded_clip(self, file_path):
        """Aggiunge la clip scaricata alla soundboard"""
        try:
            clip_name = os.path.basename(file_path)
            
            # Crea clip
            clip = AudioClip(file_path, clip_name)
            self.mixer.add_clip(clip)
            
            # Crea widget
            row = len(self.clip_widgets) // 3
            col = len(self.clip_widgets) % 3
            
            clip_widget = ClipButton(
                self.clips_container,
                clip_name,
                on_play=self.play_clip,
                on_stop=self.stop_clip,
                on_remove=self.remove_clip,
                on_volume_change=self.set_clip_volume,
                on_hotkey_change=self.start_hotkey_assignment,
                app=self
            )
            clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            self.clip_widgets[clip_name] = clip_widget
            
            # Salva configurazione
            self.save_config()
            
            # Vai alla tab soundboard
            self.tabview.set("🎮 Soundboard")
            
            messagebox.showinfo("Successo", f"Clip '{clip_name}' aggiunta!\nAssegna un tasto rapido nella tab Soundboard.")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aggiungere la clip:\n{str(e)}")
    
    def open_advanced_editor(self):
        """Apre l'editor avanzato in una nuova finestra"""
        import subprocess
        import sys
        
        # Lancia l'editor avanzato in un nuovo processo
        script_path = os.path.join(self.base_dir, "advanced_editor.py")
        
        try:
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire l'editor:\n{str(e)}")
    
    def save_config(self):
        """Salva la configurazione corrente preservando i dispositivi audio"""
        try:
            # Carica config esistente per preservare i dispositivi
            config = self.load_config_dict()
            
            # Aggiorna clips, hotkeys e cartella clips
            config['clips'] = []
            config['hotkeys'] = {}
            config['clips_folder'] = self.clips_folder  # Salva la cartella personalizzata
            config['clip_pages'] = self.clip_pages  # Salva le pagine delle clip
            
            # Salva le clip e le loro impostazioni
            for clip_name, widget in self.clip_widgets.items():
                if clip_name in self.mixer.clips:
                    clip = self.mixer.clips[clip_name]
                    clip_data = {
                        'name': clip_name,
                        'path': clip.file_path,
                        'volume': clip.volume,
                        'hotkey': self.hotkey_bindings.get(clip_name, None)
                    }
                    config['clips'].append(clip_data)
            
            # Salva nel file JSON (preservando audio_output_device e secondary_output_device)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Errore nel salvataggio configurazione: {e}")
    
    def load_config(self):
        """Carica la configurazione salvata"""
        loaded_files = set()  # Traccia i file già caricati
        
        # Prima carica dalla configurazione salvata
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Carica pagine clip
                self.clip_pages = config.get('clip_pages', {})
                
                # Carica le clip dal config
                for clip_data in config.get('clips', []):
                    file_path = clip_data['path']
                    
                    # Verifica che il file esista ancora
                    if not os.path.exists(file_path):
                        continue
                    
                    clip_name = clip_data['name']
                    loaded_files.add(file_path)  # Segna come caricato
                    
                    try:
                        # Crea clip
                        clip = AudioClip(file_path, clip_name)
                        clip.volume = clip_data.get('volume', 1.0)
                        self.mixer.add_clip(clip)
                        
                        # Crea widget
                        row = len(self.clip_widgets) // 3
                        col = len(self.clip_widgets) % 3
                        
                        clip_widget = ClipButton(
                            self.clips_container,
                            clip_name,
                            on_play=self.play_clip,
                            on_stop=self.stop_clip,
                            on_remove=self.remove_clip,
                            on_volume_change=self.set_clip_volume,
                            on_hotkey_change=self.start_hotkey_assignment,
                            app=self
                        )
                        clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                        clip_widget.volume_slider.set(clip.volume * 100)
                        
                        self.clip_widgets[clip_name] = clip_widget
                        
                        # Ripristina hotkey se presente
                        hotkey = clip_data.get('hotkey')
                        if hotkey:
                            try:
                                if hotkey.startswith('combo_scan_'):
                                    # Combinazione con numpad (es: combo_scan_71_shift)
                                    parts = hotkey.split('_')
                                    scan_code = int(parts[2])
                                    modifiers = parts[3:] if len(parts) > 3 else []
                                    
                                    def callback(e, name=clip_name, mods=modifiers):
                                        if e.event_type == 'down':
                                            all_pressed = all(keyboard.is_pressed(mod) for mod in mods)
                                            if all_pressed:
                                                self.trigger_clip_hotkey(name)
                                    
                                    hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
                                    self.hotkey_bindings[clip_name] = hotkey
                                    self.hotkey_hooks[clip_name] = hook_ref
                                    
                                    # Mostra nome leggibile
                                    numpad_names = {71: 'Numpad 7', 72: 'Numpad 8', 73: 'Numpad 9',
                                                    75: 'Numpad 4', 76: 'Numpad 5', 77: 'Numpad 6',
                                                    79: 'Numpad 1', 80: 'Numpad 2', 81: 'Numpad 3',
                                                    82: 'Numpad 0', 83: 'Numpad .'}
                                    display = '+'.join(modifiers + [numpad_names.get(scan_code, f'Scan {scan_code}').lower()])
                                    clip_widget.set_hotkey(display)
                                    
                                elif hotkey.startswith('scan_'):
                                    # Numpad singolo
                                    scan_code = int(hotkey.split('_')[1])
                                    
                                    def callback(e, name=clip_name):
                                        if e.event_type == 'down':
                                            # Non triggerare se ci sono modificatori premuti
                                            if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                                                self.trigger_clip_hotkey(name)
                                    
                                    hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
                                    self.hotkey_bindings[clip_name] = hotkey
                                    self.hotkey_hooks[clip_name] = hook_ref
                                    clip_widget.set_hotkey(self._get_numpad_display_name(scan_code))
                                    
                                elif hotkey.startswith('key_'):
                                    # Tasto singolo normale
                                    key_name = hotkey.replace('key_', '')
                                    
                                    def callback(e, name=clip_name):
                                        if e.event_type == 'down':
                                            # Non triggerare se ci sono modificatori premuti
                                            if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                                                self.trigger_clip_hotkey(name)
                                    
                                    hook_ref = keyboard.hook_key(key_name, callback, suppress=False)
                                    self.hotkey_bindings[clip_name] = hotkey
                                    self.hotkey_hooks[clip_name] = hook_ref
                                    clip_widget.set_hotkey(key_name)
                                    
                                else:
                                    # Combinazione normale o vecchio formato
                                    keyboard.add_hotkey(hotkey, self._make_hotkey_callback(clip_name), suppress=False)
                                    self.hotkey_bindings[clip_name] = hotkey
                                    self.hotkey_hooks[clip_name] = hotkey  # Per add_hotkey usiamo la stringa
                                    clip_widget.set_hotkey(hotkey)
                            except Exception as e:
                                logger.error(f"Errore ripristino hotkey {hotkey}: {e}", exc_info=True)
                                
                    except Exception as e:
                        print(f"Errore nel caricamento clip {clip_name}: {e}")
                        
            except Exception as e:
                print(f"Errore nel caricamento configurazione: {e}")
        
        # Poi carica tutti i file dalla cartella clips/ non ancora caricati
        clips_dir = self.clips_folder
        if os.path.exists(clips_dir):
            try:
                for filename in os.listdir(clips_dir):
                    if filename.endswith(('.mp3', '.wav', '.ogg', '.flac')):
                        file_path = os.path.join(clips_dir, filename)
                        
                        # Salta se già caricato dal config
                        if file_path in loaded_files:
                            continue
                        
                        try:
                            # Crea clip
                            clip = AudioClip(file_path, filename)
                            self.mixer.add_clip(clip)
                            
                            # Crea widget
                            row = len(self.clip_widgets) // 3
                            col = len(self.clip_widgets) % 3
                            
                            clip_widget = ClipButton(
                                self.clips_container,
                                filename,
                                on_play=self.play_clip,
                                on_stop=self.stop_clip,
                                on_remove=self.remove_clip,
                                on_volume_change=self.set_clip_volume,
                                on_hotkey_change=self.start_hotkey_assignment,
                                app=self
                            )
                            clip_widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                            
                            self.clip_widgets[filename] = clip_widget
                            
                        except Exception as e:
                            print(f"Errore nel caricamento clip {filename}: {e}")
                            
            except Exception as e:
                print(f"Errore nella lettura cartella clips: {e}")
        
        # Imposta le pagine per le clip caricate
        for clip_name, widget in self.clip_widgets.items():
            page_num = self.clip_pages.get(clip_name, 1)
            widget.set_page(page_num)
        
        # Aggiorna la visibilità delle clip in base alla pagina corrente
        self.update_clips_visibility()
        
        # Salva la configurazione aggiornata (include i nuovi file dalla cartella clips)
        if len(self.clip_widgets) > 0:
            self.save_config()


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
        
        # Get devices
        self.devices = pro_mixer.get_available_devices()
        
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
        
        for i in range(1, 4):
            self.create_input_config(scroll, f"HW{i}", f"Hardware {i}")
        
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
    
    def assign_input(self, channel_id, device_str):
        """Assegna device a input"""
        if device_str == "None":
            return
        
        try:
            # Estrai ID
            device_id = int(device_str.split("]")[0].replace("[", ""))
            
            # Avvia input
            success = self.pro_mixer.start_input(channel_id, device_id)
            
            if success:
                messagebox.showinfo("✓ Configurato", f"{channel_id} collegato al dispositivo {device_id}")
            else:
                messagebox.showerror("✗ Errore", "Impossibile avviare input")
        except Exception as e:
            messagebox.showerror("Errore", str(e))
    
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
            
            messagebox.showinfo("✓ Configurato", f"Bus {bus_name} → Device {device_id}\n\nRicorda di avviare il mixer!")
        except Exception as e:
            messagebox.showerror("Errore", str(e))


if __name__ == "__main__":
    app = AudioMixerApp()
    app.mainloop()
