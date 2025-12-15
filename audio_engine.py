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
    def __init__(self, file_path: str, name: str):
        self.name = name
        self.file_path = file_path
        
        # Carica il file audio
        self.samples, self.sample_rate = sf.read(file_path, dtype='float32')
        
        # Converti a stereo se necessario
        if len(self.samples.shape) == 1:
            self.samples = np.column_stack([self.samples, self.samples])
        
        self.volume = 1.0
        self.is_playing = False
        self.is_looping = False
        self.position = 0  # Posizione per stream primario
        self.position_secondary = 0  # Posizione separata per stream secondario
        self.hotkey = None
        self.lock = threading.Lock()  # Lock per thread-safety con dual output
    
    def play(self):
        """Avvia la riproduzione"""
        self.is_playing = True
        self.position = 0
        self.position_secondary = 0  # Reset anche posizione secondaria
    
    def stop(self):
        """Ferma la riproduzione"""
        self.is_playing = False
        self.position = 0
        self.position_secondary = 0  # Reset anche posizione secondaria
    
    def get_samples(self, n_frames: int, is_secondary: bool = False) -> np.ndarray:
        """Restituisce n_frames campioni dalla posizione corrente (thread-safe)"""
        with self.lock:
            if not self.is_playing:
                return np.zeros((n_frames, 2))
            
            # Usa posizione corretta in base allo stream
            current_pos = self.position_secondary if is_secondary else self.position
            
            end_pos = min(current_pos + n_frames, len(self.samples))
            samples = self.samples[current_pos:end_pos].copy()
            
            # Applica volume
            samples *= self.volume
            
            # Converti a stereo se necessario
            if samples.shape[1] == 1:
                samples = np.repeat(samples, 2, axis=1)
            elif samples.ndim == 1:
                samples = np.column_stack([samples, samples])
            
            # Aggiorna posizione corretta
            if is_secondary:
                self.position_secondary = end_pos
            else:
                self.position = end_pos
            
            # Gestisci looping
            if (is_secondary and self.position_secondary >= len(self.samples)) or \
               (not is_secondary and self.position >= len(self.samples)):
                if self.is_looping:
                    if is_secondary:
                        self.position_secondary = 0
                    else:
                        self.position = 0
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
    
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024, output_device=None, secondary_output_device=None):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.output_device = output_device  # None = default, altrimenti ID dispositivo
        self.secondary_output_device = secondary_output_device  # Secondo output (es. cuffie)
        self.secondary_sample_rate = None  # Sample rate del dispositivo secondario
        self.clips: Dict[str, AudioClip] = {}
        self.mic_volume = 0.8
        self.master_volume = 1.0
        self.secondary_volume = 1.0  # Volume separato per output secondario
        self.is_recording = False
        self.recorded_frames = []
        self.stream = None
        self.secondary_stream = None
        
        # Effetti
        self.reverb_enabled = False
        self.reverb_amount = 0.3
        self.bass_boost = 1.0
        
        # Input devices
        self.mic_enabled = True
        
    def add_clip(self, clip: AudioClip):
        """Aggiunge una clip al mixer"""
        self.clips[clip.name] = clip
    
    def remove_clip(self, name: str):
        """Rimuove una clip dal mixer"""
        if name in self.clips:
            del self.clips[name]
    
    def audio_callback(self, indata, outdata, frames, time, status):
        """Callback per il processamento audio in tempo reale"""
        if status:
            print(f"Audio status: {status}")
        
        # Mix delle clip
        mix = np.zeros((frames, 2), dtype=np.float32)
        
        for clip in self.clips.values():
            if clip.is_playing:
                clip_samples = clip.get_samples(frames)
                mix += clip_samples
        
        # Aggiungi input microfono
        if self.mic_enabled and indata is not None:
            mic_input = indata.copy()
            if mic_input.shape[1] == 1:
                mic_input = np.repeat(mic_input, 2, axis=1)
            mix += mic_input * self.mic_volume
        
        # Applica effetti
        if self.reverb_enabled:
            mix = AudioEffects.reverb(mix, self.reverb_amount)
        
        if self.bass_boost != 1.0:
            mix = AudioEffects.eq_bass(mix, self.bass_boost, self.sample_rate)
        
        # Applica master volume
        mix *= self.master_volume
        
        # Limiter per evitare clipping
        mix = np.clip(mix, -1.0, 1.0)
        
        # Registrazione
        if self.is_recording:
            self.recorded_frames.append(mix.copy())
        
        outdata[:] = mix
    
    def audio_callback_output_only(self, outdata, frames, time, status):
        """Callback per output primario"""
        if status:
            print(f"Audio status primario: {status}")
        
        # Mix delle clip
        mix = np.zeros((frames, 2), dtype=np.float32)
        
        for clip in self.clips.values():
            if clip.is_playing:
                clip_samples = clip.get_samples(frames)
                mix += clip_samples
        
        # Applica effetti
        if self.reverb_enabled:
            mix = AudioEffects.reverb(mix, self.reverb_amount)
        
        if self.bass_boost != 1.0:
            mix = AudioEffects.eq_bass(mix, self.bass_boost, self.sample_rate)
        
        # Applica master volume
        mix *= self.master_volume
        
        # Limiter per evitare clipping
        mix = np.clip(mix, -1.0, 1.0)
        
        # Registrazione
        if self.is_recording:
            self.recorded_frames.append(mix.copy())
        
        outdata[:] = mix
    
    def audio_callback_secondary(self, outdata, frames, time, status):
        """Callback per output secondario (genera audio indipendentemente)"""
        if status:
            print(f"Audio status secondario: {status}")
        
        # Mix delle clip (usa posizione SECONDARIA separata)
        mix = np.zeros((frames, 2), dtype=np.float32)
        
        for clip in self.clips.values():
            if clip.is_playing:
                clip_samples = clip.get_samples(frames, is_secondary=True)  # <-- IMPORTANTE
                mix += clip_samples
        
        # Applica effetti
        if self.reverb_enabled:
            mix = AudioEffects.reverb(mix, self.reverb_amount)
        
        if self.bass_boost != 1.0:
            mix = AudioEffects.eq_bass(mix, self.bass_boost, self.sample_rate)
        
        # Applica SECONDARY VOLUME (separato dal primario)
        mix *= self.secondary_volume
        
        # Limiter per evitare clipping
        mix = np.clip(mix, -1.0, 1.0)
        
        outdata[:] = mix
    
    def start(self):
        """Avvia lo stream audio"""
        # Determina numero di canali del dispositivo di output
        output_channels = 2  # default
        if self.output_device is not None:
            try:
                device_info = sd.query_devices(self.output_device)
                output_channels = min(device_info['max_output_channels'], 2)  # Usa max 2 canali
                print(f"Dispositivo primario {self.output_device}: {device_info['name']} ({output_channels} canali)")
            except Exception as e:
                print(f"Errore query dispositivo: {e}")
        
        try:
            self.stream = sd.Stream(
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                device=self.output_device,  # Usa dispositivo configurato
                channels=output_channels,
                dtype='float32',
                callback=self.audio_callback
            )
            self.stream.start()
            print(f"✓ Stream duplex avviato con dispositivo: {self.output_device}")
        except Exception as e:
            print(f"Errore nell'avvio dello stream duplex: {e}")
            print("Tentativo con solo output...")
            # Fallback a solo output se duplex non funziona
            self.mic_enabled = False
            try:
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.buffer_size,
                    device=self.output_device,  # Usa dispositivo configurato (NON None!)
                    channels=output_channels,
                    dtype='float32',
                    callback=self.audio_callback_output_only
                )
                self.stream.start()
                print(f"✓ OutputStream avviato con dispositivo: {self.output_device}")
            except Exception as e2:
                print(f"Errore anche con solo output: {e2}")
                print("Ultimo tentativo con dispositivo di default...")
                # Ultimo tentativo SOLO se il dispositivo configurato fallisce
                try:
                    self.stream = sd.OutputStream(
                        samplerate=self.sample_rate,
                        blocksize=self.buffer_size,
                        device=None,  # Usa default solo come ultima risorsa
                        channels=2,
                        dtype='float32',
                        callback=self.audio_callback_output_only
                    )
                    self.stream.start()
                    print("⚠ OutputStream avviato con dispositivo di default (fallback)")
                except Exception as e3:
                    print(f"❌ ERRORE CRITICO: Impossibile avviare audio: {e3}")
                    raise
        
        # Avvia secondo stream se configurato
        if self.secondary_output_device is not None:
            try:
                secondary_device_info = sd.query_devices(self.secondary_output_device)
                secondary_channels = min(secondary_device_info['max_output_channels'], 2)
                
                # FORZA LO STESSO SAMPLE RATE del primario per evitare resampling
                self.secondary_sample_rate = self.sample_rate
                
                print(f"Dispositivo secondario {self.secondary_output_device}: {secondary_device_info['name']}")
                print(f"  Canali: {secondary_channels}")
                print(f"  Sample Rate: {self.sample_rate} Hz (forzato uguale al primario)")
                
                self.secondary_stream = sd.OutputStream(
                    samplerate=self.sample_rate,  # STESSO SAMPLE RATE del primario
                    blocksize=self.buffer_size,
                    device=self.secondary_output_device,
                    channels=secondary_channels,
                    dtype='float32',
                    callback=self.audio_callback_secondary
                )
                self.secondary_stream.start()
                print(f"✓ Secondo OutputStream avviato con dispositivo: {self.secondary_output_device}")
            except Exception as e:
                print(f"⚠ Errore avvio secondo output: {e}")
                print("Continuo solo con output primario...")
    
    def stop(self):
        """Ferma lo stream audio"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.secondary_stream:
            self.secondary_stream.stop()
            self.secondary_stream.close()
    
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
