"""
Mixer Engine Professionale - Sostituto di Voicemeeter
Gestisce routing multi-canale, processing e output simultanei
"""
import numpy as np
import sounddevice as sd
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from scipy import signal
import queue
import time


@dataclass
class AudioDevice:
    """Rappresenta un dispositivo audio"""
    id: int
    name: str
    input_channels: int
    output_channels: int
    sample_rate: float
    is_default_input: bool = False
    is_default_output: bool = False


class AudioProcessor:
    """Processing chain per canale audio"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.eq_low = 0.0      # dB (-12 a +12)
        self.eq_mid = 0.0      # dB
        self.eq_high = 0.0     # dB
        self.compressor_threshold = -20.0  # dB
        self.compressor_ratio = 4.0
        self.gate_threshold = -40.0  # dB
        self.gate_enabled = False
        self.comp_enabled = False
        
    def apply_eq(self, audio: np.ndarray) -> np.ndarray:
        """Equalizzatore a 3 bande"""
        if len(audio) == 0:
            return audio
            
        output = audio.copy()
        
        # Low shelf (80Hz)
        if self.eq_low != 0.0:
            gain_linear = 10 ** (self.eq_low / 20.0)
            sos_low = signal.butter(2, 80, 'low', fs=self.sample_rate, output='sos')
            low_band = signal.sosfilt(sos_low, audio, axis=0)
            output = audio + low_band * (gain_linear - 1.0)
        
        # Mid peak (1kHz)
        if self.eq_mid != 0.0:
            gain_linear = 10 ** (self.eq_mid / 20.0)
            sos_mid = signal.butter(2, [500, 2000], 'band', fs=self.sample_rate, output='sos')
            mid_band = signal.sosfilt(sos_mid, audio, axis=0)
            output = output + mid_band * (gain_linear - 1.0)
        
        # High shelf (8kHz)
        if self.eq_high != 0.0:
            gain_linear = 10 ** (self.eq_high / 20.0)
            sos_high = signal.butter(2, 8000, 'high', fs=self.sample_rate, output='sos')
            high_band = signal.sosfilt(sos_high, audio, axis=0)
            output = output + high_band * (gain_linear - 1.0)
        
        return output
    
    def apply_compressor(self, audio: np.ndarray) -> np.ndarray:
        """Compressore dinamico semplice"""
        if not self.comp_enabled or len(audio) == 0:
            return audio
        
        # Calcola envelope RMS
        rms = np.sqrt(np.mean(audio**2, axis=1, keepdims=True))
        rms_db = 20 * np.log10(np.maximum(rms, 1e-10))
        
        # Applica compressione
        gain_reduction = np.zeros_like(rms_db)
        over_threshold = rms_db > self.compressor_threshold
        gain_reduction[over_threshold] = (
            (rms_db[over_threshold] - self.compressor_threshold) * 
            (1 - 1/self.compressor_ratio)
        )
        
        # Converti in gain lineare
        gain_linear = 10 ** (-gain_reduction / 20.0)
        
        return audio * gain_linear
    
    def apply_gate(self, audio: np.ndarray) -> np.ndarray:
        """Noise gate"""
        if not self.gate_enabled or len(audio) == 0:
            return audio
        
        # Calcola envelope
        rms = np.sqrt(np.mean(audio**2, axis=1, keepdims=True))
        rms_db = 20 * np.log10(np.maximum(rms, 1e-10))
        
        # Applica gate
        gate_open = rms_db > self.gate_threshold
        return audio * gate_open.astype(float)
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Applica tutta la processing chain"""
        if len(audio) == 0:
            return audio
        
        audio = self.apply_gate(audio)
        audio = self.apply_eq(audio)
        audio = self.apply_compressor(audio)
        
        return audio


