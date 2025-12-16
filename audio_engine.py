"""
Audio Engine - Gestisce il processamento audio in tempo reale
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal
import threading
import queue
from typing import Dict, List, Optional


class AudioClip:
    """Rappresenta una clip audio con controlli"""
    def __init__(self, file_path: str, name: str, target_sample_rate: int = None):
        self.name = name
        self.file_path = file_path
        
        # Carica il file audio
        self.samples, self.sample_rate = sf.read(file_path, dtype='float32')
        
        print(f"📀 {name}: {int(self.sample_rate)}Hz", end="")
        
        # Converti a stereo se necessario
        if len(self.samples.shape) == 1:
            self.samples = np.column_stack([self.samples, self.samples])
        
        # RESAMPLE se necessario
        if target_sample_rate and target_sample_rate != self.sample_rate:
            print(f"   ⚠️ Resampling: {self.sample_rate}Hz → {target_sample_rate}Hz")
            from scipy.signal import resample_poly
            from math import gcd
            
            g = gcd(target_sample_rate, int(self.sample_rate))
            up = target_sample_rate // g
            down = int(self.sample_rate) // g
            
            print(f"   Up={up}, Down={down}, GCD={g}")
            
            # Resample ogni canale separatamente (senza log verbose)
            resampled_channels = []
            for ch in range(2):
                resampled_ch = resample_poly(self.samples[:, ch], up, down)
                resampled_channels.append(resampled_ch)
            
            # Stack i canali
            self.samples = np.column_stack(resampled_channels).astype(np.float32)
            self.sample_rate = target_sample_rate
            print(f" ✓")
        
        self.volume = 1.0
        self.is_playing = False
        self.is_looping = False
        # Dizionario di posizioni: una per ogni stream/bus che accede alla clip
        # Chiavi: 'primary', 'secondary', 'A1', 'A2', 'A3', 'A4', 'A5'
        self.positions = {}
        self.hotkey = None
        self.lock = threading.Lock()  # Lock per thread-safety con dual output
    
    def play(self):
        """Avvia la riproduzione"""
        self.is_playing = True
        # Reset tutte le posizioni per tutti gli stream
        self.positions = {}
    
    def stop(self):
        """Ferma la riproduzione"""
        self.is_playing = False
        # Reset tutte le posizioni
        self.positions = {}
    
    def get_samples(self, n_frames: int, stream_id: str = 'primary') -> np.ndarray:
        """Restituisce n_frames campioni dalla posizione corrente (thread-safe)"""
        with self.lock:
            if not self.is_playing:
                return np.zeros((n_frames, 2))
            
            # Ottieni/inizializza posizione per questo stream
            if stream_id not in self.positions:
                self.positions[stream_id] = 0
            
            current_pos = self.positions[stream_id]
            end_pos = min(current_pos + n_frames, len(self.samples))
            samples = self.samples[current_pos:end_pos].copy()
            
            # Applica volume
            samples *= self.volume
            
            # Converti a stereo se necessario
            if samples.shape[1] == 1:
                samples = np.repeat(samples, 2, axis=1)
            elif samples.ndim == 1:
                samples = np.column_stack([samples, samples])
            
            # Aggiorna posizione per questo stream
            self.positions[stream_id] = end_pos
            
            # Gestisci looping
            if self.positions[stream_id] >= len(self.samples):
                if self.is_looping:
                    self.positions[stream_id] = 0
                else:
                    self.is_playing = False
            
            # Pad se necessario
            if len(samples) < n_frames:
                padding = np.zeros((n_frames - len(samples), 2))
                samples = np.vstack([samples, padding])
            
            return samples


class AudioEffects:
    """Effetti audio applicabili al mix"""
    
    @staticmethod
    def reverb(audio: np.ndarray, room_size: float = 0.5, damping: float = 0.5) -> np.ndarray:
        """Applica riverbero semplice"""
        delay_samples = int(0.05 * 44100)  # 50ms delay
        output = audio.copy()
        
        if len(audio) > delay_samples:
            delayed = np.zeros_like(audio)
            delayed[delay_samples:] = audio[:-delay_samples] * room_size * damping
            output = audio + delayed
        
        return output
    
    @staticmethod
    def eq_bass(audio: np.ndarray, gain: float = 1.0, sample_rate: int = 44100) -> np.ndarray:
        """Equalizzatore bassi (low-shelf filter)"""
        if gain == 1.0:
            return audio
        
        # Filtro passa-basso semplice a 200Hz
        sos = signal.butter(2, 200, 'low', fs=sample_rate, output='sos')
        bass = signal.sosfilt(sos, audio, axis=0)
        
        return audio + bass * (gain - 1.0)


class AudioMixer:
    """Mixer audio principale"""
    
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024, virtual_output_callback=None):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.virtual_output_callback = virtual_output_callback  # Callback per ProMixer
        self.clips: Dict[str, AudioClip] = {}
        self.master_volume = 1.0
        self.secondary_volume = 1.0  # Volume separato per bus secondari (A2+)
        self.is_recording = False
        self.recorded_frames = []
        
        # Effetti
        self.reverb_enabled = False
        self.reverb_amount = 0.3
        self.bass_boost = 1.0
        
    def add_clip(self, clip: AudioClip):
        """Aggiunge una clip al mixer"""
        self.clips[clip.name] = clip
    
    def remove_clip(self, name: str):
        """Rimuove una clip dal mixer"""
        if name in self.clips:
            del self.clips[name]
    
    # === CALLBACK RIMOSSI ===
    # AudioMixer funziona SOLO in modalità ProMixer integrato
    # Il ProMixer chiama direttamente get_audio() - nessun callback necessario
    
    def get_audio(self, frames: int, stream_id: str = 'primary') -> np.ndarray:
        """Metodo pubblico per ottenere audio (chiamato dal ProMixer)
        
        Args:
            frames: Numero di frame da generare
            stream_id: Identificativo dello stream (es: 'A1', 'A2', 'primary')
        """
        return self._generate_mix(frames, stream_id=stream_id)
    
    def _generate_mix(self, frames: int, stream_id: str = 'primary') -> np.ndarray:
        """Genera il mix audio (usato sia per device che per virtual output)"""
        mix = np.zeros((frames, 2), dtype=np.float32)
        
        for clip in self.clips.values():
            if clip.is_playing:
                clip_samples = clip.get_samples(frames, stream_id=stream_id)
                mix += clip_samples
        
        # Applica effetti
        if self.reverb_enabled:
            mix = AudioEffects.reverb(mix, self.reverb_amount)
        
        if self.bass_boost != 1.0:
            mix = AudioEffects.eq_bass(mix, self.bass_boost, self.sample_rate)
        
        # Applica master volume
        # 'secondary' o 'A2' e superiori usano volume secondario
        if stream_id == 'secondary' or (stream_id.startswith('A') and stream_id != 'A1'):
            mix *= self.master_volume * self.secondary_volume
        else:
            mix *= self.master_volume
        
        # Limiter per evitare clipping
        mix = np.clip(mix, -1.0, 1.0)
        
        # Registrazione (solo dal primario/A1)
        if stream_id in ('primary', 'A1') and self.is_recording:
            self.recorded_frames.append(mix.copy())
        
        return mix
    

    
    def start(self):
        """Avvia lo stream audio - Modalità SOLO ProMixer integrato"""
        # AudioMixer funziona SOLO in modalità integrata con ProMixer
        # Il ProMixer chiamerà get_audio() quando serve
        if not self.virtual_output_callback:
            print("❌ ERRORE: AudioMixer deve essere collegato a ProMixer!")
            print("   Imposta virtual_output_callback prima di chiamare start()")
            return
        
        print("✓ AudioMixer in modalità ProMixer integrato")
        print("   → L'audio verrà gestito dai bus del ProMixer")
    
    def stop(self):
        """Ferma lo stream audio"""
        # In modalità ProMixer integrato, non c'è nulla da fermare qui
        # Il ProMixer gestisce i suoi stream
        pass
    
    def start_recording(self):
        """Avvia la registrazione"""
        self.is_recording = True
        self.recorded_frames = []
    
    def stop_recording(self, output_path: str = "output.wav"):
        """Ferma la registrazione e salva il file"""
        self.is_recording = False
        
        if self.recorded_frames:
            # Concatena tutti i frame
            recording = np.vstack(self.recorded_frames)
            
            # Converti in int16
            recording = (recording * 32767).astype(np.int16)
            
            # Salva usando scipy
            from scipy.io import wavfile
            wavfile.write(output_path, self.sample_rate, recording)
            
            self.recorded_frames = []
            return output_path
        
        return None
