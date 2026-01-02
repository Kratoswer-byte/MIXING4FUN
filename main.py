"""
Audio Mixer - Interfaccia Grafica Moderna con Hotkeys per Gaming
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
import os
import sys
import logging
import time
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

# Import moduli UI
from ui.colors import COLORS
from ui.clip_button import ClipButton
from ui.config_windows import MixerConfigWindow

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


# ===== CLASSE PRINCIPALE APPLICAZIONE =====

class AudioMixerApp(ctk.CTk):
    """Applicazione principale"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🎮 Gaming Soundboard - Mix Mic + Clip")
        self.geometry("1920x1200")  # Dimensione maggiore per mostrare tutti i canali del mixer completi
        self.minsize(1600, 1000)  # Dimensione minima per evitare canali tagliati
        
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
        
        # Cartella YouTube downloads
        self.youtube_folder = saved_config.get('youtube_folder', os.path.join(self.base_dir, "youtube_downloads"))
        if not os.path.exists(self.youtube_folder):
            os.makedirs(self.youtube_folder)
        
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
        
        # ProMixer (mixer professionale multi-canale)
        print(f"🎛️ Inizializzazione ProMixer integrato...")
        
        # Rileva sample rate del dispositivo primario
        primary_sr = 48000  # Default
        if output_device is not None:
            try:
                primary_dev_info = devices[output_device]
                primary_sr = int(primary_dev_info.get('default_samplerate', 48000))
                print(f"   Sample rate rilevato dal dispositivo primario: {primary_sr} Hz")
            except:
                print(f"   Uso sample rate default: {primary_sr} Hz")
        
        # Buffer 1024 per stabilità audio (riduce scricchiolii)
        # Latenza: ~21ms @ 48kHz (accettabile per streaming/Discord)
        self.pro_mixer = ProMixer(sample_rate=primary_sr, buffer_size=1024)
        self.pro_mixer_widgets = {}  # Widgets mixer tab
        self.pro_mixer_running = False
        
        # Configura bus del ProMixer
        self.pro_mixer.set_bus_device('A1', output_device if output_device else 61)  # CABLE o default
        
        # Valida secondary device prima di usarlo
        if secondary_output_device:
            try:
                dev_info = devices[secondary_output_device]
                if dev_info['max_output_channels'] > 0:
                    self.pro_mixer.set_bus_device('A2', secondary_output_device)  # Cuffie
                    print(f"✓ Bus A2 (Cuffie): Device {secondary_output_device} ({dev_info['name']})")
                else:
                    print(f"⚠ Device {secondary_output_device} non è un output valido, uso solo A1")
                    secondary_output_device = None
            except:
                print(f"⚠ Device {secondary_output_device} non valido, uso solo A1")
                secondary_output_device = None
        
        # Routing: Soundboard va su entrambi i bus A1 e A2
        self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A1', True)
        if secondary_output_device:
            self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A2', True)
        
        print(f"✓ Bus A1 (CABLE/Discord): Device {output_device if output_device else 61}")
        
        # Mixer audio (soundboard) - integrato con ProMixer
        print(f"🎛️ Inizializzazione soundboard (integrata con ProMixer)...")
        self.mixer = AudioMixer(
            sample_rate=primary_sr,  # Usa lo stesso sample rate del ProMixer
            buffer_size=1024,  # Buffer 1024 per stabilità
            virtual_output_callback=lambda audio: None  # Callback per ProMixer
        )
        
        # Collega il mixer direttamente al canale SOUNDBOARD (pull invece di push)
        self.pro_mixer.channels['SOUNDBOARD'].audio_source = self.mixer
        print("✓ AudioMixer collegato al canale SOUNDBOARD (modalità pull)")
        
        self.clip_widgets: Dict[str, ClipButton] = {}
        self.waiting_for_hotkey = None
        self.hotkey_bindings = {}
        self.hotkey_hooks = {}  # Salva i riferimenti agli hook per rimuoverli correttamente
        self.soundboard_enabled = True  # Stato abilitazione soundboard
        self.loop_enabled = False  # Stato loop globale
        self.temp_listener = None  # Listener temporaneo per assegnazione hotkey
        
        # Sistema pagine soundboard
        self.current_page = 1
        self.total_pages = 5  # F1-F5
        self.clip_pages = {}  # {clip_name: page_number}
        
        # Recording state
        self.is_recording = False
        
        # YouTube Downloader
        self.youtube_downloader = YouTubeDownloader(self, self._add_downloaded_clip, COLORS, self.clips_folder, self.youtube_folder)
        
        # Configurazione griglia
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create tabview for main content
        self.tabview = ctk.CTkTabview(self, width=900)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Aggiungi callback per cambio tab
        self.tabview.configure(command=self._on_tab_change)
        
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
        
        # Avvia ProMixer
        print("\n🎛️ Avvio ProMixer...")
        self.pro_mixer.start_all()
        self.pro_mixer_running = True
        
        # Avvia mixer soundboard
        self.mixer.start()
        
        # Avvia aggiornamento VU meter
        self.after(100, self.update_meters)
        
        # Carica configurazione salvata
        self.load_config()
        
        # Ripristina configurazione ProMixer dopo il caricamento
        self.restore_promixer_config()
        
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
        
        # Registra hotkey per toggle loop soundboard (*)
        # Usa hook_key per compatibilità con i giochi
        try:
            def asterisk_callback(e):
                if e.event_type == 'down':
                    self.toggle_soundboard_loop()
            keyboard.hook_key('*', asterisk_callback, suppress=False)
            logger.info("Hotkey loop registrato: * = Toggle Loop Soundboard")
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
            text="Premi * per toggle loop",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 10))
        
        # Libreria YouTube
        self.youtube_downloader.create_library_in_sidebar(self.sidebar, row=7)
        
        # Info
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info_frame.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="s")
        
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
        pages_frame.grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
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
                        clip = AudioClip(file_path, filename, target_sample_rate=self.mixer.sample_rate)
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
        """Riordina le clip in TUTTE le pagine rimuovendo spazi vuoti"""
        logger.info("Riordinamento clips in tutte le pagine F1-F5...")
        
        try:
            # Raggruppa clip per pagina
            pages_clips = {1: [], 2: [], 3: [], 4: [], 5: []}
            for clip_name, widget in self.clip_widgets.items():
                clip_page = self.clip_pages.get(clip_name, 1)
                pages_clips[clip_page].append((clip_name, widget))
            
            # Riordina ogni pagina
            for page_num, clips_list in pages_clips.items():
                for index, (clip_name, widget) in enumerate(clips_list):
                    row = index // 3
                    col = index % 3
                    widget.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    # Nascondi widget se non è la pagina corrente
                    if page_num != self.current_page:
                        widget.grid_remove()
            
            total_clips = sum(len(clips) for clips in pages_clips.values())
            logger.info(f"✓ Riordinate {total_clips} clip in tutte le pagine")
            
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
            to=200,
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
            to=200,
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
        
        # Loop Controls
        loop_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        loop_frame.grid(row=0, column=4, padx=15, pady=15, sticky="ew")
        
        ctk.CTkLabel(
            loop_frame,
            text="🔁 Loop",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        ).pack(anchor="w")
        
        self.loop_soundboard_btn = ctk.CTkButton(
            loop_frame,
            text="🔁 Loop Soundboard (*)",
            command=self.toggle_soundboard_loop,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_secondary"],
            height=40
        )
        self.loop_soundboard_btn.pack(fill="x", pady=(10, 5))
        
        # Registrazione
        rec_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        rec_frame.grid(row=0, column=5, padx=15, pady=15, sticky="ew")
        
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
                clip = AudioClip(file_path, clip_name, target_sample_rate=self.mixer.sample_rate)
                
                # Applica stato loop globale se attivo
                clip.is_looping = self.loop_enabled
                
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
                
                # Aggiorna lista clip nel mixer
                self.update_mixer_clips_list()
                
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
            
            # Aggiorna bottone nel mixer se esiste
            if hasattr(self, 'mixer_clip_buttons') and clip_name in self.mixer_clip_buttons:
                btn = self.mixer_clip_buttons[clip_name]
                btn.configure(text="▶", fg_color=COLORS["success"], hover_color="#059669")
    
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
            
            # Aggiorna lista clip nel mixer
            self.update_mixer_clips_list()
            
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
    
    def toggle_soundboard_loop(self):
        """Attiva/disattiva loop globale per tutte le clip della soundboard"""
        self.loop_enabled = not self.loop_enabled
        
        # Applica lo stato loop a tutte le clip
        for clip_name, clip in self.mixer.clips.items():
            clip.is_looping = self.loop_enabled
        
        # Aggiorna UI del bottone
        if self.loop_enabled:
            self.loop_soundboard_btn.configure(
                text="🔁 Loop ON (*)",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"]
            )
            # Aggiorna sidebar
            self.loop_label.configure(
                text="🔁 Loop: ON",
                text_color=COLORS["accent"]
            )
        else:
            self.loop_soundboard_btn.configure(
                text="🔁 Loop Soundboard (*)",
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["bg_secondary"]
            )
            # Aggiorna sidebar
            self.loop_label.configure(
                text="🔁 Loop: OFF",
                text_color=COLORS["text_muted"]
            )
    
    def on_bass_changed(self, value):
        """Callback per bass boost"""
        bass_pct = int(value - 100)
        self.bass_label.configure(text=f"Bass Boost: {bass_pct:+d}%")
        self.mixer.bass_boost = value / 100.0
    
    def toggle_recording(self):
        """Avvia/ferma la registrazione dall'output A1 (Discord/streaming)"""
        if not self.is_recording:
            # Usa ProMixer invece di AudioMixer per registrare
            self.pro_mixer.start_recording('A1')
            self.is_recording = True
            self.record_btn.configure(
                text="⏹ Ferma Registrazione",
                fg_color="#ff0000"
            )
            messagebox.showinfo("🔴 Registrazione", "Registrazione avviata da bus A1\n(Discord/Streaming output)")
        else:
            output_file = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")],
                initialfile=f"recording_{int(time.time())}.wav"
            )
            
            if output_file:
                self.pro_mixer.stop_recording(output_file)
                messagebox.showinfo("✓ Registrazione", f"File salvato:\n{output_file}")
            else:
                # Salva comunque con nome default
                default_name = f"recording_{int(time.time())}.wav"
                self.pro_mixer.stop_recording(default_name)
                messagebox.showinfo("✓ Registrazione", f"File salvato:\n{default_name}")
            
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
                    clip = AudioClip(file_path, file, target_sample_rate=self.mixer.sample_rate)
                    
                    # Applica stato loop globale se attivo
                    clip.is_looping = self.loop_enabled
                    
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
            text="🔊 Configurazione Bus Output A1/A2 (Mixer + Soundboard)",
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
            text="📤 Bus A1 - Output Primario (Discord/Streaming)",
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
            text="🎧 Bus A2 - Output Secondario (Monitor/Cuffie)",
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
        
        # Checkbox Avvio Automatico
        startup_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        startup_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        self.autostart_var = ctk.BooleanVar(value=self.check_autostart())
        self.autostart_check = ctk.CTkCheckBox(
            startup_frame,
            text="🚀 Avvia automaticamente con Windows",
            variable=self.autostart_var,
            command=self.toggle_autostart,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.autostart_check.grid(row=0, column=0, pady=15, padx=15, sticky="w")
        
        # Pulsanti azione
        buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=20, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        self.apply_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ APPLICA CONFIGURAZIONE",
            command=self.apply_audio_settings,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.apply_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Pulsante rilevamento sample rate
        self.detect_samplerate_btn = ctk.CTkButton(
            buttons_frame,
            text="🔍 RILEVA SAMPLE RATE",
            command=self.detect_and_fix_samplerates,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["warning"],
            hover_color="#d97706"
        )
        self.detect_samplerate_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        # Sample Rate Override
        sr_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        sr_frame.grid(row=4, column=0, pady=10, sticky="ew")
        sr_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            sr_frame,
            text="🎚️ Sample Rate Processing (se hai problemi audio):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, pady=15, padx=15, sticky="w")
        
        sr_buttons = ctk.CTkFrame(sr_frame, fg_color="transparent")
        sr_buttons.grid(row=0, column=1, pady=15, padx=15, sticky="e")
        
        ctk.CTkButton(
            sr_buttons,
            text="44100 Hz",
            width=100,
            height=35,
            command=lambda: self.set_processing_samplerate(44100),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=5)
        
        ctk.CTkButton(
            sr_buttons,
            text="48000 Hz",
            width=100,
            height=35,
            command=lambda: self.set_processing_samplerate(48000),
            fg_color=COLORS["success"],
            hover_color="#059669",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(
            sr_buttons,
            text="96000 Hz",
            width=100,
            height=35,
            command=lambda: self.set_processing_samplerate(96000),
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=2, padx=5)
        
        # Pulsante per aprire impostazioni Windows
        ctk.CTkButton(
            sr_buttons,
            text="⚙️ Windows",
            width=100,
            height=35,
            command=self.open_windows_audio_settings,
            fg_color=COLORS["warning"],
            hover_color="#d97706",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=3, padx=5)
        
        # Label processing rate
        self.processing_sr_label = ctk.CTkLabel(
            sr_frame,
            text=f"Processing interno: {self.pro_mixer.sample_rate} Hz",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.processing_sr_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=15, sticky="w")
        
        # Buffer Size Control (Latenza)
        latency_frame = ctk.CTkFrame(sr_frame, fg_color="transparent")
        latency_frame.grid(row=2, column=0, columnspan=2, pady=(10, 15), padx=15, sticky="ew")
        
        ctk.CTkLabel(
            latency_frame,
            text="⚡ Latenza:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        ).grid(row=0, column=0, padx=(0, 10))
        
        # Pulsanti latenza
        latency_presets = [
            ("Ultra Bassa (128)", 128, "Richiede CPU potente"),
            ("Bassa (256)", 256, "Bilanciata"),
            ("Normale (512)", 512, "Stabile"),
            ("Alta (1024)", 1024, "Massima stabilità")
        ]
        
        for idx, (label, buffer_val, tooltip) in enumerate(latency_presets):
            btn = ctk.CTkButton(
                latency_frame,
                text=label,
                width=120,
                height=30,
                command=lambda b=buffer_val: self.set_buffer_size(b),
                fg_color=COLORS["success"] if buffer_val == 512 else COLORS["bg_secondary"],
                hover_color="#059669" if buffer_val == 512 else COLORS["accent_hover"],
                font=ctk.CTkFont(size=11)
            )
            btn.grid(row=0, column=idx+1, padx=3)
        
        # Calcola e mostra latenza attuale
        latency_ms = (self.pro_mixer.buffer_size / self.pro_mixer.sample_rate) * 1000
        self.latency_label = ctk.CTkLabel(
            latency_frame,
            text=f"({latency_ms:.1f}ms @ {self.pro_mixer.sample_rate}Hz)",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        self.latency_label.grid(row=0, column=5, padx=10)
        
        ctk.CTkLabel(
            sr_frame,
            text="ℹ️ Cambia solo se l'audio è distorto/robotico. I bus useranno sempre il sample rate nativo dei dispositivi.",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            wraplength=700,
            justify="left"
        ).grid(row=2, column=0, columnspan=2, pady=(0, 15), padx=15, sticky="w")
        
        # Info box
        info_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_card"])
        info_frame.grid(row=4, column=0, pady=10, sticky="ew")
        
        info_text = """💡 CONFIGURAZIONE BUS A1/A2 (MIXER + SOUNDBOARD):

📤 Bus A1 - Output Primario (obbligatorio):
   • Corrisponde al Bus A1 del Mixer Professionale
   • Seleziona "CABLE Input" per inviare a Discord/Streaming
   • Usato per soundboard E mixer

🎧 Bus A2 - Output Secondario (opzionale):
   • Corrisponde al Bus A2 del Mixer Professionale
   • Seleziona le tue cuffie per monitoraggio diretto
   • L'audio sarà inviato CONTEMPORANEAMENTE a A1 e A2

🎛️ Integrazione Mixer:
   • Questi bus sono condivisi tra Soundboard e Mixer
   • Configurali anche nel tab 🎛️ Mixer per routing avanzato

⚡ Raccomandazione:
   • Bus A1: CABLE Input (VB-Audio Virtual Cable) 48kHz
   • Bus A2: Headphones (Realtek HD Audio) o le tue cuffie"""
        
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
    
    def set_buffer_size(self, new_buffer_size: int):
        """Cambia il buffer size per ridurre la latenza"""
        try:
            current_buffer = self.pro_mixer.buffer_size
            
            if current_buffer == new_buffer_size:
                messagebox.showinfo("Buffer Size", f"Buffer già impostato a {new_buffer_size} samples!")
                return
            
            # Calcola latenza
            old_latency = (current_buffer / self.pro_mixer.sample_rate) * 1000
            new_latency = (new_buffer_size / self.pro_mixer.sample_rate) * 1000
            
            # Chiedi conferma
            msg = (
                f"Cambiare buffer size (latenza)?\n\n"
                f"Attuale: {current_buffer} samples ({old_latency:.1f}ms)\n"
                f"Nuovo: {new_buffer_size} samples ({new_latency:.1f}ms)\n\n"
            )
            
            if new_buffer_size < 256:
                msg += "⚠️ ULTRA BASSA LATENZA:\n• Richiede CPU potente\n• Possibili glitch audio se CPU sovraccarica\n\n"
            elif new_buffer_size == 256:
                msg += "✓ BASSA LATENZA:\n• Buon compromesso\n• Adatta a gaming e streaming\n\n"
            elif new_buffer_size == 512:
                msg += "✓ NORMALE:\n• Latenza bilanciata\n• Buona stabilità\n\n"
            else:
                msg += "✓ ALTA STABILITÀ:\n• Latenza maggiore ma audio stabile\n• Usa se hai glitch audio\n\n"
            
            msg += "Il mixer verrà riavviato."
            
            result = messagebox.askyesno("Cambia Buffer Size", msg)
            if not result:
                return
            
            print(f"🔄 Cambio buffer size: {current_buffer} → {new_buffer_size} samples")
            
            # Ferma tutti gli stream
            was_running = self.pro_mixer_running
            active_buses = []
            
            if was_running:
                print(f"   Fermando bus attivi...")
                for bus_name, bus in self.pro_mixer.buses.items():
                    if bus.stream and bus.device_id is not None:
                        try:
                            bus.stream.stop()
                            bus.stream.close()
                            bus.stream = None
                            active_buses.append(bus_name)
                            print(f"   ✓ Bus {bus_name} fermato")
                        except:
                            pass
            
            # Cambia buffer size
            self.pro_mixer.buffer_size = new_buffer_size
            self.mixer.buffer_size = new_buffer_size
            print(f"   ✓ Buffer size aggiornato: {new_buffer_size} samples")
            
            # Riavvia bus attivi
            if was_running and active_buses:
                print(f"   Riavvio bus con nuovo buffer size...")
                for bus_name in active_buses:
                    try:
                        self.pro_mixer.start_output(bus_name)
                        print(f"   ✓ Bus {bus_name} riavviato")
                    except Exception as e:
                        print(f"   ✗ Errore riavvio Bus {bus_name}: {e}")
            
            # Aggiorna label latenza
            latency_ms = (new_buffer_size / self.pro_mixer.sample_rate) * 1000
            self.latency_label.configure(text=f"({latency_ms:.1f}ms @ {self.pro_mixer.sample_rate}Hz)")
            
            msg_result = f"✓ Buffer size: {new_buffer_size} samples\n✓ Latenza: {latency_ms:.1f}ms @ {self.pro_mixer.sample_rate}Hz\n\n"
            
            if was_running and active_buses:
                msg_result += f"✓ Bus audio riavviati: {', '.join(active_buses)}\n\n"
            
            msg_result += "Testa l'audio. Se senti glitch/interruzioni,\naumenta il buffer size."
            
            messagebox.showinfo("Buffer Size Aggiornato", msg_result)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore cambio buffer size:\n{str(e)}")
            print(f"❌ Errore set_buffer_size: {e}")
    
    def open_windows_audio_settings(self):
        """Apre le impostazioni audio di Windows con istruzioni"""
        import subprocess
        
        msg = (
            "🔧 CAMBIO SAMPLE RATE DISPOSITIVO WINDOWS\n\n"
            "Il sample rate dei dispositivi è configurato in Windows.\n"
            "Per cambiarlo:\n\n"
            "1️⃣ Sto aprendo le Impostazioni Audio di Windows...\n"
            "2️⃣ Nella finestra che si aprirà:\n"
            "   • Scorri in basso e clicca su 'Altre impostazioni audio'\n"
            "   • Oppure clicca su 'Proprietà dispositivo'\n\n"
            "3️⃣ Vai sulla scheda 'Avanzate'\n"
            "4️⃣ Nel menu a tendina 'Formato predefinito':\n"
            "   • Seleziona il sample rate desiderato (44100, 48000, 96000 Hz)\n"
            "   • Clicca 'Applica' e poi 'OK'\n\n"
            "5️⃣ Torna qui e clicca 'Rileva Sample Rate' per verificare.\n\n"
            "⚠️ NOTA IMPORTANTE:\n"
            "I pulsanti 44100/48000/96000 Hz cambiano solo il PROCESSING\n"
            "interno del mixer (con resampling automatico).\n"
            "Per prestazioni ottimali, il sample rate di Windows dovrebbe\n"
            "coincidere con quello del processing."
        )
        
        result = messagebox.showinfo("Cambia Sample Rate Windows", msg)
        
        # Apri impostazioni audio Windows
        try:
            subprocess.Popen('control mmsys.cpl sounds')
        except:
            try:
                subprocess.Popen('ms-settings:sound')
            except:
                messagebox.showerror("Errore", "Impossibile aprire le impostazioni audio di Windows.\nAprile manualmente dal menu Start.")
    
    def set_processing_samplerate(self, new_samplerate: int):
        """Cambia il sample rate - richiede che anche i device Windows usino lo stesso SR"""
        try:
            current_sr = self.pro_mixer.sample_rate
            
            if current_sr == new_samplerate:
                messagebox.showinfo("Sample Rate", f"Il sistema usa già {new_samplerate} Hz!")
                return
            
            # Avvisa che serve cambiare anche Windows
            result = messagebox.askyesno(
                "Cambia Sample Rate Sistema",
                f"⚠️ IMPORTANTE: Cambiare il sample rate richiede\n"
                f"che ANCHE i dispositivi Windows siano configurati\n"
                f"allo stesso sample rate!\n\n"
                f"Attuale: {current_sr} Hz\n"
                f"Nuovo: {new_samplerate} Hz\n\n"
                f"📋 PROCEDURA CONSIGLIATA:\n"
                f"1. Clicca '⚙️ Windows' qui sopra\n"
                f"2. Cambia il sample rate del dispositivo a {new_samplerate} Hz\n"
                f"3. Torna qui e cambia il sample rate\n"
                f"4. Riavvia il mixer\n\n"
                f"⚠️ Se i sample rate non coincidono, l'audio\n"
                f"sarà distorto o non funzionerà.\n\n"
                f"Procedere comunque?"
            )
            
            if not result:
                return
            
            print(f"🔄 Cambio sample rate processing: {current_sr} Hz → {new_samplerate} Hz")
            print(f"   ProMixer attuale: {self.pro_mixer.sample_rate} Hz")
            print(f"   Soundboard attuale: {self.mixer.sample_rate} Hz")
            
            # Se il mixer è attivo, ferma tutti gli stream prima di cambiare
            was_running = self.pro_mixer_running
            active_buses = []
            
            if was_running:
                print(f"   Fermando bus attivi...")
                for bus_name, bus in self.pro_mixer.buses.items():
                    if bus.stream and bus.device_id is not None:
                        try:
                            bus.stream.stop()
                            bus.stream.close()
                            bus.stream = None
                            active_buses.append(bus_name)
                            print(f"   ✓ Bus {bus_name} fermato")
                        except:
                            pass
            
            # Aggiorna sample rate interno
            self.pro_mixer.sample_rate = new_samplerate
            self.mixer.sample_rate = new_samplerate
            print(f"   ✓ Sample rate processing aggiornato: {new_samplerate} Hz")
            print(f"   ProMixer dopo cambio: {self.pro_mixer.sample_rate} Hz")
            print(f"   Soundboard dopo cambio: {self.mixer.sample_rate} Hz")
            
            # Aggiorna sample rate anche nei canali del ProMixer
            for channel_id, channel in self.pro_mixer.channels.items():
                channel.sample_rate = new_samplerate
                print(f"   ✓ Canale {channel_id} sample_rate aggiornato")
            
            # Aggiorna sample rate nei bus del ProMixer
            for bus_name, bus in self.pro_mixer.buses.items():
                bus.sample_rate = new_samplerate
                print(f"   ✓ Bus {bus_name} sample_rate aggiornato")
            
            # Riavvia i bus che erano attivi
            if was_running and active_buses:
                print(f"   Riavvio bus con nuovo sample rate...")
                for bus_name in active_buses:
                    bus = self.pro_mixer.buses[bus_name]
                    if bus.device_id is not None:
                        success = self.pro_mixer.start_output(bus_name)
                        if success:
                            print(f"   ✓ Bus {bus_name} riavviato")
                        else:
                            print(f"   ✗ Errore riavvio Bus {bus_name}")
            
            # Aggiorna label
            self.processing_sr_label.configure(text=f"Processing interno: {new_samplerate} Hz")
            
            msg = f"✓ Processing interno: {new_samplerate} Hz\n\n"
            if was_running and active_buses:
                msg += f"✅ Bus audio riavviati:\n"
                for bus_name in active_buses:
                    bus = self.pro_mixer.buses[bus_name]
                    if bus.stream:
                        msg += f"   • {bus_name} @ {bus.sample_rate} Hz\n"
                msg += "\n💡 Ogni bus usa il proprio sample rate nativo."
            else:
                msg += "ℹ️ Mixer non attivo.\n"
                msg += "Avvia il mixer per applicare il nuovo sample rate."
            
            msg += "\n\nProva a riprodurre audio per verificare."
            
            messagebox.showinfo("Sample Rate Aggiornato", msg)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore cambio sample rate:\n{str(e)}")
            print(f"❌ Errore set_processing_samplerate: {e}")
    
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
    
    def detect_and_fix_samplerates(self):
        """Rileva sample rate dei dispositivi configurati e li allinea"""
        try:
            devices = sd.query_devices()
            
            # Ottieni device ID correnti
            primary_choice = self.primary_output_var.get()
            secondary_choice = self.secondary_output_var.get()
            
            if primary_choice == "Nessuno":
                messagebox.showwarning("Attenzione", "Seleziona prima un dispositivo Bus A1 (Primary Output)!")
                return
            
            primary_device = None
            secondary_device = None
            
            try:
                primary_device = int(primary_choice.split(']')[0][1:])
            except:
                messagebox.showerror("Errore", "Dispositivo primario non valido!")
                return
            
            if self.enable_secondary_var.get() and secondary_choice != "Nessuno":
                try:
                    secondary_device = int(secondary_choice.split(']')[0][1:])
                except:
                    secondary_device = None
            
            # Rileva sample rate
            info_text = "🔍 RILEVAMENTO SAMPLE RATE:\n\n"
            info_text += f"🎛️ ProMixer: {self.pro_mixer.sample_rate} Hz\n\n"
            
            # Bus A1 - Sample rate nativo del dispositivo
            dev1 = devices[primary_device]
            sr1_native = int(dev1.get('default_samplerate', 48000))
            info_text += f"📤 Bus A1 (Primary):\n"
            info_text += f"   Device: {dev1['name']}\n"
            info_text += f"   Sample Rate Nativo: {sr1_native} Hz\n"
            info_text += f"   Canali: {dev1['max_output_channels']}\n"
            
            # Mostra sample rate EFFETTIVO se il bus è attivo
            bus_a1 = self.pro_mixer.buses['A1']
            if bus_a1.stream and hasattr(bus_a1, 'sample_rate'):
                sr1_actual = bus_a1.sample_rate
                info_text += f"   Sample Rate Stream: {sr1_actual} Hz"
                if sr1_actual == sr1_native == self.pro_mixer.sample_rate:
                    info_text += f" ✅ PERFETTO!"
                elif sr1_actual == sr1_native:
                    info_text += f" ✓"
                else:
                    info_text += f" ⚠️ ERRORE!"
            else:
                info_text += f"   Status: Non attivo"
            info_text += "\n\n"
            
            # Bus A2
            if secondary_device is not None:
                dev2 = devices[secondary_device]
                sr2_native = int(dev2.get('default_samplerate', 48000))
                info_text += f"🎧 Bus A2 (Secondary):\n"
                info_text += f"   Device: {dev2['name']}\n"
                info_text += f"   Sample Rate Nativo: {sr2_native} Hz\n"
                info_text += f"   Canali: {dev2['max_output_channels']}\n"
                
                # Mostra sample rate EFFETTIVO
                bus_a2 = self.pro_mixer.buses['A2']
                if bus_a2.stream and hasattr(bus_a2, 'sample_rate'):
                    sr2_actual = bus_a2.sample_rate
                    info_text += f"   Sample Rate Stream: {sr2_actual} Hz"
                    if sr2_actual == sr2_native == self.pro_mixer.sample_rate:
                        info_text += f" ✅ PERFETTO!"
                    elif sr2_actual == sr2_native:
                        info_text += f" ✓"
                    else:
                        info_text += f" ⚠️ ERRORE!"
                else:
                    info_text += f"   Status: Non attivo"
                info_text += "\n\n"
                
                # Verifica compatibilità
                if sr1_native == sr2_native == self.pro_mixer.sample_rate:
                    info_text += f"✅ CONFIGURAZIONE PERFETTA!\n"
                    info_text += f"   Tutti i sample rate a {sr1_native} Hz\n"
                    info_text += f"   Audio ottimale, latenza minima.\n"
                elif sr1_native == sr2_native:
                    info_text += f"⚠️ ATTENZIONE:\n"
                    info_text += f"   ProMixer: {self.pro_mixer.sample_rate} Hz\n"
                    info_text += f"   Dispositivi: {sr1_native} Hz\n\n"
                    info_text += f"❌ I sample rate NON coincidono!\n"
                    info_text += f"   L'audio potrebbe essere distorto.\n\n"
                    info_text += f"💡 Usa '⚙️ Windows' per cambiare il sample rate\n"
                    info_text += f"   dei dispositivi a {self.pro_mixer.sample_rate} Hz"
                else:
                    info_text += f"❌ CONFIGURAZIONE NON VALIDA:\n"
                    info_text += f"   ProMixer: {self.pro_mixer.sample_rate} Hz\n"
                    info_text += f"   Bus A1: {sr1_native} Hz\n"
                    info_text += f"   Bus A2: {sr2_native} Hz\n\n"
                    info_text += f"⚠️ Sample rate diversi causano audio distorto!\n\n"
                    info_text += f"💡 Configura tutti i dispositivi Windows allo\n"
                    info_text += f"   stesso sample rate (usa '⚙️ Windows')"
            else:
                if sr1_native == self.pro_mixer.sample_rate:
                    info_text += f"✅ Sample rate corretto: {sr1_native} Hz\n"
                else:
                    info_text += f"⚠️ ProMixer: {self.pro_mixer.sample_rate} Hz\n"
                    info_text += f"⚠️ Dispositivo: {sr1_native} Hz\n"
                    info_text += f"❌ Sample rate NON coincide!"
            
            messagebox.showinfo("Rilevamento Sample Rate", info_text)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante rilevamento:\n{str(e)}")
            print(f"❌ Errore detect_samplerate: {e}")
    
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
            
            # 🎯 SINCRONIZZAZIONE: Configura i bus del ProMixer (che ora gestisce l'output reale)
            print(f"🎛️ Riconfigurazione bus ProMixer:")
            
            # Bus A1 - Primary Output
            bus_a1 = self.pro_mixer.buses['A1']
            if bus_a1.stream:
                print(f"   Fermando stream esistente Bus A1...")
                bus_a1.stream.stop()
                bus_a1.stream.close()
                bus_a1.stream = None
            
            bus_a1.device_id = primary_device
            print(f"   Bus A1 → Device {primary_device}")
            
            # Se il mixer è attivo, riavvia lo stream A1
            if self.pro_mixer_running:
                self.pro_mixer.start_output('A1')
                print(f"   ✓ Stream Bus A1 riavviato")
            
            # Bus A2 - Secondary Output
            if secondary_device is not None:
                bus_a2 = self.pro_mixer.buses['A2']
                if bus_a2.stream:
                    print(f"   Fermando stream esistente Bus A2...")
                    bus_a2.stream.stop()
                    bus_a2.stream.close()
                    bus_a2.stream = None
                
                bus_a2.device_id = secondary_device
                print(f"   Bus A2 → Device {secondary_device}")
                
                # Abilita routing SOUNDBOARD → A2
                self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A2', True)
                
                # Se il mixer è attivo, riavvia lo stream A2
                if self.pro_mixer_running:
                    self.pro_mixer.start_output('A2')
                    print(f"   ✓ Stream Bus A2 riavviato")
            else:
                # Disabilita routing SOUNDBOARD → A2
                self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A2', False)
                print(f"   Bus A2 disabilitato")
            
            print(f"✓ Bus sincronizzati con ProMixer!")
            
            # Note: Il mixer soundboard ora NON usa più output_device direttamente,
            # ma invia tutto tramite virtual_output_callback al ProMixer
            
            # Messaggio conferma con info sample rate
            devices = sd.query_devices()
            dev1 = devices[primary_device]
            sr1_native = int(dev1.get('default_samplerate', 48000))
            
            msg = f"✓ Bus A1 (Primary Output):\n{dev1['name']}\n"
            msg += f"Sample Rate Nativo: {sr1_native} Hz"
            
            warnings = []
            if secondary_device is not None:
                dev2 = devices[secondary_device]
                sr2_native = int(dev2.get('default_samplerate', 48000))
                msg += f"\n\n✓ Bus A2 (Secondary Output):\n{dev2['name']}\n"
                msg += f"Sample Rate Nativo: {sr2_native} Hz"
                
                # Verifica sample rate matching
                if sr1_native != sr2_native:
                    warnings.append(f"ℹ️ I bus hanno sample rate diversi:")
                    warnings.append(f"   A1={sr1_native}Hz, A2={sr2_native}Hz")
                    warnings.append(f"Ogni bus userà il proprio sample rate nativo.")
                    warnings.append(f"Questo è NORMALE e supportato.")
            
            msg += "\n\n🎛️ I bus del mixer sono stati sincronizzati!"
            msg += f"\n🎚️ ProMixer processing: {self.pro_mixer.sample_rate} Hz"
            
            if warnings:
                msg += "\n\n" + "\n".join(warnings)
            
            if self.pro_mixer_running:
                msg += "\n\n✅ Mixer attivo: nuovi dispositivi pronti!"
            else:
                msg += "\n\n💡 Avvia il mixer dal tab 🎛️ Mixer per usare i nuovi dispositivi."
            
            messagebox.showinfo("Configurazione Applicata", msg)
            
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
        
        self.mute_a1_btn = ctk.CTkButton(
            btn_frame,
            text="🔊 A1 (Discord)",
            width=140,
            height=40,
            fg_color=COLORS["success"],
            hover_color="#059669",
            command=self.toggle_mute_a1,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mute_a1_btn.grid(row=0, column=0, padx=5)
        
        self.mute_a2_btn = ctk.CTkButton(
            btn_frame,
            text="🔊 A2 (Cuffie)",
            width=140,
            height=40,
            fg_color=COLORS["success"],
            hover_color="#059669",
            command=self.toggle_mute_a2,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mute_a2_btn.grid(row=0, column=1, padx=5)
        
        config_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ CONFIGURA",
            width=140,
            height=40,
            command=self.open_mixer_config,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        config_btn.grid(row=0, column=2, padx=5)
        
        # Info sync A1/A2
        info_sync = ctk.CTkLabel(
            header_frame,
            text="ℹ️ Bus A1/A2 sincronizzati con tab 🔊 Audio (Soundboard Output)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        info_sync.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="w")
        
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
        
        # CLIPS Section
        clips_frame = ctk.CTkFrame(mixer_container, fg_color="transparent")
        clips_frame.pack(side="left", fill="y", padx=10)
        
        ctk.CTkLabel(
            clips_frame,
            text="🎵 CLIPS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"]
        ).pack(pady=10)
        
        # Scrollable clips list
        self.mixer_clips_container = ctk.CTkScrollableFrame(
            clips_frame,
            width=250,
            height=600,
            fg_color=COLORS["bg_secondary"],
            corner_radius=10
        )
        self.mixer_clips_container.pack(fill="both", expand=True, pady=5)
        
        # Popolerà dinamicamente quando vengono caricate le clip
        self.update_mixer_clips_list()
        
        # Separator
        sep2 = ctk.CTkFrame(mixer_container, width=3, fg_color=COLORS["border"])
        sep2.pack(side="left", fill="y", padx=20)
        
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
        
        # YouTube Player Section (orizzontale in basso)
        yt_separator = ctk.CTkFrame(self.tab_mixer, height=3, fg_color=COLORS["border"])
        yt_separator.grid(row=2, column=0, sticky="ew", padx=10)
        
        self.create_youtube_player()
    
    def create_youtube_player(self):
        """Crea il Media Player orizzontale nel mixer (usa canale HW3)"""
        yt_frame = ctk.CTkFrame(self.tab_mixer, fg_color=COLORS["bg_secondary"], height=150)
        yt_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        yt_frame.grid_columnconfigure(1, weight=1)
        
        # Label titolo
        ctk.CTkLabel(
            yt_frame,
            text="🎵 Media Player (HW3)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["accent"]
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        # Input URL
        url_container = ctk.CTkFrame(yt_frame, fg_color="transparent")
        url_container.grid(row=1, column=0, columnspan=5, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            url_container,
            text="🔗 Link:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 5))
        
        self.yt_url_entry = ctk.CTkEntry(
            url_container,
            placeholder_text="Inserisci link YouTube...",
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.yt_url_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Selettore formato download
        ctk.CTkLabel(
            url_container,
            text="Formato:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(10, 5))
        
        self.yt_format_menu = ctk.CTkOptionMenu(
            url_container,
            values=["WAV", "MP3"],
            width=80,
            height=35,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_format_menu.set("WAV")
        self.yt_format_menu.pack(side="left", padx=5)
        
        self.yt_load_btn = ctk.CTkButton(
            url_container,
            text="📥 YouTube",
            width=100,
            height=35,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.load_youtube_url,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_load_btn.pack(side="left", padx=5)
        
        self.yt_file_btn = ctk.CTkButton(
            url_container,
            text="📂 File PC",
            width=100,
            height=35,
            fg_color=COLORS["success"],
            hover_color="#059669",
            command=self.load_local_file,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_file_btn.pack(side="left", padx=5)
        
        # Progress bar
        progress_container = ctk.CTkFrame(yt_frame, fg_color="transparent")
        progress_container.grid(row=2, column=0, columnspan=5, padx=15, pady=5, sticky="ew")
        
        self.yt_time_label = ctk.CTkLabel(
            progress_container,
            text="0:00",
            font=ctk.CTkFont(size=11),
            width=50
        )
        self.yt_time_label.pack(side="left", padx=5)
        
        self.yt_progress_slider = ctk.CTkSlider(
            progress_container,
            from_=0,
            to=100,
            command=self.on_media_seek,
            state="disabled"
        )
        self.yt_progress_slider.set(0)
        self.yt_progress_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.yt_duration_label = ctk.CTkLabel(
            progress_container,
            text="0:00",
            font=ctk.CTkFont(size=11),
            width=50
        )
        self.yt_duration_label.pack(side="left", padx=5)
        
        # Controlli playback
        controls_frame = ctk.CTkFrame(yt_frame, fg_color="transparent")
        controls_frame.grid(row=3, column=0, padx=15, pady=10, sticky="w")
        
        self.yt_play_btn = ctk.CTkButton(
            controls_frame,
            text="▶️ PLAY",
            width=80,
            height=35,
            fg_color=COLORS["success"],
            hover_color="#059669",
            command=self.play_youtube,
            state="disabled",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_play_btn.pack(side="left", padx=2)
        
        self.yt_stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹️ STOP",
            width=80,
            height=35,
            fg_color=COLORS["danger"],
            hover_color="#b91c1c",
            command=self.stop_youtube,
            state="disabled",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_stop_btn.pack(side="left", padx=2)
        
        self.yt_loop_btn = ctk.CTkButton(
            controls_frame,
            text="🔁 Loop",
            width=80,
            height=35,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_secondary"],
            command=self.toggle_media_loop,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.yt_loop_btn.pack(side="left", padx=2)
        
        # Volume slider
        vol_frame = ctk.CTkFrame(yt_frame, fg_color="transparent")
        vol_frame.grid(row=3, column=1, padx=15, pady=10, sticky="ew")
        
        ctk.CTkLabel(
            vol_frame,
            text="🔊 Volume:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 5))
        
        self.yt_volume_slider = ctk.CTkSlider(
            vol_frame,
            from_=0,
            to=100,
            width=150,
            command=self.on_youtube_volume_change
        )
        self.yt_volume_slider.set(80)
        self.yt_volume_slider.pack(side="left", padx=5)
        
        self.yt_volume_label = ctk.CTkLabel(
            vol_frame,
            text="80%",
            font=ctk.CTkFont(size=11),
            width=40
        )
        self.yt_volume_label.pack(side="left")
        
        # Info: routing gestito dal canale HW3
        routing_info = ctk.CTkLabel(
            vol_frame,
            text="→ Usa i pulsanti routing del canale HW3 per scegliere l'uscita",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        routing_info.pack(side="left", padx=15)
        
        # Info status
        self.yt_status_label = ctk.CTkLabel(
            yt_frame,
            text="⏸️ Nessun audio caricato",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.yt_status_label.grid(row=0, column=1, columnspan=4, padx=15, pady=(10, 5), sticky="e")
        
        # Variabili stato media player
        self.media_player_audio = None  # Dati audio caricati
        self.media_player_sr = None  # Sample rate
        self.media_player_positions = {}  # Posizioni per ogni bus (come AudioClip)
        self.media_player_playing = False
        self.media_player_looping = False  # Stato loop media player
        self.media_player_duration = 0  # Durata totale in samples
        
        # Avvia aggiornamento progress bar
        self.update_media_progress()
    
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
        strip_frame.channel_id = channel_id  # Salva ID per update meter
        
        # Nome canale
        name_label = ctk.CTkLabel(
            strip_frame,
            text=channel.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        )
        name_label.pack(pady=(10, 5))
        strip_frame.name_label = name_label  # Salva per aggiornamenti
        
        # VU Meter (Canvas)
        meter = Canvas(
            strip_frame,
            width=30,
            height=100,
            bg=COLORS["bg_card"],
            highlightthickness=0
        )
        meter.pack(pady=5)
        # Crea barra di background
        meter.create_rectangle(2, 2, 28, 98, fill=COLORS["bg_card"], outline=COLORS["border"], tags="bg")
        # Crea barra livello (inizialmente vuota)
        meter.create_rectangle(2, 98, 28, 98, fill=COLORS["accent"], tags="level")
        strip_frame.meter = meter  # Salva riferimento
        strip_frame.meter_level = 0.0  # Livello attuale per smooth
        
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
        
        # Pulsante FX (effetti/noise gate)
        fx_btn = ctk.CTkButton(
            controls,
            text="FX",
            width=40,
            height=28,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self.open_channel_fx(channel_id)
        )
        fx_btn.grid(row=0, column=2, padx=2)
        strip_frame.fx_btn = fx_btn
        
        return strip_frame
    
    def create_bus_strip(self, parent, bus_name, bus):
        """Crea uno strip per un bus output"""
        strip_frame = ctk.CTkFrame(
            parent,
            fg_color=COLORS["bg_secondary"],
            corner_radius=10,
            border_width=2,
            border_color=COLORS["accent"],
            width=120,
            height=450
        )
        strip_frame.pack_propagate(False)  # Mantieni dimensioni fisse
        
        # Nome bus
        name_label = ctk.CTkLabel(
            strip_frame,
            text=f"BUS {bus_name}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["accent"]
        )
        name_label.pack(pady=(10, 5))
        
        # Device label - mostra device attuale
        device_name = "No Device"
        if bus.device_id is not None:
            import sounddevice as sd
            try:
                device_info = sd.query_devices(bus.device_id)
                device_name = device_info['name'][:18]
            except:
                device_name = f"Dev {bus.device_id}"
        
        device_label = ctk.CTkLabel(
            strip_frame,
            text=device_name,
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
        strip_frame.fader = fader  # Salva riferimento al fader
        
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
            channel = self.pro_mixer.channels[channel_id]
            channel.set_fader_db(db)
        
        # Aggiorna label dB (sempre, anche senza audio)
        if channel_id in self.mixer_channel_strips:
            strip = self.mixer_channel_strips[channel_id]
            strip.db_label.configure(text=f"{db:.1f} dB")
    
    def update_meters(self):
        """Aggiorna i VU meter di tutti i canali"""
        if not hasattr(self, 'mixer_channel_strips') or not self.pro_mixer_running:
            return
        
        try:
            # Aggiorna meter per ogni canale
            for channel_id, strip in self.mixer_channel_strips.items():
                channel = self.pro_mixer.channels.get(channel_id)
                if not channel:
                    continue
                
                # Aggiorna nome se cambiato
                if hasattr(strip, 'name_label'):
                    current_text = strip.name_label.cget("text")
                    if current_text != channel.name:
                        strip.name_label.configure(text=channel.name)
                
                # Aggiorna meter
                if hasattr(strip, 'meter') and hasattr(channel, 'peak_level'):
                        # Leggi livello dal canale
                        peak_db = channel.peak_level
                        
                        # Converti dB in altezza (da -60dB a 0dB)
                        if peak_db <= -60:
                            height = 0
                        else:
                            # Scala da -60dB (0%) a 0dB (100%)
                            height = int(((peak_db + 60) / 60.0) * 96)
                        
                        # Smooth: media con valore precedente
                        if hasattr(strip, 'meter_level'):
                            height = int(strip.meter_level * 0.7 + height * 0.3)
                        strip.meter_level = height
                        
                        # Colore basato sul livello
                        if peak_db > -3:
                            color = "#ff4444"  # Rosso (clipping)
                        elif peak_db > -6:
                            color = "#ffaa00"  # Arancione
                        elif peak_db > -12:
                            color = "#ffff00"  # Giallo
                        else:
                            color = COLORS["accent"]  # Verde
                        
                        # Aggiorna barra
                        meter = strip.meter
                        y_top = 98 - height
                        meter.coords("level", 2, y_top, 28, 98)
                        meter.itemconfig("level", fill=color)
        except Exception as e:
            pass  # Ignora errori durante update
        
        # Richiama ogni 50ms per 20 FPS
        if self.pro_mixer_running:
            self.after(50, self.update_meters)
    
    def update_mixer_clips_list(self):
        """Aggiorna la lista delle clip nel mixer"""
        if not hasattr(self, 'mixer_clips_container'):
            return
        
        # Cancella tutti i widget esistenti
        for widget in self.mixer_clips_container.winfo_children():
            widget.destroy()
        
        # Se non ci sono clip
        if not self.mixer or not self.mixer.clips:
            ctk.CTkLabel(
                self.mixer_clips_container,
                text="Nessuna clip caricata",
                text_color=COLORS["text_secondary"],
                font=ctk.CTkFont(size=12)
            ).pack(pady=20)
            return
        
        # Crea bottone per ogni clip
        for clip_name, clip in sorted(self.mixer.clips.items()):
            clip_frame = ctk.CTkFrame(
                self.mixer_clips_container,
                fg_color=COLORS["bg_card"],
                corner_radius=8,
                height=45
            )
            clip_frame.pack(fill="x", pady=2, padx=5)
            clip_frame.pack_propagate(False)  # Mantiene altezza fissa
            
            # Grid layout per allineamento perfetto
            clip_frame.grid_columnconfigure(0, weight=1)
            clip_frame.grid_columnconfigure(1, weight=0)
            
            # Nome clip (troncato se troppo lungo)
            display_name = clip_name if len(clip_name) <= 35 else clip_name[:32] + "..."
            name_label = ctk.CTkLabel(
                clip_frame,
                text=display_name,
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=11),
                anchor="w"
            )
            name_label.grid(row=0, column=0, padx=(12, 5), pady=0, sticky="w")
            
            # Bottone play/pause
            play_btn = ctk.CTkButton(
                clip_frame,
                text="▶",
                width=50,
                height=35,
                fg_color=COLORS["success"],
                hover_color="#059669",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda name=clip_name, btn=None: self.toggle_clip_from_mixer(name),
                corner_radius=8
            )
            play_btn.grid(row=0, column=1, padx=(5, 8), pady=5, sticky="e")
            
            # Salva riferimento al bottone per aggiornare lo stato
            if not hasattr(self, 'mixer_clip_buttons'):
                self.mixer_clip_buttons = {}
            self.mixer_clip_buttons[clip_name] = play_btn
    
    def toggle_clip_from_mixer(self, clip_name: str):
        """Toggle play/pause di una clip dal mixer"""
        if clip_name not in self.mixer.clips:
            return
        
        clip = self.mixer.clips[clip_name]
        btn = self.mixer_clip_buttons.get(clip_name)
        
        if clip.is_playing:
            # Ferma
            clip.stop()
            if btn:
                btn.configure(text="▶", fg_color=COLORS["success"], hover_color="#059669")
        else:
            # Avvia
            clip.is_looping = False
            clip.play()
            if btn:
                btn.configure(text="⏸", fg_color=COLORS["warning"], hover_color="#d97706")
    
    def on_bus_fader_change(self, bus_name, value):
        """Callback fader bus"""
        db = float(value)
        if bus_name in self.pro_mixer.buses:
            self.pro_mixer.buses[bus_name].set_fader_db(db)
        
        # Aggiorna label dB
        if bus_name in self.mixer_bus_strips:
            strip = self.mixer_bus_strips[bus_name]
            strip.db_label.configure(text=f"{db:.1f} dB")
        
        # Aggiorna label dB (sempre, anche senza audio)
        if bus_name in self.mixer_bus_strips:
            self.mixer_bus_strips[bus_name].db_label.configure(text=f"{db:.1f} dB")
    
    def toggle_routing(self, channel_id, bus_name):
        """Toggle routing di un canale verso un bus"""
        if channel_id in self.pro_mixer.channels:
            current = self.pro_mixer.channels[channel_id].routing.get(bus_name, False)
            new_state = not current
            self.pro_mixer.set_channel_routing(channel_id, bus_name, new_state)
            
            print(f"🔀 Routing {channel_id} → {bus_name}: {'ON' if new_state else 'OFF'}")
            
            # Aggiorna UI
            if channel_id in self.mixer_channel_strips:
                btn = self.mixer_channel_strips[channel_id].routing_buttons[bus_name]
                btn.configure(fg_color=COLORS["accent"] if new_state else COLORS["bg_card"])
            
            # Salva configurazione
            self.save_config()
    
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
    
    def load_local_file(self):
        """Carica file audio locale dal PC"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.ogg *.m4a"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.yt_status_label.configure(text="⏳ Caricamento file...")
            self.after(100, lambda: self._load_media_file(file_path, os.path.basename(file_path)))
    
    def _load_media_file(self, file_path, title):
        """Carica file audio nel media player"""
        try:
            import soundfile as sf
            
            # Carica file audio
            audio_data, sr = sf.read(file_path, dtype='float32')
            
            print(f"📀 Media Player: {int(sr)}Hz", end="")
            
            # Converti a stereo se necessario
            if len(audio_data.shape) == 1:
                audio_data = np.column_stack([audio_data, audio_data])
            
            # Resample se necessario AL SAMPLE RATE DEL MIXER
            target_sr = self.pro_mixer.sample_rate
            print(f" → Target: {target_sr}Hz")
            
            if sr != target_sr:
                print(f"   ⚠️ Resampling: {sr}Hz → {target_sr}Hz")
                from scipy.signal import resample_poly
                from math import gcd
                g = gcd(target_sr, int(sr))
                up = target_sr // g
                down = int(sr) // g
                
                print(f"   Up={up}, Down={down}, GCD={g}")
                
                resampled_channels = []
                for ch in range(audio_data.shape[1]):
                    resampled_ch = resample_poly(audio_data[:, ch], up, down)
                    resampled_channels.append(resampled_ch)
                audio_data = np.column_stack(resampled_channels).astype(np.float32)
                sr = target_sr
                print(f" ✓")
            
            # STOP playback precedente se attivo
            if hasattr(self, 'media_player_playing') and self.media_player_playing:
                self.stop_youtube()
            
            # RESET COMPLETO stato media player
            self.media_player_audio = audio_data
            self.media_player_sr = target_sr  # USA IL TARGET, NON IL SR ORIGINALE
            self.media_player_duration = len(audio_data)
            self.media_player_positions = {}  # Reset posizioni per tutti i bus
            self._media_positions = {}  # Reset posizioni callback (CRITICO!)
            self.media_player_playing = False
            self._media_debug_printed = False  # Reset flag debug
            
            print(f"✅ Audio caricato: {len(audio_data)} samples @ {target_sr}Hz")
            print(f"   Durata: {len(audio_data) / target_sr:.2f} secondi")
            
            # Aggiorna UI
            duration_sec = self.media_player_duration / sr
            duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}"
            self.yt_duration_label.configure(text=duration_str)
            self.yt_status_label.configure(text=f"✅ {title[:40]}...", text_color=COLORS["success"])
            self.yt_play_btn.configure(state="normal")
            self.yt_stop_btn.configure(state="normal")
            self.yt_progress_slider.configure(state="normal")
            
            # Configura HW3 per ricevere audio
            self._setup_media_player_hw3()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare file:\n{e}")
            self.yt_status_label.configure(text="❌ Errore caricamento", text_color=COLORS["error"])
    
    def _setup_media_player_hw3(self):
        """Configura canale HW3 per ricevere audio dal media player"""
        # Imposta callback per HW3
        hw3_channel = self.pro_mixer.channels.get('HW3')
        if hw3_channel:
            hw3_channel.channel_type = 'python'  # Imposta come canale Python
            hw3_channel.audio_callback = self._media_player_callback
            
            print(f"✅ Media Player configurato su HW3")
            print(f"   Usa i pulsanti routing del canale HW3 per scegliere l'uscita")
    
    def _media_player_callback(self, frames, bus_name=None):
        """Callback che fornisce audio al canale HW3
        
        Args:
            frames: Numero di frame richiesti
            bus_name: Nome del bus che richiede audio (per posizioni indipendenti)
        """
        try:
            if not self.media_player_playing or self.media_player_audio is None:
                return np.zeros((frames, 2), dtype=np.float32)
            
            # POSIZIONI INDIPENDENTI PER OGNI BUS (come AudioClip)
            # Ogni bus ha la sua posizione, così non si influenzano
            
            if not hasattr(self, '_media_positions'):
                self._media_positions = {}
                print(f"🎵 Media Player callback inizializzato - Duration: {self.media_player_duration} samples")
            
            # Ottieni o crea posizione per questo bus
            if bus_name not in self._media_positions:
                self._media_positions[bus_name] = 0
            
            position = self._media_positions[bus_name]
            
            # Genera audio per questo bus
            start = position
            end = min(start + frames, self.media_player_duration)
            
            audio = self.media_player_audio[start:end].copy()
            
            # Applica volume
            volume = self.yt_volume_slider.get() / 100.0
            audio *= volume
            
            # Pad se necessario
            if len(audio) < frames:
                padding = np.zeros((frames - len(audio), 2), dtype=np.float32)
                audio = np.vstack([audio, padding])
                # Fine file per questo bus
                if position + frames >= self.media_player_duration:
                    # Se TUTTI i bus hanno finito, ferma la riproduzione
                    all_finished = all(pos >= self.media_player_duration for pos in self._media_positions.values())
                    if all_finished:
                        self.media_player_playing = False
                        self.after(0, self._on_playback_finished)
                        print(f"⏹️ Media Player: Fine riproduzione")
            
            # Avanza posizione per questo bus
            self._media_positions[bus_name] = end
            
            # Log ogni secondo (solo per il primo bus)
            if bus_name == 'A1' or (bus_name and len(self._media_positions) == 1):
                if not hasattr(self, '_last_log_pos'):
                    self._last_log_pos = 0
                if start - self._last_log_pos >= 48000:
                    print(f"🎵 Playing [{bus_name}]: {start/48000:.1f}s / {self.media_player_duration/48000:.1f}s | Volume: {volume*100:.0f}%")
                    self._last_log_pos = start
            
            return audio
        except Exception as e:
            print(f"❌ Errore in _media_player_callback: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros((frames, 2), dtype=np.float32)
    
    def _on_playback_finished(self):
        """Gestisce fine riproduzione"""
        if self.media_player_looping:
            # Riavvia la riproduzione se loop è attivo
            self._media_positions = {}  # Reset posizioni corrette
            self.media_player_playing = True
            self.yt_status_label.configure(text="🔁 Loop attivo", text_color=COLORS["accent"])
            print(f"🔁 Media Player: Riparte in loop")
        else:
            self.yt_status_label.configure(text="⏹️ Fine riproduzione", text_color=COLORS["text_muted"])
            if hasattr(self, '_media_master_position'):
                self._media_master_position = 0
            if hasattr(self, '_media_positions'):
                self._media_positions = {}
            self.media_player_playing = False
    
    def load_youtube_url(self):
        """Carica audio da URL YouTube"""
        url = self.yt_url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL Mancante", "Inserisci un link YouTube valido")
            return
        
        # Disabilita pulsante durante il caricamento
        self.yt_load_btn.configure(state="disabled", text="⏳ Caricamento...")
        self.yt_status_label.configure(text="⏳ Download audio in corso...")
        
        # Ottieni formato selezionato
        selected_format = self.yt_format_menu.get().lower()  # 'wav' o 'mp3'
        
        def download_thread():
            try:
                import yt_dlp
                import soundfile as sf
                import re
                
                # Opzioni yt-dlp per ottenere info
                ydl_opts_info = {
                    'quiet': True,
                    'no_warnings': True,
                }
                
                # Ottieni titolo video
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'YouTube Audio')
                
                # Sanitize filename
                safe_title = re.sub(r'[\\/:*?"<>|]', '', title)
                safe_title = safe_title[:100]  # Max 100 caratteri
                
                # Usa il formato selezionato
                output_file = os.path.join(self.youtube_folder, f"{safe_title}.{selected_format}")
                
                # Se esiste già, aggiungi numero
                counter = 1
                while os.path.exists(output_file):
                    output_file = os.path.join(self.youtube_folder, f"{safe_title}_{counter}.{selected_format}")
                    counter += 1
                
                # Opzioni yt-dlp per download
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': selected_format,
                    }],
                    'outtmpl': output_file.replace(f'.{selected_format}', ''),
                    'quiet': True,
                    'no_warnings': True,
                }
                
                # Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Verifica quale file è stato effettivamente creato
                # yt_dlp potrebbe aver aggiunto l'estensione
                import time
                time.sleep(0.5)  # Aspetta che il file sia scritto
                
                actual_file = output_file
                if not os.path.exists(output_file):
                    # Prova con estensione aggiunta da yt_dlp
                    if os.path.exists(output_file + '.wav'):
                        actual_file = output_file + '.wav'
                    else:
                        # Cerca il file più recente nella cartella
                        files = [os.path.join(self.youtube_folder, f) for f in os.listdir(self.youtube_folder) 
                                if f.lower().endswith('.wav')]
                        if files:
                            actual_file = max(files, key=os.path.getctime)
                
                # Aggiorna libreria
                self.after(0, lambda: self.youtube_downloader._refresh_library())
                
                # Carica nel media player
                self.after(0, lambda: self._load_media_file(actual_file, title))
                self.after(0, lambda: self.yt_load_btn.configure(state="normal", text="📥 YouTube"))
                
            except Exception as e:
                self.after(0, lambda: self._youtube_load_error(str(e)))
        
        import threading
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _youtube_load_error(self, error):
        """Gestisce errore caricamento YouTube"""
        messagebox.showerror("Errore", f"Impossibile caricare audio:\n{error}")
        self.yt_status_label.configure(text="❌ Errore caricamento", text_color=COLORS["error"])
        self.yt_load_btn.configure(state="normal", text="📥 YouTube")
    
    def play_youtube(self):
        """Avvia riproduzione media player"""
        if self.media_player_audio is not None:
            # Verifica routing di HW3
            hw3_channel = self.pro_mixer.channels.get('HW3')
            if hw3_channel:
                active_routes = [bus for bus, enabled in hw3_channel.routing.items() if enabled]
                print(f"▶️ Media Player START")
                print(f"   Audio: {self.media_player_duration/48000:.1f}s @ 48kHz")
                print(f"   HW3 Routing: {active_routes if active_routes else 'NESSUNO ATTIVO!'}")
                
                if not active_routes:
                    messagebox.showwarning(
                        "Nessun routing attivo",
                        "Il canale HW3 non ha routing attivi!\n\n"
                        "Attiva almeno un pulsante (A1, A2, etc.) sul canale HW3 nel mixer."
                    )
                    return
            else:
                print(f"❌ Canale HW3 non trovato!")
                return
            
            self.media_player_playing = True
            self.yt_status_label.configure(text="▶️ In riproduzione...", text_color=COLORS["success"])
    
    def stop_youtube(self):
        """Ferma riproduzione media player"""
        self.media_player_playing = False
        if hasattr(self, '_media_positions'):
            self._media_positions = {}  # Reset tutte le posizioni
        self.yt_status_label.configure(text="⏹️ Fermato", text_color=COLORS["text_muted"])
    
    def toggle_media_loop(self):
        """Attiva/disattiva loop del media player"""
        self.media_player_looping = not self.media_player_looping
        
        # Aggiorna UI del bottone
        if self.media_player_looping:
            self.yt_loop_btn.configure(
                text="🔁 ON",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"]
            )
            if self.media_player_playing:
                self.yt_status_label.configure(text="🔁 Loop attivo", text_color=COLORS["accent"])
        else:
            self.yt_loop_btn.configure(
                text="🔁 Loop",
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["bg_secondary"]
            )
            if self.media_player_playing:
                self.yt_status_label.configure(text="▶️ In riproduzione", text_color=COLORS["success"])
    
    def on_youtube_volume_change(self, value):
        """Cambia volume media player"""
        volume = int(value)
        self.yt_volume_label.configure(text=f"{volume}%")
    
    def on_media_seek(self, value):
        """Seek nella posizione del media player"""
        if self.media_player_audio is not None:
            # Converti percentuale in samples
            position_pct = float(value) / 100.0
            new_position = int(position_pct * self.media_player_duration)
            
            # Aggiorna tutte le posizioni di tutti i bus
            if hasattr(self, '_media_positions'):
                for bus_name in list(self._media_positions.keys()):
                    self._media_positions[bus_name] = new_position
    
    def update_media_progress(self):
        """Aggiorna progress bar del media player"""
        # Aggiorna UI
        if self.media_player_audio is not None and self.media_player_duration > 0:
            # Usa la posizione media di tutti i bus attivi
            if hasattr(self, '_media_positions') and self._media_positions:
                current_pos = sum(self._media_positions.values()) / len(self._media_positions)
            else:
                current_pos = 0
            
            # Calcola percentuale
            progress_pct = (current_pos / self.media_player_duration) * 100.0
            
            # Aggiorna slider senza triggerare callback
            self.yt_progress_slider.set(progress_pct)
            
            # Aggiorna label tempo
            current_sec = current_pos / self.media_player_sr
            current_str = f"{int(current_sec // 60)}:{int(current_sec % 60):02d}"
            self.yt_time_label.configure(text=current_str)
        
        # Richiama dopo 100ms
        self.after(100, self.update_media_progress)
    
    def open_channel_fx(self, channel_id):
        """Apri finestra effetti per un canale"""
        from ui.fx_window import ChannelFXWindow
        ChannelFXWindow(self, self.pro_mixer, channel_id)
    
    def toggle_mute_a1(self):
        """Toggle mute del bus A1 (Discord)"""
        bus = self.pro_mixer.output_buses.get('A1')
        if bus:
            bus.mute = not bus.mute
            self.mute_a1_btn.configure(
                text="🔇 A1 MUTED" if bus.mute else "🔊 A1 (Discord)",
                fg_color=COLORS["danger"] if bus.mute else COLORS["success"]
            )
    
    def toggle_mute_a2(self):
        """Toggle mute del bus A2 (Cuffie)"""
        bus = self.pro_mixer.output_buses.get('A2')
        if bus:
            bus.mute = not bus.mute
            self.mute_a2_btn.configure(
                text="🔇 A2 MUTED" if bus.mute else "🔊 A2 (Cuffie)",
                fg_color=COLORS["danger"] if bus.mute else COLORS["success"]
            )
    
    def check_autostart(self):
        """Verifica se l'app è nell'avvio automatico di Windows"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "SoundboardMixing4Fun")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            print(f"Errore check autostart: {e}")
            return False
    
    def toggle_autostart(self):
        """Attiva/disattiva avvio automatico con Windows"""
        try:
            import winreg
            import sys
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            if self.autostart_var.get():
                # Aggiungi all'avvio
                exe_path = os.path.abspath(sys.argv[0])
                if exe_path.endswith('.py'):
                    # Se eseguito da Python, usa pythonw.exe
                    python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                    cmd = f'"{python_exe}" "{exe_path}"'
                else:
                    # Se è un .exe compilato
                    cmd = f'"{exe_path}"'
                
                winreg.SetValueEx(key, "SoundboardMixing4Fun", 0, winreg.REG_SZ, cmd)
                messagebox.showinfo("Avvio Automatico", "✓ App aggiunta all'avvio automatico di Windows")
            else:
                # Rimuovi dall'avvio
                try:
                    winreg.DeleteValue(key, "SoundboardMixing4Fun")
                    messagebox.showinfo("Avvio Automatico", "✓ App rimossa dall'avvio automatico di Windows")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile modificare avvio automatico:\n{e}")
            self.autostart_var.set(not self.autostart_var.get())
    
    def start_pro_mixer(self):
        """Avvia il mixer professionale"""
        try:
            self.pro_mixer.start_all()
            self.pro_mixer_running = True
            messagebox.showinfo("ProMixer", "Mixer professionale avviato!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare mixer:\n{e}")
    
    def stop_pro_mixer(self):
        """Ferma il mixer professionale"""
        self.pro_mixer.stop_all()
        self.pro_mixer_running = False
    
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
    
    def _on_tab_change(self):
        """Gestisce il cambio di tab"""
        current_tab = self.tabview.get()
        # Disabilita hotkey se nella tab YouTube
        if current_tab == "📥 YouTube":
            self.soundboard_enabled = False
            logger.debug("Tab YouTube attiva - hotkey soundboard disabilitate")
        else:
            # Riabilita solo se non è già disabilitato dall'utente
            if hasattr(self, 'enable_checkbox') and self.enable_checkbox.get():
                self.soundboard_enabled = True
                logger.debug("Tab cambiata - hotkey soundboard riabilitate")
    
    def trigger_clip_hotkey(self, clip_name: str):
        """Triggera una clip tramite hotkey"""
        try:
            # Non triggerare se siamo nella tab YouTube
            if hasattr(self, 'tabview') and self.tabview.get() == "📥 YouTube":
                logger.debug(f"Tab YouTube attiva, ignoro hotkey per {clip_name}")
                return
            
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
        
        # Salva configurazione PRIMA di fermare qualsiasi cosa
        try:
            # Debug: mostra input_device_map prima del salvataggio
            if hasattr(self, 'pro_mixer'):
                print(f"   📋 input_device_map al momento della chiusura: {self.pro_mixer.input_device_map}")
            self.save_config()
            print("✓ Configurazione salvata prima della chiusura")
        except Exception as e:
            print(f"⚠ Errore salvataggio configurazione: {e}")
            import traceback
            traceback.print_exc()
        
        # Ferma mixer
        if hasattr(self, 'mixer'):
            self.mixer.stop()
        
        # Ferma ProMixer
        if hasattr(self, 'pro_mixer'):
            self.pro_mixer.stop_all()
        
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
            clip = AudioClip(file_path, clip_name, target_sample_rate=self.mixer.sample_rate)
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
    
    def restore_promixer_config(self):
        """Ripristina la configurazione del ProMixer dal file salvato"""
        try:
            config = self.load_config_dict()
            mixer_config = config.get('pro_mixer', {})
            
            if not mixer_config:
                print("   Nessuna configurazione ProMixer salvata")
                return
            
            print("🔄 Ripristino configurazione ProMixer...")
            
            # Ripristina dispositivi input
            input_devices = mixer_config.get('input_devices', {})
            print(f"   📋 input_devices da caricare: {input_devices}")
            for channel_id, device_id in input_devices.items():
                if channel_id in self.pro_mixer.channels:
                    success = self.pro_mixer.start_input(channel_id, device_id)
                    if success:
                        print(f"   ✓ {channel_id} → Device {device_id}")
                        # Aggiorna UI del canale
                        if hasattr(self, 'mixer_channel_strips') and channel_id in self.mixer_channel_strips:
                            strip = self.mixer_channel_strips[channel_id]
                            channel = self.pro_mixer.channels[channel_id]
                            if hasattr(strip, 'name_label'):
                                strip.name_label.configure(text=channel.name)
                            # Aggiorna routing buttons
                            if hasattr(strip, 'routing_buttons'):
                                from ui.colors import COLORS
                                for bus_name, btn in strip.routing_buttons.items():
                                    is_active = channel.routing.get(bus_name, False)
                                    btn.configure(fg_color=COLORS["accent"] if is_active else COLORS["bg_card"])
            
            # Ripristina dispositivi output
            output_devices = mixer_config.get('output_devices', {})
            for bus_name, device_id in output_devices.items():
                if bus_name in self.pro_mixer.buses:
                    self.pro_mixer.set_bus_device(bus_name, device_id)
                    print(f"   ✓ Bus {bus_name} → Device {device_id}")
            
            # Ripristina routing
            channel_routing = mixer_config.get('channel_routing', {})
            for channel_id, routing in channel_routing.items():
                if channel_id in self.pro_mixer.channels:
                    for bus_name, level in routing.items():
                        self.pro_mixer.set_channel_routing(channel_id, bus_name, level > 0)
                        if level > 0:
                            self.pro_mixer.channels[channel_id].routing[bus_name] = level
            
            # Ripristina fader (in dB)
            channel_volumes = mixer_config.get('channel_volumes', {})
            for channel_id, fader_db in channel_volumes.items():
                if channel_id in self.pro_mixer.channels:
                    self.pro_mixer.channels[channel_id].set_fader_db(fader_db)
                    # Aggiorna UI del fader
                    if hasattr(self, 'mixer_channel_strips') and channel_id in self.mixer_channel_strips:
                        strip = self.mixer_channel_strips[channel_id]
                        if hasattr(strip, 'fader'):
                            strip.fader.set(fader_db)
                        if hasattr(strip, 'db_label'):
                            strip.db_label.configure(text=f"{fader_db:+.1f} dB")
            
            # Ripristina effetti
            channel_effects = mixer_config.get('channel_effects', {})
            for channel_id, effects in channel_effects.items():
                if channel_id in self.pro_mixer.channels:
                    proc = self.pro_mixer.channels[channel_id].processor
                    proc.gate_enabled = effects.get('gate_enabled', False)
                    proc.gate_threshold = effects.get('gate_threshold', -40.0)
                    proc.comp_enabled = effects.get('comp_enabled', False)
                    proc.compressor_threshold = effects.get('comp_threshold', -20.0)
                    proc.compressor_ratio = effects.get('comp_ratio', 4.0)
                    proc.eq_low = effects.get('eq_low', 0.0)
                    proc.eq_mid = effects.get('eq_mid', 0.0)
                    proc.eq_high = effects.get('eq_high', 0.0)
            
            print("✓ Configurazione ProMixer ripristinata")
            
        except Exception as e:
            print(f"⚠ Errore ripristino configurazione ProMixer: {e}")
    
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
            
            # Salva configurazione ProMixer (dispositivi e routing)
            if hasattr(self, 'pro_mixer') and self.pro_mixer:
                mixer_config = {
                    'input_devices': {},  # {channel_id: device_id}
                    'output_devices': {},  # {bus_name: device_id}
                    'channel_routing': {},  # {channel_id: {bus_name: level}}
                    'channel_volumes': {},  # {channel_id: volume}
                    'channel_effects': {}  # {channel_id: effect_settings}
                }
                
                # Salva dispositivi input (usa input_device_map)
                mixer_config['input_devices'] = self.pro_mixer.input_device_map.copy()
                print(f"   📝 Salvataggio input_devices: {mixer_config['input_devices']}")
                
                # Salva routing e fader
                for channel_id, channel in self.pro_mixer.channels.items():
                    # Salva routing
                    mixer_config['channel_routing'][channel_id] = channel.routing.copy()
                    # Salva fader (in dB)
                    mixer_config['channel_volumes'][channel_id] = channel.fader
                    
                    # Salva impostazioni effetti
                    proc = channel.processor
                    mixer_config['channel_effects'][channel_id] = {
                        'gate_enabled': proc.gate_enabled,
                        'gate_threshold': proc.gate_threshold,
                        'comp_enabled': proc.comp_enabled,
                        'comp_threshold': proc.compressor_threshold,
                        'comp_ratio': proc.compressor_ratio,
                        'eq_low': proc.eq_low,
                        'eq_mid': proc.eq_mid,
                        'eq_high': proc.eq_high
                    }
                
                # Salva dispositivi output
                for bus_name, bus in self.pro_mixer.buses.items():
                    if bus.device_id is not None:
                        mixer_config['output_devices'][bus_name] = bus.device_id
                
                config['pro_mixer'] = mixer_config
            
            # Salva nel file JSON (preservando audio_output_device e secondary_output_device)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Configurazione salvata (ProMixer incluso)")
                
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
                        clip = AudioClip(file_path, clip_name, target_sample_rate=self.mixer.sample_rate)
                        clip.volume = clip_data.get('volume', 1.0)
                        
                        # Applica stato loop globale se attivo
                        clip.is_looping = self.loop_enabled
                        
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
        
        # Riordina automaticamente le clip dopo il caricamento
        self.after(100, self.reorder_clips)  # Dopo 100ms per dare tempo alla UI
        
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
                            clip = AudioClip(file_path, filename, target_sample_rate=self.mixer.sample_rate)
                            
                            # Applica stato loop globale se attivo
                            clip.is_looping = self.loop_enabled
                            
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
        
        # NON salvare qui - sovrascrive input_devices prima del restore!
        # Il salvataggio verrà fatto dopo restore_promixer_config()
        
        # Aggiorna lista clip nel mixer
        self.update_mixer_clips_list()


# ===== ENTRY POINT =====

if __name__ == "__main__":
    app = AudioMixerApp()
    app.mainloop()