class MixerChannel:
    """Singolo canale del mixer"""
    
    def __init__(self, name: str, channel_type: str, sample_rate: int = 44100):
        self.name = name
        self.channel_type = channel_type  # 'hardware', 'virtual', 'bus', 'python'
        self.sample_rate = sample_rate
        
        # Controlli base
        self.gain = 1.0  # 0.0 a 2.0 (linear)
        self.fader = 0.0  # -60dB a +12dB
        self.mute = False
        self.solo = False
        self.pan = 0.0  # -1.0 (L) a +1.0 (R)
        
        # Routing - a quali bus mandare questo canale
        self.routing = {
            'A1': False,
            'A2': False,
            'A3': False,
            'B1': False,
            'B2': False,
        }
        
        # Processing
        self.processor = AudioProcessor(sample_rate)
        
        # Source per canali python (riferimento diretto al mixer)
        self.audio_source = None  # Per canali 'python', punta all'AudioMixer
        
        # Buffer audio
        self.audio_buffer = None
        
        # Input queue per canali "python" (ricevono audio da codice Python)
        if channel_type == 'python':
            self.input_queue = queue.Queue(maxsize=100)
        else:
            self.input_queue = None
        
        # Metering
        self.peak_level = -np.inf  # dB
        self.rms_level = -np.inf   # dB
        
    def set_fader_db(self, db: float):
        """Imposta fader in dB (-60 a +12)"""
        db = np.clip(db, -60, 12)
        self.fader = db
        if db <= -60:
            self.gain = 0.0
        else:
            self.gain = 10 ** (db / 20.0)
    
    def get_fader_db(self) -> float:
        """Leggi fader in dB"""
        return self.fader
    
    def apply_pan(self, audio: np.ndarray) -> np.ndarray:
        """Applica panoramica stereo"""
        if audio.shape[1] != 2 or self.pan == 0.0:
            return audio
        
        output = audio.copy()
        if self.pan > 0:  # Verso destra
            output[:, 0] *= (1.0 - self.pan)  # Abbassa sinistra
        else:  # Verso sinistra
            output[:, 1] *= (1.0 + self.pan)  # Abbassa destra
        
        return output
    
    def update_metering(self, audio: np.ndarray):
        """Aggiorna livelli per VU meter"""
        if len(audio) == 0:
            self.peak_level = -np.inf
            self.rms_level = -np.inf
            return
        
        # Peak
        peak = np.max(np.abs(audio))
        self.peak_level = 20 * np.log10(np.maximum(peak, 1e-10))
        
        # RMS
        rms = np.sqrt(np.mean(audio**2))
        self.rms_level = 20 * np.log10(np.maximum(rms, 1e-10))
    
    def push_audio(self, audio: np.ndarray):
        """Invia audio al canale (per canali 'python')"""
        if self.input_queue is not None:
            try:
                self.input_queue.put_nowait(audio.copy())
            except queue.Full:
                # Rimuovi il frame più vecchio e aggiungi quello nuovo
                try:
                    self.input_queue.get_nowait()
                    self.input_queue.put_nowait(audio.copy())
                except:
                    pass
    
    def get_audio_from_queue(self, n_frames: int) -> np.ndarray:
        """Leggi audio dalla queue (per canali 'python')"""
        if self.input_queue is None:
            return np.zeros((n_frames, 2))
        
        # Raccogli tutti i frame disponibili
        frames = []
        total_frames = 0
        queue_size = self.input_queue.qsize()
        
        while total_frames < n_frames and not self.input_queue.empty():
            try:
                frame = self.input_queue.get_nowait()
                frames.append(frame)
                total_frames += len(frame)
            except queue.Empty:
                break
        
        if not frames:
            # UNDERRUN: nessun dato disponibile - ritorna silenzio
            return np.zeros((n_frames, 2), dtype=np.float32)
        
        # Concatena e ritaglia
        audio = np.vstack(frames)
        if len(audio) >= n_frames:
            result = audio[:n_frames]
            # Se abbiamo letto più del necessario, rimetti in coda
            if len(audio) > n_frames:
                remainder = audio[n_frames:]
                try:
                    self.input_queue.put_nowait(remainder)
                except:
                    pass
            return result
        else:
            # Pad con silenzio - underrun parziale
            padding = np.zeros((n_frames - len(audio), 2), dtype=np.float32)
            return np.vstack([audio, padding])
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Processa l'audio del canale"""
        if self.mute:
            return np.zeros_like(audio)
        
        # Applica gain
        output = audio * self.gain
        
        # Processing chain
        output = self.processor.process(output)
        
        # Pan
        output = self.apply_pan(output)
        
        # Metering
        self.update_metering(output)
        
        return output


