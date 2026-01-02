"""
YouTube Downloader Module - Sistema completo integrato per scaricare e tagliare clip
con anteprima waveform e selezione visuale
"""
import customtkinter as ctk
from tkinter import messagebox, Canvas, Menu, filedialog, simpledialog
import os
import tempfile
import soundfile as sf
import sounddevice as sd
import numpy as np
from threading import Thread
import time
import subprocess
import shutil

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class YouTubeDownloader:
    """Gestisce il download da YouTube con anteprima e taglio integrati"""
    
    def __init__(self, parent, on_download_complete, colors, clips_folder=None, youtube_folder=None):
        self.parent = parent
        self.on_download_complete = on_download_complete
        self.colors = colors
        self.is_downloading = False
        self.clips_folder = clips_folder or os.path.join(os.path.dirname(__file__), "clips")
        self.youtube_folder = youtube_folder or os.path.join(os.path.dirname(__file__), "youtube_downloads")
        
        # Crea cartella YouTube se non esiste
        os.makedirs(self.youtube_folder, exist_ok=True)
        
        # Libreria file YouTube scaricati
        self.youtube_library = []
        self._load_youtube_library()
        self.search_filter = ""  # Filtro ricerca
        
        # Drag and Drop
        self.drag_data = None  # {'path': path, 'name': name, 'is_folder': bool, 'widget': widget}
        self.drag_start_pos = None
        self.drop_target = None
        self.current_hover_folder = None  # (folder_path, frame_widget) quando mouse sopra cartella
        self.highlighted_widget = None  # Widget attualmente evidenziato
        self.drag_check_job = None  # Job per controllo periodico posizione mouse
        
        # Stato audio
        self.audio_data = None
        self.sample_rate = None
        self.duration = 0
        self.temp_file = None
        self.video_title = ""
        
        # Playback
        self.is_playing = False
        self.playback_thread = None
        self.playback_position = 0  # Posizione corrente durante playback
        self.playback_update_job = None  # Job per update progressione
        
        # Selezione
        self.start_time = 0
        self.end_time = 0
        
        # UI elements
        self.url_entry = None
        self.download_btn = None
    
    def _format_time(self, seconds):
        """Formatta secondi in formato mm:ss.ms"""
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:05.2f}"
    
    def _parse_time(self, time_str):
        """Converte mm:ss.ms o secondi in secondi"""
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                mins = int(parts[0])
                secs = float(parts[1])
                return mins * 60 + secs
            else:
                return float(time_str)
        except:
            return 0
    
    def _load_youtube_library(self):
        """Carica la libreria dei file YouTube scaricati"""
        self.youtube_library = []
        
        # Debug per troubleshooting
        try:
            with open(os.path.join(os.path.dirname(__file__), "library_debug.txt"), "w", encoding="utf-8") as f:
                f.write(f"Libreria YouTube Debug\n")
                f.write(f"======================\n")
                f.write(f"Cartella: {self.youtube_folder}\n")
                f.write(f"Esiste: {os.path.exists(self.youtube_folder)}\n")
                
                if os.path.exists(self.youtube_folder):
                    files = os.listdir(self.youtube_folder)
                    f.write(f"File totali: {len(files)}\n")
                    f.write(f"File trovati:\n")
                    for file in files:
                        f.write(f"  - {file}\n")
                else:
                    f.write("Cartella non esiste - creazione...\n")
        except Exception as e:
            pass
        
        if os.path.exists(self.youtube_folder):
            for file in os.listdir(self.youtube_folder):
                if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                    file_path = os.path.join(self.youtube_folder, file)
                    self.youtube_library.append({
                        'name': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
        else:
            os.makedirs(self.youtube_folder, exist_ok=True)
        
        self.youtube_library.sort(key=lambda x: x['name'])
        self.progress_label = None
        self.waveform_canvas = None
        self.preview_container = None
        self.start_entry = None
        self.end_entry = None
        self.duration_label = None
        self.play_btn = None
        self.filename_entry = None
    
    def create_youtube_tab(self, tab):
        """Crea l'interfaccia completa nella tab YouTube"""
        main_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="🎬 Download da YouTube",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["accent"]
        )
        header.pack(pady=(0, 20))
        
        # Sezione Download
        download_frame = ctk.CTkFrame(main_frame, fg_color=self.colors["bg_card"], corner_radius=10)
        download_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            download_frame,
            text="📥 Download Video",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        if not YT_DLP_AVAILABLE:
            ctk.CTkLabel(
                download_frame,
                text="⚠️ yt-dlp non installato! Installa con: pip install yt-dlp",
                text_color=self.colors["danger"],
                font=ctk.CTkFont(size=12)
            ).pack(padx=15, pady=10)
        
        # URL input
        url_container = ctk.CTkFrame(download_frame, fg_color="transparent")
        url_container.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            url_container,
            text="URL:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.url_entry = ctk.CTkEntry(
            url_container,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        
        # Download button
        self.download_btn = ctk.CTkButton(
            download_frame,
            text="📥 Scarica & Mostra Waveform",
            command=self.download_and_preview,
            height=45,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.download_btn.pack(pady=15, padx=50, fill="x")
        
        # Progress
        self.progress_label = ctk.CTkLabel(
            download_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.progress_label.pack(pady=(0, 15))
        
        # Sezione Preview (nascosta inizialmente)
        self.preview_container = ctk.CTkFrame(main_frame, fg_color=self.colors["bg_card"], corner_radius=10)
        # Non pack ancora
        
        self._create_preview_section()
    
    def create_library_tab(self, parent):
        """Crea la tab dedicata alla libreria con navigazione"""
        # Frame principale che occupa tutto lo spazio
        main_frame = ctk.CTkFrame(parent, fg_color=self.colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header_frame,
            text="📚 Libreria YouTube",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(side="left")
        
        # Pulsante cambia cartella
        ctk.CTkButton(
            header_frame,
            text="📁 Cambia Cartella",
            width=140,
            height=35,
            command=self._change_youtube_folder,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"]
        ).pack(side="right", padx=5)
        
        # Pulsante refresh
        ctk.CTkButton(
            header_frame,
            text="🔄 Aggiorna",
            width=100,
            height=35,
            command=self._refresh_library,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="right")
        
        # Pulsante crea cartella
        ctk.CTkButton(
            header_frame,
            text="📁+ Nuova Cartella",
            width=140,
            height=35,
            command=self._create_new_folder,
            fg_color=self.colors["success"],
            hover_color="#059669"
        ).pack(side="right", padx=5)
        
        # Barra di ricerca
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Cerca file o cartelle...",
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        ctk.CTkButton(
            search_frame,
            text="✖️",
            width=35,
            height=35,
            command=self._clear_search,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="left")
        
        # Info cartella corrente
        self.library_folder_label_tab = ctk.CTkLabel(
            main_frame,
            text=f"📂 Cartella: {self.youtube_folder}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.library_folder_label_tab.pack(pady=(0, 10), anchor="w")
        
        # Lista file scrollabile che occupa tutto lo spazio disponibile
        list_container = ctk.CTkScrollableFrame(
            main_frame, 
            fg_color=self.colors["bg_secondary"],
            corner_radius=10
        )
        list_container.pack(fill="both", expand=True)
        
        self.library_list_frame_tab = list_container
        self._update_library_ui()
    
    def _create_library_section(self, parent):
        """Crea sezione libreria YouTube"""
        library_frame = ctk.CTkFrame(parent, fg_color=self.colors["bg_card"], corner_radius=10)
        library_frame.pack(fill="x", pady=10)
        
        # Header con pulsanti
        header_frame = ctk.CTkFrame(library_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📚 Libreria YouTube",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Pulsante cambia cartella
        ctk.CTkButton(
            header_frame,
            text="📁 Cambia Cartella",
            width=140,
            height=30,
            command=self._change_youtube_folder,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="right", padx=5)
        
        # Pulsante refresh
        ctk.CTkButton(
            header_frame,
            text="🔄 Aggiorna",
            width=100,
            height=30,
            command=self._refresh_library,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="right")
        
        # Info cartella
        folder_label = ctk.CTkLabel(
            library_frame,
            text=f"📂 Cartella: {self.youtube_folder}",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_muted"]
        )
        folder_label.pack(padx=15, pady=(0, 5), anchor="w")
        self.library_folder_label = folder_label
        
        # Lista file
        list_container = ctk.CTkScrollableFrame(library_frame, height=150, fg_color=self.colors["bg_primary"])
        list_container.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        self.library_list_frame_youtube = list_container
        self._update_library_ui()
    
    def create_library_in_mixer(self, parent, row):
        """Crea la libreria YouTube nel tab Mixer usando grid layout"""
        library_frame = ctk.CTkFrame(parent, fg_color=self.colors["bg_card"], corner_radius=10)
        library_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        
        # Header con pulsanti
        header_frame = ctk.CTkFrame(library_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📚 Libreria YouTube",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Pulsante cambia cartella
        ctk.CTkButton(
            header_frame,
            text="📁 Cambia Cartella",
            width=140,
            height=30,
            command=self._change_youtube_folder,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="right", padx=5)
        
        # Pulsante refresh
        ctk.CTkButton(
            header_frame,
            text="🔄 Aggiorna",
            width=100,
            height=30,
            command=self._refresh_library,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="right")
        
        # Info cartella
        folder_label = ctk.CTkLabel(
            library_frame,
            text=f"📂 Cartella: {self.youtube_folder}",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_muted"]
        )
        folder_label.pack(padx=15, pady=(0, 5), anchor="w")
        self.library_folder_label = folder_label
        
        # Lista file (più compatta per il mixer)
        list_container = ctk.CTkScrollableFrame(library_frame, height=120, fg_color=self.colors["bg_primary"])
        list_container.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        self.library_list_frame = list_container
        self._update_library_ui()
    
    def create_library_in_sidebar(self, parent, row):
        """Crea la libreria YouTube nella sidebar laterale usando grid layout"""
        library_frame = ctk.CTkFrame(parent, fg_color=self.colors["bg_card"], corner_radius=10)
        library_frame.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        
        # Header compatto
        header_frame = ctk.CTkFrame(library_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="📚 Libreria YouTube",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w")
        
        # Pulsanti compatti
        buttons_frame = ctk.CTkFrame(library_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="🔄",
            width=40,
            height=25,
            command=self._refresh_library,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            buttons_frame,
            text="📁",
            width=40,
            height=25,
            command=self._change_youtube_folder,
            fg_color=self.colors["bg_secondary"],
            hover_color=self.colors["bg_card"]
        ).pack(side="left", padx=2)
        
        # Info cartella (compatta)
        folder_label = ctk.CTkLabel(
            library_frame,
            text=f"📂 {os.path.basename(self.youtube_folder)}",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_muted"]
        )
        folder_label.pack(padx=10, pady=(0, 3), anchor="w")
        self.library_folder_label = folder_label
        
        # Lista file compatta con navigazione
        list_container = ctk.CTkScrollableFrame(library_frame, height=100, fg_color=self.colors["bg_primary"])
        list_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self.library_list_frame_sidebar = list_container
        self.current_folder = self.youtube_folder  # Cartella corrente
        self._update_library_ui()
        
        # Avvia auto-refresh periodico ogni 5 secondi
        self._start_auto_refresh()
    
    def _start_auto_refresh(self):
        """Avvia controllo periodico per nuovi file"""
        def check_updates():
            old_count = len(self.youtube_library)
            self._load_youtube_library()
            new_count = len(self.youtube_library)
            if old_count != new_count:
                self._update_library_ui()
            # Richiama dopo 5 secondi
            self.parent.after(5000, check_updates)
        
        # Avvia il primo controllo dopo 5 secondi
        self.parent.after(5000, check_updates)
    
    def _update_library_ui(self):
        """Aggiorna UI della libreria - aggiorna TUTTE le liste"""
        # Aggiorna lista Tab dedicata (con navigazione completa)
        if hasattr(self, 'library_list_frame_tab') and self.library_list_frame_tab:
            self._update_single_library_ui(self.library_list_frame_tab, compact=False, show_navigation=True)
        
        # Aggiorna lista YouTube (vecchia, senza navigazione)
        if hasattr(self, 'library_list_frame_youtube') and self.library_list_frame_youtube:
            self._update_single_library_ui(self.library_list_frame_youtube, compact=False)
        
        # Aggiorna lista Sidebar (compatta con navigazione)
        if hasattr(self, 'library_list_frame_sidebar') and self.library_list_frame_sidebar:
            self._update_single_library_ui(self.library_list_frame_sidebar, compact=True, show_navigation=True)
    
    def _update_single_library_ui(self, list_frame, compact=False, show_navigation=False):
        """Aggiorna una singola lista libreria"""
        if list_frame is None:
            return
        
        # Pulisci lista
        try:
            for widget in list_frame.winfo_children():
                widget.destroy()
        except:
            pass
        
        # Determina quale cartella mostrare
        if show_navigation and hasattr(self, 'current_folder'):
            folder_to_show = self.current_folder
        else:
            folder_to_show = self.youtube_folder
        
        # Navigazione stile Windows (solo per sidebar)
        if show_navigation:
            nav_frame = ctk.CTkFrame(list_frame, fg_color=self.colors["bg_secondary"])
            nav_frame.pack(fill="x", pady=(0, 5), padx=2)
            
            # Pulsante UP (cartella padre)
            parent_folder = os.path.dirname(folder_to_show)
            if parent_folder and os.path.exists(parent_folder):
                ctk.CTkButton(
                    nav_frame,
                    text="⬆️",
                    width=30,
                    height=25,
                    command=self._navigate_up,
                    fg_color=self.colors["accent"],
                    hover_color=self.colors["accent_hover"]
                ).pack(side="left", padx=2, pady=2)
            
            # Percorso corrente (troncato)
            path_text = os.path.basename(folder_to_show) or folder_to_show
            if len(path_text) > 20:
                path_text = path_text[:18] + "..."
            
            ctk.CTkLabel(
                nav_frame,
                text=f"📂 {path_text}",
                font=ctk.CTkFont(size=9, weight="bold")
            ).pack(side="left", padx=5, pady=2)
        
        # Lista file e cartelle
        if not os.path.exists(folder_to_show):
            ctk.CTkLabel(
                list_frame,
                text="Cartella non trovata",
                text_color=self.colors["text_muted"]
            ).pack(pady=20)
            return
        
        items = []
        try:
            for item_name in os.listdir(folder_to_show):
                # Applica filtro ricerca
                if self.search_filter and self.search_filter.lower() not in item_name.lower():
                    continue
                
                item_path = os.path.join(folder_to_show, item_name)
                if os.path.isdir(item_path):
                    items.append({'type': 'folder', 'name': item_name, 'path': item_path})
                elif item_name.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                    items.append({
                        'type': 'file',
                        'name': item_name,
                        'path': item_path,
                        'size': os.path.getsize(item_path)
                    })
        except Exception as e:
            ctk.CTkLabel(
                list_frame,
                text=f"Errore lettura: {str(e)[:30]}",
                text_color=self.colors["text_muted"]
            ).pack(pady=20)
            return
        
        # Ordina: cartelle prima, poi file alfabeticamente
        items.sort(key=lambda x: (x['type'] != 'folder', x['name'].lower()))
        
        if not items:
            ctk.CTkLabel(
                list_frame,
                text="Cartella vuota",
                text_color=self.colors["text_muted"]
            ).pack(pady=20)
            return
        
        # Mostra cartelle e file
        for item in items:
            item_frame = ctk.CTkFrame(list_frame, fg_color=self.colors["bg_card"], corner_radius=3)
            item_frame.pack(fill="x", pady=1, padx=2)
            item_frame.grid_columnconfigure(0, weight=1)
            
            if item['type'] == 'folder':
                # CARTELLA
                info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)
                
                display_name = item['name']
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."
                
                folder_label = ctk.CTkLabel(
                    info_frame,
                    text=f"📁 {display_name}",
                    font=ctk.CTkFont(size=10 if compact else 11, weight="bold"),
                    anchor="w"
                )
                folder_label.pack(anchor="w")
                
                # Marca questo frame come drop target per drag & drop
                item_frame._folder_drop_path = item['path']
                
                # Menu contestuale cartella
                folder_label.bind("<Button-3>", lambda e, p=item['path'], n=item['name']: self._show_folder_context_menu(e, p, n))
                
                # Drag and Drop - Cartella come DRAGGABLE (con parametri default per catturare valore)
                folder_label.bind("<ButtonPress-1>", lambda e, p=item['path'], n=item['name'], isf=True, w=item_frame: self._on_drag_start(e, p, n, isf, w))
                folder_label.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e))
                
                # Pulsante entra (solo se navigazione attiva)
                if show_navigation:
                    ctk.CTkButton(
                        item_frame,
                        text="➡️",
                        width=25,
                        height=22,
                        command=lambda p=item['path']: self._navigate_into(p),
                        fg_color=self.colors["accent"],
                        hover_color=self.colors["accent_hover"]
                    ).grid(row=0, column=1, padx=3, pady=3)
            else:
                # FILE AUDIO
                info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)
                
                display_name = item['name']
                if len(display_name) > (25 if compact else 35):
                    display_name = display_name[:(22 if compact else 32)] + "..."
                
                file_label = ctk.CTkLabel(
                    info_frame,
                    text=display_name,
                    font=ctk.CTkFont(size=9 if compact else 11),
                    anchor="w"
                )
                file_label.pack(anchor="w")
                
                # Menu contestuale file
                file_label.bind("<Button-3>", lambda e, p=item['path'], n=item['name']: self._show_file_context_menu(e, p, n))
                
                # Drag and Drop - File come DRAGGABLE (con parametri default per catturare valore)
                file_label.bind("<ButtonPress-1>", lambda e, p=item['path'], n=item['name'], isf=False, w=item_frame: self._on_drag_start(e, p, n, isf, w))
                file_label.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e))
                
                if not compact:
                    size_mb = item['size'] / (1024 * 1024)
                    ctk.CTkLabel(
                        info_frame,
                        text=f"{size_mb:.1f} MB",
                        font=ctk.CTkFont(size=8),
                        text_color=self.colors["text_muted"],
                        anchor="w"
                    ).pack(anchor="w")
                
                # Pulsanti azione
                btn_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                btn_frame.grid(row=0, column=1, padx=3, pady=3)
                
                ctk.CTkButton(
                    btn_frame,
                    text="▶️",
                    width=25 if compact else 35,
                    height=22,
                    command=lambda p=item['path'], n=item['name']: self._load_from_library(p, n),
                    fg_color=self.colors["success"],
                    hover_color="#059669"
                ).pack(side="left", padx=1)
                
                ctk.CTkButton(
                    btn_frame,
                    text="🗑️",
                    width=25,
                    height=22,
                    command=lambda p=item['path']: self._delete_from_library(p),
                    fg_color=self.colors["danger"],
                    hover_color="#b91c1c"
                ).pack(side="left", padx=1)
        
        # Forza rendering
        try:
            list_frame.update_idletasks()
        except:
            pass
    
    def _navigate_up(self):
        """Naviga alla cartella padre"""
        if hasattr(self, 'current_folder'):
            parent = os.path.dirname(self.current_folder)
            if parent and os.path.exists(parent):
                self.current_folder = parent
                # Aggiorna label percorso
                if hasattr(self, 'library_folder_label_tab'):
                    self.library_folder_label_tab.configure(text=f"📂 Cartella: {self.current_folder}")
                self._update_library_ui()
    
    def _navigate_into(self, folder_path):
        """Naviga dentro una cartella"""
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            self.current_folder = folder_path
            # Aggiorna label percorso
            if hasattr(self, 'library_folder_label_tab'):
                self.library_folder_label_tab.configure(text=f"📂 Cartella: {self.current_folder}")
            self._update_library_ui()
    
    def _on_search_changed(self, event=None):
        """Gestisce cambio ricerca"""
        if hasattr(self, 'search_entry'):
            self.search_filter = self.search_entry.get().strip()
            self._update_library_ui()
    
    def _clear_search(self):
        """Pulisce ricerca"""
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, 'end')
            self.search_filter = ""
            self._update_library_ui()
    
    def _create_new_folder(self):
        """Crea nuova cartella nella posizione corrente"""
        folder_name = simpledialog.askstring(
            "Nuova Cartella",
            "Nome della nuova cartella:",
            parent=self.parent
        )
        if folder_name:
            current = self.current_folder if hasattr(self, 'current_folder') else self.youtube_folder
            new_path = os.path.join(current, folder_name)
            try:
                os.makedirs(new_path, exist_ok=True)
                messagebox.showinfo("✓ Successo", f"Cartella '{folder_name}' creata!")
                self._update_library_ui()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare cartella: {str(e)}")
    
    def _show_folder_context_menu(self, event, folder_path, folder_name):
        """Mostra menu contestuale cartella"""
        menu = Menu(self.parent, tearoff=0)
        menu.add_command(label="📂 Apri", command=lambda: self._navigate_into(folder_path))
        menu.add_command(label="📂 Apri in Esplora File", command=lambda: self._open_in_explorer(folder_path))
        menu.add_separator()
        menu.add_command(label="✏️ Rinomina", command=lambda: self._rename_item(folder_path, folder_name, is_folder=True))
        menu.add_command(label="🗑️ Elimina", command=lambda: self._delete_folder(folder_path, folder_name))
        menu.add_separator()
        menu.add_command(label="ℹ️ Proprietà", command=lambda: self._show_properties(folder_path, is_folder=True))
        menu.tk_popup(event.x_root, event.y_root)
    
    def _show_file_context_menu(self, event, file_path, file_name):
        """Mostra menu contestuale file"""
        menu = Menu(self.parent, tearoff=0)
        menu.add_command(label="▶️ Carica", command=lambda: self._load_from_library(file_path, file_name))
        menu.add_command(label="📂 Apri in Esplora File", command=lambda: self._open_in_explorer(os.path.dirname(file_path)))
        menu.add_separator()
        menu.add_command(label="📋 Sposta in...", command=lambda: self._move_file(file_path, file_name))
        menu.add_command(label="📄 Copia in...", command=lambda: self._copy_file(file_path, file_name))
        menu.add_separator()
        menu.add_command(label="✏️ Rinomina", command=lambda: self._rename_item(file_path, file_name, is_folder=False))
        menu.add_command(label="🗑️ Elimina", command=lambda: self._delete_from_library(file_path))
        menu.add_separator()
        menu.add_command(label="ℹ️ Proprietà", command=lambda: self._show_properties(file_path, is_folder=False))
        menu.tk_popup(event.x_root, event.y_root)
    
    def _open_in_explorer(self, path):
        """Apre percorso in Esplora File"""
        try:
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                subprocess.Popen(f'explorer "{path}"')
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire: {str(e)}")
    
    def _rename_item(self, old_path, old_name, is_folder=False):
        """Rinomina file o cartella"""
        new_name = simpledialog.askstring(
            "Rinomina",
            f"Nuovo nome per '{old_name}':",
            initialvalue=old_name,
            parent=self.parent
        )
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                messagebox.showinfo("✓ Successo", f"Rinominato in '{new_name}'")
                self._load_youtube_library()
                self._update_library_ui()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile rinominare: {str(e)}")
    
    def _move_file(self, file_path, file_name):
        """Sposta file in altra cartella"""
        dest_folder = filedialog.askdirectory(
            title="Seleziona cartella destinazione",
            initialdir=self.youtube_folder
        )
        if dest_folder:
            dest_path = os.path.join(dest_folder, file_name)
            try:
                shutil.move(file_path, dest_path)
                messagebox.showinfo("✓ Successo", f"File spostato in {dest_folder}")
                self._load_youtube_library()
                self._update_library_ui()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile spostare: {str(e)}")
    
    def _copy_file(self, file_path, file_name):
        """Copia file in altra cartella"""
        dest_folder = filedialog.askdirectory(
            title="Seleziona cartella destinazione",
            initialdir=self.youtube_folder
        )
        if dest_folder:
            dest_path = os.path.join(dest_folder, file_name)
            try:
                shutil.copy2(file_path, dest_path)
                messagebox.showinfo("✓ Successo", f"File copiato in {dest_folder}")
                self._update_library_ui()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile copiare: {str(e)}")
    
    def _delete_folder(self, folder_path, folder_name):
        """Elimina cartella"""
        if messagebox.askyesno("Conferma", f"Eliminare la cartella '{folder_name}' e tutto il suo contenuto?"):
            try:
                shutil.rmtree(folder_path)
                messagebox.showinfo("✓ Successo", "Cartella eliminata")
                self._load_youtube_library()
                self._update_library_ui()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile eliminare: {str(e)}")
    
    def _show_properties(self, path, is_folder=False):
        """Mostra proprietà file/cartella"""
        try:
            name = os.path.basename(path)
            size = 0
            file_count = 0
            
            if is_folder:
                # Conta file e dimensione totale
                for root, dirs, files in os.walk(path):
                    file_count += len(files)
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp):
                            size += os.path.getsize(fp)
                info = f"📁 Cartella: {name}\n\n"
                info += f"File contenuti: {file_count}\n"
                info += f"Dimensione totale: {size / (1024*1024):.2f} MB\n"
            else:
                size = os.path.getsize(path)
                info = f"🎵 File: {name}\n\n"
                info += f"Dimensione: {size / (1024*1024):.2f} MB\n"
                
                # Info audio
                try:
                    data, sr = sf.read(path)
                    duration = len(data) / sr
                    info += f"Durata: {duration:.1f}s\n"
                    info += f"Sample Rate: {sr} Hz\n"
                    info += f"Canali: {data.shape[1] if len(data.shape) > 1 else 1}\n"
                except:
                    pass
            
            info += f"\nPercorso:\n{path}"
            messagebox.showinfo("Proprietà", info)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere proprietà: {str(e)}")
    
    def _on_drag_start(self, event, file_path, file_name, is_folder, widget):
        """Inizia drag operation"""
        print(f"🖱️ Drag START: {file_name}")
        self.drag_data = {
            'path': file_path,
            'name': file_name,
            'is_folder': is_folder,
            'widget': widget
        }
        self.drag_start_pos = (event.x, event.y)
        # Cambia aspetto widget durante drag
        try:
            widget.configure(fg_color=self.colors["accent"])
        except:
            pass
        
        # Avvia controllo periodico posizione mouse
        self._check_drag_position()
    
    def _check_drag_position(self):
        """Controlla periodicamente la posizione del mouse durante il drag"""
        if not self.drag_data:
            return
        
        try:
            # Ottieni widget sotto il mouse
            x_abs = self.parent.winfo_pointerx()
            y_abs = self.parent.winfo_pointery()
            target_widget = self.parent.winfo_containing(x_abs, y_abs)
            
            # Cerca attributo _folder_drop_path navigando fino a 10 parent
            target_folder = None
            target_frame = None
            
            if target_widget:
                check_widget = target_widget
                for _ in range(10):
                    if check_widget is None:
                        break
                    
                    # Controlla se ha l'attributo _folder_drop_path
                    if hasattr(check_widget, '_folder_drop_path'):
                        target_folder = check_widget._folder_drop_path
                        target_frame = check_widget
                        break
                    
                    try:
                        check_widget = check_widget.master
                    except:
                        break
            
            # Evidenzia cartella target
            if target_folder and target_folder != self.drag_data['path']:
                # Rimuovi evidenziazione precedente
                if self.highlighted_widget and self.highlighted_widget != target_frame:
                    try:
                        self.highlighted_widget.configure(fg_color=self.colors["bg_card"])
                    except:
                        pass
                
                # Evidenzia nuova cartella
                self.drop_target = target_folder
                self.highlighted_widget = target_frame
                try:
                    self.highlighted_widget.configure(fg_color=self.colors["success"])
                except:
                    pass
            else:
                # Nessun target valido, rimuovi evidenziazione
                if self.highlighted_widget:
                    try:
                        self.highlighted_widget.configure(fg_color=self.colors["bg_card"])
                    except:
                        pass
                    self.highlighted_widget = None
                self.drop_target = None
            
            # Richiama dopo 50ms
            self.drag_check_job = self.parent.after(50, self._check_drag_position)
        except:
            pass
    
    def _on_drag_motion(self, event):
        """Durante drag - NON PIU' USATO"""
        pass
    
    def _on_drag_release(self, event):
        """Fine drag operation"""
        # Ferma il controllo periodico
        if self.drag_check_job:
            try:
                self.parent.after_cancel(self.drag_check_job)
            except:
                pass
            self.drag_check_job = None
        
        print(f"🖱️ Drag RELEASE - Target: {os.path.basename(self.drop_target) if self.drop_target else 'None'}")
        
        if self.drag_data:
            # Ripristina aspetto widget trascinato
            try:
                if self.drag_data['widget'].winfo_exists():
                    self.drag_data['widget'].configure(fg_color=self.colors["bg_card"])
            except:
                pass
            
            # Ripristina aspetto cartella target
            if self.highlighted_widget:
                try:
                    self.highlighted_widget.configure(fg_color=self.colors["bg_card"])
                except:
                    pass
            
            # Se c'è un target, sposta il file/cartella
            if self.drop_target and os.path.exists(self.drop_target):
                src_path = self.drag_data['path']
                src_name = self.drag_data['name']
                dest_path = os.path.join(self.drop_target, src_name)
                
                # Evita spostamento su se stesso o dentro se stesso
                if os.path.dirname(src_path) != self.drop_target and src_path != self.drop_target:
                    try:
                        shutil.move(src_path, dest_path)
                        print(f"✓ '{src_name}' spostato in '{os.path.basename(self.drop_target)}'")
                        messagebox.showinfo("✓ Drag&Drop", f"'{src_name}' spostato in '{os.path.basename(self.drop_target)}'!")
                        self._load_youtube_library()
                        self._update_library_ui()
                    except Exception as e:
                        print(f"✗ Errore: {str(e)}")
                        messagebox.showerror("Errore Drag&Drop", f"Impossibile spostare: {str(e)}")
                else:
                    print("⚠️ Spostamento ignorato (stessa cartella o dentro se stesso)")
            
            # Reset
            self.drag_data = None
            self.drag_start_pos = None
            self.drop_target = None
            self.highlighted_widget = None
    
    def _on_drag_enter(self, event, folder_path, widget):
        """Mouse entra su cartella durante drag"""
        pass  # Non più usato, gestito in _on_drag_motion
    
    def _on_drag_leave(self, event, widget):
        """Mouse esce da cartella"""
        pass  # Non più usato, gestito in _on_drag_motion
    
    def _change_youtube_folder(self):
        """Cambia cartella YouTube"""
        from tkinter import filedialog
        new_folder = filedialog.askdirectory(title="Seleziona cartella YouTube")
        if new_folder:
            self.youtube_folder = new_folder
            # Salva nel config
            if hasattr(self.parent, 'save_config'):
                config = self.parent.load_config_dict()
                config['youtube_folder'] = new_folder
                with open(self.parent.config_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(config, f, indent=2, ensure_ascii=False)
            # Aggiorna label (basename per sidebar, path completo per altre UI)
            try:
                folder_text = f"📂 {os.path.basename(self.youtube_folder)}" if len(self.youtube_folder) > 40 else f"📂 Cartella: {self.youtube_folder}"
                self.library_folder_label.configure(text=folder_text)
            except:
                pass
            self._refresh_library()
    
    def _refresh_library(self):
        """Ricarica libreria"""
        print(f"🔄 Refresh libreria chiamato...")
        self._load_youtube_library()
        print(f"   File trovati: {len(self.youtube_library)}")
        # Forza aggiornamento UI nel thread principale
        try:
            if hasattr(self.parent, 'after'):
                self.parent.after(10, self._update_library_ui)  # Ridotto delay
            else:
                self._update_library_ui()
        except Exception as e:
            print(f"   Errore refresh: {e}")
            self._update_library_ui()
    
    def _load_from_library(self, file_path, title):
        """Carica file dalla libreria"""
        self.parent.after(100, lambda: self.parent._load_media_file(file_path, title))
    
    def _delete_from_library(self, file_path):
        """Elimina file dalla libreria"""
        from tkinter import messagebox
        if messagebox.askyesno("Conferma", f"Eliminare il file?\n\n{os.path.basename(file_path)}"):
            try:
                os.remove(file_path)
                self._refresh_library()
                messagebox.showinfo("✓ Eliminato", "File eliminato dalla libreria")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile eliminare file:\n{e}")
    
    def _create_preview_section(self):
        """Crea sezione preview e taglio"""
        ctk.CTkLabel(
            self.preview_container,
            text="✂️ Taglia & Anteprima",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 5), padx=15, anchor="w")
        
        # Durata totale
        self.duration_label = ctk.CTkLabel(
            self.preview_container,
            text="Durata: 0:00",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        )
        self.duration_label.pack(pady=5)
        
        # Waveform
        waveform_label = ctk.CTkLabel(
            self.preview_container,
            text="🎵 Forma d'onda (clicca per impostare inizio/fine):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        waveform_label.pack(pady=(10, 5), padx=15, anchor="w")
        
        canvas_container = ctk.CTkFrame(self.preview_container, fg_color=self.colors["bg_primary"], corner_radius=5)
        canvas_container.pack(fill="x", padx=15, pady=5)
        
        self.waveform_canvas = Canvas(
            canvas_container,
            height=120,
            bg=self.colors["bg_primary"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        self.waveform_canvas.pack(fill="x", padx=5, pady=5)
        self.waveform_canvas.bind("<Button-1>", self._on_waveform_click)
        self.waveform_canvas.bind("<B1-Motion>", self._on_waveform_drag)
        
        # Controlli tempo
        time_container = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        time_container.pack(fill="x", padx=15, pady=15)
        
        # Inizio
        left_col = ctk.CTkFrame(time_container, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(
            left_col,
            text="▶️ Inizio (mm:ss):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        self.start_entry = ctk.CTkEntry(
            left_col,
            placeholder_text="0:00",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.start_entry.pack(fill="x", pady=5)
        self.start_entry.bind("<KeyRelease>", lambda e: self._update_from_entries())
        
        # Fine
        right_col = ctk.CTkFrame(time_container, fg_color="transparent")
        right_col.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(
            right_col,
            text="⏸️ Fine (mm:ss):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        
        self.end_entry = ctk.CTkEntry(
            right_col,
            placeholder_text="Fine",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.end_entry.pack(fill="x", pady=5)
        self.end_entry.bind("<KeyRelease>", lambda e: self._update_from_entries())
        
        # Info durata selezione
        self.selection_info = ctk.CTkLabel(
            self.preview_container,
            text="Selezione: 0.00s",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["accent"]
        )
        self.selection_info.pack(pady=5)
        
        # Controlli playback
        playback_container = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        playback_container.pack(pady=15)
        
        self.play_btn = ctk.CTkButton(
            playback_container,
            text="▶️ Ascolta Selezione",
            command=self._toggle_playback,
            width=180,
            height=45,
            fg_color=self.colors["success"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.play_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            playback_container,
            text="⏹️ Stop",
            command=self._stop_playback,
            width=100,
            height=45,
            fg_color=self.colors["danger"]
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            playback_container,
            text="↩️ Reset",
            command=self._reset_selection,
            width=100,
            height=45,
            fg_color=self.colors["text_muted"]
        ).pack(side="left", padx=5)
        
        # Nome file
        name_container = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        name_container.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            name_container,
            text="📝 Nome file:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.filename_entry = ctk.CTkEntry(
            name_container,
            placeholder_text="nome_clip.mp3",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.filename_entry.pack(side="left", fill="x", expand=True)
        
        # Pulsante salva
        ctk.CTkButton(
            self.preview_container,
            text="💾 Salva Clip",
            command=self._save_clip,
            height=50,
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20, padx=50, fill="x")
    
    def download_and_preview(self):
        """Download audio e mostra preview"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Errore", "Inserisci un URL YouTube")
            return
        
        if not YT_DLP_AVAILABLE:
            messagebox.showerror("Errore", "yt-dlp non installato!\n\nInstalla con: pip install yt-dlp")
            return
        
        self.download_btn.configure(state="disabled", text="⏳ Download...")
        thread = Thread(target=self._download_thread, args=(url,), daemon=True)
        thread.start()
    
    def _download_thread(self, url):
        """Thread per download"""
        try:
            self.progress_label.configure(text="📥 Download video...")
            
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"yt_{int(time.time())}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self.video_title = info.get('title', 'audio')
            
            self.temp_file = temp_path + '.wav'
            
            self.progress_label.configure(text="📂 Caricamento audio...")
            self.audio_data, self.sample_rate = sf.read(self.temp_file)
            
            # Converti a mono per waveform
            if len(self.audio_data.shape) > 1:
                audio_mono = np.mean(self.audio_data, axis=1)
            else:
                audio_mono = self.audio_data
            
            self.duration = len(self.audio_data) / self.sample_rate
            
            self.parent.after(0, lambda: self._on_download_complete(audio_mono))
            
        except Exception as e:
            error_msg = str(e)
            if "blocked it in your country" in error_msg or "not available" in error_msg.lower():
                error_msg = "❌ Video non disponibile nella tua regione\n\nQuesto video è bloccato per copyright o geo-restrizioni."
            elif "video unavailable" in error_msg.lower():
                error_msg = "❌ Video non disponibile\n\nIl video potrebbe essere privato o rimosso."
            else:
                error_msg = f"Errore: {error_msg}"
            
            self.parent.after(0, lambda msg=error_msg: messagebox.showerror("Errore Download", msg))
            self.parent.after(0, lambda: self.download_btn.configure(state="normal", text="📥 Scarica & Mostra Waveform"))
            self.parent.after(0, lambda: self.progress_label.configure(text=""))
    
    def _on_download_complete(self, audio_mono):
        """Completamento download"""
        self.download_btn.configure(state="normal", text="✓ Download Completato")
        self.progress_label.configure(text=f"✓ {self.video_title}")
        
        # STOP playback precedente se attivo (importante!)
        if hasattr(self.parent, 'media_player_playing') and self.parent.media_player_playing:
            self.parent.stop_youtube()
        
        # Mostra preview
        self.preview_container.pack(fill="both", expand=True, pady=10)
        
        # Imposta valori
        mins = int(self.duration // 60)
        secs = int(self.duration % 60)
        self.duration_label.configure(text=f"Durata totale: {mins}:{secs:02d} ({self.duration:.2f}s)")
        
        self.start_time = 0
        self.end_time = self.duration
        
        self.start_entry.delete(0, 'end')
        self.start_entry.insert(0, "0:00")
        self.end_entry.delete(0, 'end')
        self.end_entry.insert(0, self._format_time(self.duration))
        
        # Nome file
        safe_title = "".join(c for c in self.video_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]  # Limita lunghezza
        self.filename_entry.delete(0, 'end')
        self.filename_entry.insert(0, f"{safe_title}.mp3")
        
        # Disegna waveform
        self._draw_waveform(audio_mono)
        self._update_selection_info()
    
    def _draw_waveform(self, audio_mono):
        """Disegna waveform"""
        self.waveform_canvas.delete("all")
        
        self.waveform_canvas.update_idletasks()
        width = self.waveform_canvas.winfo_width()
        if width <= 1:
            width = 800
        height = 120
        
        # Downsample
        samples_per_pixel = max(1, len(audio_mono) // width)
        downsampled = audio_mono[::samples_per_pixel]
        
        # Normalizza
        max_val = np.max(np.abs(downsampled))
        if max_val < 1e-10:
            max_val = 1.0
        normalized = downsampled / max_val
        
        # Disegna
        center_y = height / 2
        for i in range(len(normalized)):
            x = (i / len(normalized)) * width
            y_offset = normalized[i] * (height / 2 - 10)
            
            self.waveform_canvas.create_line(
                x, center_y - y_offset,
                x, center_y + y_offset,
                fill=self.colors["accent"], width=1
            )
        
        self._update_selection_overlay()
    
    def _update_selection_overlay(self):
        """Aggiorna overlay selezione"""
        self.waveform_canvas.delete("selection")
        
        width = self.waveform_canvas.winfo_width()
        if width <= 1:
            width = 800
        height = 120
        
        if self.duration == 0:
            return
        
        x_start = (self.start_time / self.duration) * width
        x_end = (self.end_time / self.duration) * width
        
        # Area selezionata con pattern semi-trasparente
        self.waveform_canvas.create_rectangle(
            x_start, 0, x_end, height,
            fill=self.colors["success"], stipple="gray25",
            outline="", width=0, tags="selection"
        )
        
        # Linee verticali per start e end
        self.waveform_canvas.create_line(
            x_start, 0, x_start, height,
            fill=self.colors["success"], width=3, tags="selection"
        )
        self.waveform_canvas.create_line(
            x_end, 0, x_end, height,
            fill=self.colors["danger"], width=3, tags="selection"
        )
        
        # Labels
        self.waveform_canvas.create_text(
            x_start, 10,
            text=f"▶ {self._format_time(self.start_time)}",
            fill=self.colors["success"],
            font=("Arial", 10, "bold"),
            anchor="nw", tags="selection"
        )
        self.waveform_canvas.create_text(
            x_end, 10,
            text=f"⏸ {self._format_time(self.end_time)}",
            fill=self.colors["danger"],
            font=("Arial", 10, "bold"),
            anchor="ne", tags="selection"
        )
    
    def _on_waveform_click(self, event):
        """Click su waveform"""
        if self.duration == 0:
            return
        
        width = self.waveform_canvas.winfo_width()
        ratio = event.x / width
        click_time = max(0, min(ratio * self.duration, self.duration))
        
        # Se in riproduzione, sposta la posizione di playback (seek)
        if self.is_playing:
            self.playback_position = click_time
            self.playback_start_time = time.time() - (click_time - self.start_time)
            
            # Ferma e riavvia da nuova posizione
            try:
                sd.stop()
            except:
                pass
            
            start_sample = int(click_time * self.sample_rate)
            end_sample = int(self.end_time * self.sample_rate)
            
            if len(self.audio_data.shape) > 1:
                segment = self.audio_data[start_sample:end_sample, :]
            else:
                segment = self.audio_data[start_sample:end_sample]
            
            def play():
                try:
                    sd.play(segment, self.sample_rate)
                    sd.wait()
                    self.parent.after(0, self._stop_playback)
                except Exception as e:
                    print(f"Errore playback: {e}")
                    self.parent.after(0, self._stop_playback)
            
            self.playback_thread = Thread(target=play, daemon=True)
            self.playback_thread.start()
            return
        
        # Altrimenti, modifica selezione come prima
        # Determina se settare start o end
        dist_start = abs(click_time - self.start_time)
        dist_end = abs(click_time - self.end_time)
        
        if dist_start < dist_end:
            self.start_time = click_time
            self.start_entry.delete(0, 'end')
            self.start_entry.insert(0, self._format_time(click_time))
        else:
            self.end_time = click_time
            self.end_entry.delete(0, 'end')
            self.end_entry.insert(0, self._format_time(click_time))
        
        # Assicura start < end
        if self.start_time >= self.end_time:
            self.start_time, self.end_time = self.end_time, self.start_time
            self.start_entry.delete(0, 'end')
            self.start_entry.insert(0, self._format_time(self.start_time))
            self.end_entry.delete(0, 'end')
            self.end_entry.insert(0, self._format_time(self.end_time))
        
        self._update_selection_overlay()
        self._update_selection_info()
    
    def _on_waveform_drag(self, event):
        """Drag su waveform"""
        self._on_waveform_click(event)
    
    def _update_from_entries(self):
        """Aggiorna da input manuale"""
        try:
            start_val = self.start_entry.get().strip()
            if start_val:
                self.start_time = max(0, min(self._parse_time(start_val), self.duration))
            
            end_val = self.end_entry.get().strip()
            if end_val:
                self.end_time = max(0, min(self._parse_time(end_val), self.duration))
            
            if self.start_time >= self.end_time:
                self.end_time = min(self.duration, self.start_time + 1)
                self.end_entry.delete(0, 'end')
                self.end_entry.insert(0, self._format_time(self.end_time))
            
            self._update_selection_overlay()
            self._update_selection_info()
        except ValueError:
            pass
    
    def _update_selection_info(self):
        """Aggiorna info selezione"""
        duration = self.end_time - self.start_time
        self.selection_info.configure(text=f"📏 Selezione: {self._format_time(duration)} ({self._format_time(self.start_time)} → {self._format_time(self.end_time)})")
    
    def _reset_selection(self):
        """Reset selezione completa"""
        self.start_time = 0
        self.end_time = self.duration
        self.start_entry.delete(0, 'end')
        self.start_entry.insert(0, "0:00")
        self.end_entry.delete(0, 'end')
        self.end_entry.insert(0, self._format_time(self.duration))
        self._update_selection_overlay()
        self._update_selection_info()
    
    def _toggle_playback(self):
        """Toggle playback"""
        if self.is_playing:
            self._stop_playback()
        else:
            self._start_playback()
    
    def _start_playback(self):
        """Avvia playback"""
        if self.audio_data is None:
            return
        
        # Ferma qualsiasi playback in corso
        try:
            sd.stop()
        except:
            pass
        
        # Cancella update job precedente
        if self.playback_update_job:
            try:
                self.parent.after_cancel(self.playback_update_job)
            except:
                pass
        
        self.is_playing = True
        self.play_btn.configure(text="⏸️ In Riproduzione...")
        self.playback_position = self.start_time
        
        start_sample = int(self.start_time * self.sample_rate)
        end_sample = int(self.end_time * self.sample_rate)
        
        if len(self.audio_data.shape) > 1:
            segment = self.audio_data[start_sample:end_sample, :]
        else:
            segment = self.audio_data[start_sample:end_sample]
        
        # Avvia aggiornamento progressione
        self.playback_start_time = time.time()
        self._update_playback_progress()
        
        def play():
            try:
                sd.play(segment, self.sample_rate)
                sd.wait()
                self.parent.after(0, self._stop_playback)
            except Exception as e:
                print(f"Errore playback: {e}")
                self.parent.after(0, self._stop_playback)
        
        self.playback_thread = Thread(target=play, daemon=True)
        self.playback_thread.start()
    
    def _update_playback_progress(self):
        """Aggiorna linea di progressione durante playback"""
        if not self.is_playing:
            return
        
        # Calcola posizione corrente
        elapsed = time.time() - self.playback_start_time
        self.playback_position = self.start_time + elapsed
        
        if self.playback_position <= self.end_time:
            # Disegna linea di progressione
            self._draw_playback_line()
            # Continua aggiornamento
            self.playback_update_job = self.parent.after(50, self._update_playback_progress)
        else:
            self.playback_position = self.end_time
    
    def _draw_playback_line(self):
        """Disegna linea di progressione sul canvas"""
        self.waveform_canvas.delete("playback_line")
        
        width = self.waveform_canvas.winfo_width()
        if width <= 1:
            width = 800
        height = 120
        
        if self.duration == 0:
            return
        
        x_pos = (self.playback_position / self.duration) * width
        
        # Linea blu di progressione
        self.waveform_canvas.create_line(
            x_pos, 0, x_pos, height,
            fill="#2196F3", width=2, tags="playback_line"
        )
    
    def _stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        self.play_btn.configure(text="▶️ Ascolta Selezione")
        
        # Cancella update job
        if self.playback_update_job:
            try:
                self.parent.after_cancel(self.playback_update_job)
            except:
                pass
        
        # Rimuovi linea di progressione
        self.waveform_canvas.delete("playback_line")
        
        try:
            sd.stop()
        except Exception as e:
            print(f"Errore stop playback: {e}")
    
    def _save_clip(self):
        """Salva clip nella cartella YouTube"""
        if self.audio_data is None:
            messagebox.showerror("Errore", "Nessun audio caricato")
            return
        
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("Errore", "Inserisci nome file")
            return
        
        if not filename.lower().endswith(('.mp3', '.wav')):
            filename += '.mp3'
        
        # Salva nella cartella YouTube
        output_path = os.path.join(self.youtube_folder, filename)
        
        start_sample = int(self.start_time * self.sample_rate)
        end_sample = int(self.end_time * self.sample_rate)
        
        if len(self.audio_data.shape) > 1:
            segment = self.audio_data[start_sample:end_sample, :]
        else:
            segment = self.audio_data[start_sample:end_sample]
        
        try:
            temp_wav = output_path.replace('.mp3', '_temp.wav')
            sf.write(temp_wav, segment, self.sample_rate)
            
            if filename.lower().endswith('.mp3'):
                ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-essentials_build', 'bin', 'ffmpeg.exe')
                subprocess.run([
                    ffmpeg, '-i', temp_wav,
                    '-codec:a', 'libmp3lame', '-qscale:a', '2',
                    '-y', output_path
                ], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                os.remove(temp_wav)
            else:
                os.rename(temp_wav, output_path)
            
            duration = self.end_time - self.start_time
            messagebox.showinfo(
                "✓ Clip Salvata",
                f"File: {filename}\nDurata: {duration:.2f}s\nCartella: youtube_downloads/\n\nLa clip è disponibile nella Libreria YouTube!"
            )
            
            # Aggiorna libreria
            self._refresh_library()
            
            # NON aggiungere alla soundboard, solo alla libreria YouTube
            # if self.on_download_complete:
            #     self.on_download_complete(output_path)
            
            # Reset
            self.preview_container.pack_forget()
            self.download_btn.configure(text="📥 Scarica & Mostra Waveform")
            self.progress_label.configure(text="")
            self.url_entry.delete(0, 'end')
            
            # Cleanup temp
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except:
                    pass
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore salvataggio:\n{str(e)}")
