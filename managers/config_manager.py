"""
Gestione configurazione soundboard
"""
import json
import os
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gestisce il caricamento e salvataggio della configurazione"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
    
    def load_config_dict(self) -> dict:
        """Carica configurazione da file JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Errore caricamento config: {e}")
                return {}
        return {}
    
    def save_config(self, app) -> None:
        """Salva configurazione su file JSON"""
        try:
            config = {
                'clips': {},
                'audio_output_device': getattr(app.mixer, 'output_device', None),
                'secondary_output_device': getattr(app.mixer, 'secondary_output_device', None),
                'clips_folder': app.clips_folder,
                'clip_pages': app.clip_pages
            }
            
            # Salva info su ogni clip
            for clip_name, widget in app.clip_widgets.items():
                if clip_name in app.mixer.clips:
                    clip = app.mixer.clips[clip_name]
                    hotkey = app.hotkey_bindings.get(clip_name, None)
                    
                    config['clips'][clip_name] = {
                        'file_path': clip.file_path,
                        'volume': clip.volume,
                        'hotkey': hotkey,
                        'page': app.clip_pages.get(clip_name, 1)
                    }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configurazione salvata: {len(config['clips'])} clip")
        except Exception as e:
            logger.error(f"Errore salvataggio config: {e}", exc_info=True)