class OutputBus:
    """Bus di output (come A1, A2, etc in Voicemeeter)"""
    
    def __init__(self, name: str, device_id: Optional[int] = None, sample_rate: int = 44100):
        self.name = name
        self.device_id = device_id
        self.sample_rate = sample_rate
        
        self.master_volume = 1.0
        self.master_fader = 0.0  # dB
        self.mute = False
        
        # Stream audio
        self.stream: Optional[sd.OutputStream] = None
        self.audio_queue = queue.Queue(maxsize=10)
        
        # Metering
        self.peak_level = -np.inf
        self.rms_level = -np.inf
    
    def set_fader_db(self, db: float):
        """Imposta master fader in dB"""
        db = np.clip(db, -60, 12)
        self.master_fader = db
        if db <= -60:
            self.master_volume = 0.0
        else:
            self.master_volume = 10 ** (db / 20.0)
    
    def update_metering(self, audio: np.ndarray):
        """Aggiorna metering del bus"""
        if len(audio) == 0:
            self.peak_level = -np.inf
            self.rms_level = -np.inf
            return
        
        peak = np.max(np.abs(audio))
        self.peak_level = 20 * np.log10(np.maximum(peak, 1e-10))
        
        rms = np.sqrt(np.mean(audio**2))
        self.rms_level = 20 * np.log10(np.maximum(rms, 1e-10))


