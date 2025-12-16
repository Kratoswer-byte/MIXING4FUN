"""Custom widget for audio clip buttons"""
import customtkinter as ctk
from tkinter import messagebox
import logging

from .colors import COLORS

logger = logging.getLogger(__name__)


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
        """Override destroy per prevenire errori"""
        self._is_destroyed = True
        super().destroy()
