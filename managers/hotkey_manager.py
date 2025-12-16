"""
Gestione hotkey per soundboard
"""
import keyboard
import logging
from typing import Dict, Optional, Callable, Tuple

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Gestisce l'assegnazione e rimozione degli hotkey"""
    
    def __init__(self):
        self.hotkey_bindings: Dict[str, str] = {}
        self.hotkey_hooks: Dict = {}
        self.waiting_for_hotkey: Optional[Tuple] = None
        self.temp_listener = None
        self.captured_keys = []
        self.modifier_keys = set()
        self.assignment_timer = None
    
    def start_hotkey_assignment(self, clip_name: str, widget, trigger_callback: Callable, after_callback: Callable):
        """Inizia l'assegnazione di una hotkey"""
        self.waiting_for_hotkey = (clip_name, widget)
        widget.set_hotkey("Premi un tasto...")
        
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
                    after_callback(0, lambda: None)  # Cancel
                
                # Aspetta 1.5 secondi: se non arriva un tasto principale, ignora
                def modifier_timeout():
                    if self.temp_listener:
                        keyboard.unhook(self.temp_listener)
                        self.temp_listener = None
                    widget.set_hotkey("Solo modificatori - riprova")
                    logger.debug("Solo modificatori premuti, operazione annullata")
                    self.waiting_for_hotkey = None
                    self.modifier_keys = set()
                
                self.assignment_timer = after_callback(1500, modifier_timeout)
                return
            
            # È un tasto normale/numpad - cattura IMMEDIATAMENTE
            logger.debug(f"Tasto principale: {event.name} (scan: {event.scan_code}), modificatori: {list(self.modifier_keys)}")
            
            # Cancella il timer se esisteva
            if self.assignment_timer:
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
            
            # Processa SUBITO
            after_callback(0, lambda: self._process_captured_hotkey(clip_name, widget, trigger_callback, after_callback))
        
        # Registra listener temporaneo
        self.temp_listener = keyboard.hook(on_key_capture)
    
    def _process_captured_hotkey(self, clip_name, widget, trigger_callback, save_callback):
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
                combo = '+'.join(modifiers + [display_name.lower()])
                storage_key = f"combo_scan_{scan_code}_{'_'.join(modifiers)}"
                self._assign_combo_with_numpad(clip_name, widget, combo, storage_key, scan_code, modifiers, trigger_callback, save_callback)
            else:
                storage_key = f"scan_{scan_code}"
                self._assign_single_numpad(clip_name, widget, storage_key, display_name, scan_code, trigger_callback, save_callback)
        else:
            # Tasto normale
            if modifiers:
                combo = '+'.join(modifiers + [key_name])
                self._assign_combo_normal(clip_name, widget, combo, trigger_callback, save_callback)
            else:
                storage_key = f"key_{key_name}"
                self._assign_single_key(clip_name, widget, storage_key, key_name, trigger_callback, save_callback)
        
        self.captured_keys = []
        self.modifier_keys = set()
        self.waiting_for_hotkey = None
    
    def _remove_old_hotkey(self, clip_name):
        """Rimuove un vecchio hotkey se esiste"""
        if clip_name not in self.hotkey_bindings:
            return
        
        old_key = self.hotkey_bindings[clip_name]
        
        if clip_name in self.hotkey_hooks:
            try:
                hook_ref = self.hotkey_hooks[clip_name]
                keyboard.unhook(hook_ref)
                logger.debug(f"Rimosso hook per {clip_name} (key: {old_key})")
                del self.hotkey_hooks[clip_name]
            except Exception as e:
                logger.debug(f"Errore rimozione hook {old_key}: {e}")
        
        if clip_name in self.hotkey_bindings:
            del self.hotkey_bindings[clip_name]
    
    def _assign_single_numpad(self, clip_name, widget, storage_key, display_name, scan_code, trigger_callback, save_callback):
        """Assegna un tasto numpad singolo"""
        try:
            self._remove_old_hotkey(clip_name)
            
            def callback(e, name=clip_name):
                if e.event_type == 'down':
                    if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                        trigger_callback(name)
            
            hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(display_name)
            
            logger.info(f"Hotkey numpad '{display_name}' (scan {scan_code}) assegnato a '{clip_name}'")
            save_callback()
        except Exception as e:
            logger.error(f"Errore assegnazione numpad: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _assign_single_key(self, clip_name, widget, storage_key, key_name, trigger_callback, save_callback):
        """Assegna un tasto singolo normale"""
        try:
            self._remove_old_hotkey(clip_name)
            
            def callback(e, name=clip_name):
                if e.event_type == 'down':
                    if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                        trigger_callback(name)
            
            hook_ref = keyboard.hook_key(key_name, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(key_name)
            
            logger.info(f"Hotkey '{key_name}' assegnato a '{clip_name}'")
            save_callback()
        except Exception as e:
            logger.error(f"Errore assegnazione tasto: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _assign_combo_normal(self, clip_name, widget, combo, trigger_callback, save_callback):
        """Assegna una combinazione normale"""
        try:
            self._remove_old_hotkey(clip_name)
            
            keyboard.add_hotkey(combo, lambda name=clip_name: trigger_callback(name), suppress=False)
            self.hotkey_bindings[clip_name] = combo
            self.hotkey_hooks[clip_name] = combo
            widget.set_hotkey(combo)
            
            logger.info(f"Hotkey combinazione '{combo}' assegnato a '{clip_name}'")
            logger.warning("Le combinazioni potrebbero non funzionare in alcuni giochi")
            save_callback()
        except Exception as e:
            logger.error(f"Errore assegnazione combinazione: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _assign_combo_with_numpad(self, clip_name, widget, combo, storage_key, scan_code, modifiers, trigger_callback, save_callback):
        """Assegna una combinazione con numpad"""
        try:
            self._remove_old_hotkey(clip_name)
            
            def callback(e, name=clip_name, mods=modifiers):
                if e.event_type == 'down':
                    all_pressed = all(keyboard.is_pressed(mod) for mod in mods)
                    if all_pressed:
                        trigger_callback(name)
            
            hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
            self.hotkey_bindings[clip_name] = storage_key
            self.hotkey_hooks[clip_name] = hook_ref
            widget.set_hotkey(combo)
            
            logger.info(f"Hotkey combinazione numpad '{combo}' assegnato a '{clip_name}'")
            save_callback()
        except Exception as e:
            logger.error(f"Errore assegnazione combinazione numpad: {e}", exc_info=True)
            widget.set_hotkey("Errore")
    
    def _get_numpad_display_name(self, scan_code: int) -> str:
        """Ottiene il nome display per un numpad scan code"""
        numpad_scancodes = {
            71: 'Numpad 7', 72: 'Numpad 8', 73: 'Numpad 9',
            75: 'Numpad 4', 76: 'Numpad 5', 77: 'Numpad 6',
            79: 'Numpad 1', 80: 'Numpad 2', 81: 'Numpad 3',
            82: 'Numpad 0', 83: 'Numpad .',
            78: 'Numpad +', 74: 'Numpad -', 55: 'Numpad *', 53: 'Numpad /'
        }
        return numpad_scancodes.get(scan_code, f"Scan {scan_code}")
    
    def restore_hotkeys_from_config(self, config: dict, clip_widgets: dict, trigger_callback: Callable):
        """Ripristina gli hotkey dalla configurazione"""
        for clip_name, clip_data in config.get('clips', {}).items():
            hotkey = clip_data.get('hotkey')
            if hotkey and clip_name in clip_widgets:
                clip_widget = clip_widgets[clip_name]
                try:
                    if hotkey.startswith('combo_scan_'):
                        # Combinazione numpad
                        parts = hotkey.replace('combo_scan_', '').split('_')
                        scan_code = int(parts[0])
                        modifiers = parts[1:] if len(parts) > 1 else []
                        
                        def callback(e, name=clip_name, mods=modifiers):
                            if e.event_type == 'down':
                                all_pressed = all(keyboard.is_pressed(mod) for mod in mods)
                                if all_pressed:
                                    trigger_callback(name)
                        
                        hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
                        self.hotkey_bindings[clip_name] = hotkey
                        self.hotkey_hooks[clip_name] = hook_ref
                        display = self._get_numpad_display_name(scan_code)
                        if modifiers:
                            display = '+'.join(modifiers + [display])
                        clip_widget.set_hotkey(display)
                        
                    elif hotkey.startswith('scan_'):
                        # Numpad singolo
                        scan_code = int(hotkey.replace('scan_', ''))
                        
                        def callback(e, name=clip_name):
                            if e.event_type == 'down':
                                if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                                    trigger_callback(name)
                        
                        hook_ref = keyboard.hook_key(scan_code, callback, suppress=False)
                        self.hotkey_bindings[clip_name] = hotkey
                        self.hotkey_hooks[clip_name] = hook_ref
                        clip_widget.set_hotkey(self._get_numpad_display_name(scan_code))
                        
                    elif hotkey.startswith('key_'):
                        # Tasto singolo normale
                        key_name = hotkey.replace('key_', '')
                        
                        def callback(e, name=clip_name):
                            if e.event_type == 'down':
                                if not any(keyboard.is_pressed(mod) for mod in ['shift', 'ctrl', 'alt']):
                                    trigger_callback(name)
                        
                        hook_ref = keyboard.hook_key(key_name, callback, suppress=False)
                        self.hotkey_bindings[clip_name] = hotkey
                        self.hotkey_hooks[clip_name] = hook_ref
                        clip_widget.set_hotkey(key_name)
                        
                    else:
                        # Combinazione normale o vecchio formato
                        keyboard.add_hotkey(hotkey, lambda name=clip_name: trigger_callback(name), suppress=False)
                        self.hotkey_bindings[clip_name] = hotkey
                        self.hotkey_hooks[clip_name] = hotkey
                        clip_widget.set_hotkey(hotkey)
                except Exception as e:
                    logger.error(f"Errore ripristino hotkey {hotkey}: {e}", exc_info=True)
    
    def cleanup(self):
        """Rimuove tutti gli hotkey"""
        for clip_name in list(self.hotkey_bindings.keys()):
            try:
                if clip_name in self.hotkey_hooks:
                    hook_ref = self.hotkey_hooks[clip_name]
                    if isinstance(hook_ref, str):
                        keyboard.remove_hotkey(hook_ref)
                    else:
                        keyboard.unhook(hook_ref)
                    logger.debug(f"Rimosso hotkey per {clip_name}")
            except Exception as e:
                logger.debug(f"Errore rimozione hotkey per {clip_name}: {e}")