class ProMixer:
    """Mixer Professionale Multi-Bus"""
    
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Canali input
        self.channels: Dict[str, MixerChannel] = {}
        
        # Bus output
        self.buses: Dict[str, OutputBus] = {}
        
        # Streams attivi
        self.input_streams: Dict[str, sd.InputStream] = {}
        self.input_device_map: Dict[str, int] = {}  # Mappa channel_id -> device_id per salvataggio config
        self.is_running = False
        
        # Lock per thread-safety
        self.lock = threading.Lock()
        
        # Callback per metering UI
        self.metering_callback: Optional[Callable] = None
        
        self._init_default_channels()
    
    def _init_default_channels(self):
        """Inizializza canali di default come Voicemeeter"""
        # Canale Soundboard (input da Python)
        soundboard_ch = MixerChannel("Soundboard", "python", self.sample_rate)
        self.channels["SOUNDBOARD"] = soundboard_ch
        
        # Hardware Inputs (3 come Voicemeeter)
        for i in range(1, 4):
            ch = MixerChannel(f"Hardware {i}", "hardware", self.sample_rate)
            self.channels[f"HW{i}"] = ch
        
        # Virtual Inputs (2 come Voicemeeter)
        for i in range(1, 3):
            ch = MixerChannel(f"Virtual {i}", "virtual", self.sample_rate)
            self.channels[f"VIRT{i}"] = ch
        
        # Buses (A1-A3, B1-B2 come Voicemeeter)
        for bus_name in ['A1', 'A2', 'A3', 'B1', 'B2']:
            bus = OutputBus(bus_name, None, self.sample_rate)
            self.buses[bus_name] = bus
    
    def set_channel_routing(self, channel_id: str, bus_name: str, enabled: bool):
        """Imposta routing di un canale verso un bus"""
        with self.lock:
            if channel_id in self.channels and bus_name in self.buses:
                self.channels[channel_id].routing[bus_name] = enabled
    
    def set_bus_device(self, bus_name: str, device_id: int):
        """Assegna dispositivo fisico a un bus"""
        with self.lock:
            if bus_name in self.buses:
                self.buses[bus_name].device_id = device_id
    
    def audio_input_callback(self, channel_id: str):
        """Genera callback per input stream"""
        def callback(indata, frames, time, status):
            if status:
                print(f"[{channel_id}] Status: {status}")
            
            with self.lock:
                if channel_id in self.channels:
                    # Converti a stereo se necessario
                    if indata.shape[1] == 1:
                        audio = np.repeat(indata, 2, axis=1)
                    else:
                        audio = indata.copy()
                    
                    # Salva nel buffer del canale
                    self.channels[channel_id].audio_buffer = audio
                    
                    # Aggiorna metering per VU meter
                    self.channels[channel_id].update_metering(audio)
        
        return callback
    
    def audio_output_callback(self, bus_name: str):
        """Genera callback per output stream"""
        import time as time_module
        callback_count = [0]
        error_count = [0]
        
        def callback(outdata, frames, time_info, status):
            callback_count[0] += 1
            
            # Log SOLO errori critici (max 5)
            if status:
                if error_count[0] < 5:
                    error_count[0] += 1
                    print(f"🔴 [{bus_name}] Audio error #{error_count[0]}: {status}")
                # In caso di errore, riempi con silenzio e continua
                if status.output_underflow:
                    outdata.fill(0)
                    return
            
            with self.lock:
                bus = self.buses[bus_name]
                
                # Mix di tutti i canali routati verso questo bus
                mix = np.zeros((frames, 2), dtype=np.float32)
                active_channels = 0
                
                for ch_id, channel in self.channels.items():
                    if not channel.routing.get(bus_name, False):
                        continue
                    
                    # Ottieni audio dal canale
                    audio = None
                    
                    if channel.channel_type == 'python':
                        # Canale virtuale Python (es. soundboard)
                        # Se ha un audio_source, tira l'audio direttamente
                        if channel.audio_source:
                            # Passa il nome del bus come stream_id per posizioni indipendenti
                            audio = channel.audio_source.get_audio(frames, stream_id=bus_name)
                        else:
                            # Fallback: usa la queue (legacy)
                            audio = channel.get_audio_from_queue(frames)
                    elif channel.audio_buffer is not None:
                        # Canale hardware/virtual con buffer
                        # Prendi esattamente frames samples, troncando o padding
                        buffer_len = len(channel.audio_buffer)
                        
                        if buffer_len >= frames:
                            # Buffer sufficiente: prendi primi frames samples
                            audio = channel.audio_buffer[:frames].copy()
                        else:
                            # Buffer insufficiente: pad con zeri
                            padding = np.zeros((frames - buffer_len, 2), dtype=np.float32)
                            audio = np.vstack([channel.audio_buffer, padding])
                    
                    if audio is not None and len(audio) > 0:
                        # Processa canale (applica gain, effetti, pan)
                        processed = channel.process(audio)
                        
                        # Aggiungi al mix
                        mix += processed
                        active_channels += 1
                
                # Applica master volume del bus
                if not bus.mute:
                    mix *= bus.master_volume
                else:
                    mix *= 0.0
                
                # Limiter
                mix = np.clip(mix, -1.0, 1.0)
                
                # Metering
                bus.update_metering(mix)
                
                # Verifica dimensioni finali
                if mix.shape[0] != frames or mix.shape[1] != 2:
                    print(f"❌ [{bus_name}] ERRORE DIMENSIONI OUTPUT!")
                    print(f"   Mix shape: {mix.shape}, atteso: ({frames}, 2)")
                    # Riempi con silenzio
                    outdata.fill(0)
                else:
                    # Output
                    outdata[:] = mix
                
                # Callback UI per metering
                if self.metering_callback:
                    self.metering_callback()
        
        return callback
    
    def start_input(self, channel_id: str, device_id: int):
        """Avvia input stream per un canale"""
        try:
            device_info = sd.query_devices(device_id)
            channels = min(device_info['max_input_channels'], 2)
            
            # Rinomina il canale con il nome del device
            if channel_id in self.channels:
                device_name = device_info['name']
                # Accorcia il nome se troppo lungo
                if len(device_name) > 20:
                    device_name = device_name[:17] + "..."
                self.channels[channel_id].name = device_name
            
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                device=device_id,
                channels=channels,
                dtype='float32',
                callback=self.audio_input_callback(channel_id)
            )
            stream.start()
            self.input_streams[channel_id] = stream
            self.input_device_map[channel_id] = device_id  # Salva per config
            
            # Attiva routing automatico SOLO verso A1 (Discord/streaming)
            # A2 (cuffie) rimane disattivato per evitare feedback del microfono
            if channel_id in self.channels:
                if 'A1' in self.buses and self.buses['A1'].device_id is not None:
                    self.set_channel_routing(channel_id, 'A1', True)
                    print(f"   ✓ Routing automatico: {channel_id} → A1 (Output principale)")
                
                # Imposta fader a 0 dB (unity gain)
                self.channels[channel_id].set_fader_db(0.0)
            
            print(f"✓ Input avviato: {channel_id} -> Device {device_id} ({device_info['name']})")
            return True
        except Exception as e:
            print(f"✗ Errore avvio input {channel_id}: {e}")
            return False
    
    def start_output(self, bus_name: str):
        """Avvia output stream per un bus"""
        bus = self.buses[bus_name]
        
        if bus.device_id is None:
            print(f"⚠ Bus {bus_name} non ha dispositivo assegnato")
            return False
        
        # Se lo stream è già attivo, non fare nulla
        if bus.stream is not None:
            try:
                if bus.stream.active:
                    print(f"⚠ Bus {bus_name} già attivo, skip")
                    return True
            except:
                pass  # Stream non valido, continua ad avviarne uno nuovo
        
        try:
            device_info = sd.query_devices(bus.device_id)
            channels = min(device_info['max_output_channels'], 2)
            
            # USA SEMPRE il sample rate nativo del dispositivo
            # Windows WASAPI non supporta sample rate diversi
            device_samplerate = int(device_info.get('default_samplerate', 48000))
            
            # FORZA il sample rate del ProMixer a coincidere col device
            if device_samplerate != self.sample_rate:
                print(f"⚠️ Device {bus.device_id} ha sample rate {device_samplerate}Hz")
                print(f"   ProMixer forzato da {self.sample_rate}Hz a {device_samplerate}Hz")
                self.sample_rate = device_samplerate
                # Aggiorna tutti i canali e bus
                for ch in self.channels.values():
                    ch.sample_rate = device_samplerate
                for b in self.buses.values():
                    b.sample_rate = device_samplerate
            
            stream = sd.OutputStream(
                samplerate=device_samplerate,
                blocksize=self.buffer_size,
                device=bus.device_id,
                channels=channels,
                dtype='float32',
                callback=self.audio_output_callback(bus_name),
                prime_output_buffers_using_stream_callback=True  # Pre-buffering per audio più fluido
            )
            stream.start()
            bus.stream = stream
            bus.sample_rate = device_samplerate
            
            print(f"✓ Output avviato: {bus_name} -> Device {bus.device_id} ({device_info['name']}) @ {device_samplerate}Hz")
            return True
        except Exception as e:
            print(f"✗ Errore avvio output {bus_name}: {e}")
            return False
    
    def start_all(self):
        """Avvia tutti gli stream configurati"""
        # Se già running, ferma tutto prima di riavviare
        if self.is_running:
            print("⚠ Mixer già avviato, fermo e riavvio...")
            self.stop_all()
        
        self.is_running = True
        
        # Avvia output buses
        for bus_name in self.buses:
            if self.buses[bus_name].device_id is not None:
                self.start_output(bus_name)
        
        print(f"\n✓ Mixer avviato ({self.sample_rate}Hz, {self.buffer_size} samples)")
    
    def stop_all(self):
        """Ferma tutti gli stream"""
        self.is_running = False
        
        # Stop inputs
        for stream in self.input_streams.values():
            stream.stop()
            stream.close()
        self.input_streams.clear()
        
        # Stop outputs
        for bus in self.buses.values():
            if bus.stream:
                bus.stream.stop()
                bus.stream.close()
                bus.stream = None
        
        # Reset posizioni delle clip soundboard per evitare audio veloce al riavvio
        for channel in self.channels.values():
            if channel.audio_source:
                # Resetta le posizioni di tutte le clip nell'audio_source
                if hasattr(channel.audio_source, 'clips'):
                    for clip in channel.audio_source.clips.values():
                        if hasattr(clip, 'positions'):
                            clip.positions = {}
        
        print("✓ Mixer fermato")
    
    def get_available_devices(self) -> List[AudioDevice]:
        """Ritorna lista dispositivi disponibili (solo WASAPI per evitare duplicati)"""
        devices = []
        default_in, default_out = sd.default.device
        
        all_devices = sd.query_devices()
        host_apis = sd.query_hostapis()
        
        for i, dev in enumerate(all_devices):
            # Ottieni host API
            hostapi_idx = dev['hostapi']
            hostapi_name = host_apis[hostapi_idx]['name'] if hostapi_idx < len(host_apis) else 'Unknown'
            
            # Filtra solo WASAPI (evita duplicati MME/DirectSound)
            if 'WASAPI' in hostapi_name:
                audio_dev = AudioDevice(
                    id=i,
                    name=dev['name'],
                    input_channels=dev['max_input_channels'],
                    output_channels=dev['max_output_channels'],
                    sample_rate=dev['default_samplerate'],
                    is_default_input=(i == default_in),
                    is_default_output=(i == default_out)
                )
                devices.append(audio_dev)
        
        # Ordina alfabeticamente
        devices.sort(key=lambda d: d.name.lower())
        
        return devices


# Test standalone
if __name__ == "__main__":
    print("=== PRO MIXER ENGINE ===\n")
    
    mixer = ProMixer()
    
    # Lista dispositivi
    print("Dispositivi disponibili:")
    devices = mixer.get_available_devices()
    
    print("\n📥 INPUT:")
    for dev in devices:
        if dev.input_channels > 0:
            default = " [DEFAULT]" if dev.is_default_input else ""
            print(f"  [{dev.id}] {dev.name} ({dev.input_channels}ch){default}")
    
    print("\n📤 OUTPUT:")
    for dev in devices:
        if dev.output_channels > 0:
            default = " [DEFAULT]" if dev.is_default_output else ""
            print(f"  [{dev.id}] {dev.name} ({dev.output_channels}ch){default}")
    
    print("\n" + "="*50)
    print("Configurazione esempio:")
    print("  HW1 → Input Device 13 (Microfono)")
    print("  VIRT1 → Virtual Cable")
    print("  Bus A1 → Output Device 16 (Speakers)")
    print("="*50)
