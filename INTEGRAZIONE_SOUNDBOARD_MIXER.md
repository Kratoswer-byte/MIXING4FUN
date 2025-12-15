# 🔄 Integrazione Soundboard + ProMixer

## Architettura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                    SOUNDBOARD                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Clip 1   │  │ Clip 2   │  │ Clip N   │                  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘                  │
│        └─────────────┴─────────────┘                        │
│                      ↓                                       │
│              [Audio Mix Buffer]                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌──────────────────────┴──────────────────────────────────────┐
│                   PRO MIXER                                  │
│                                                              │
│  CHANNEL 1: Soundboard Input ─┐                             │
│  CHANNEL 2: Microphone Input ─┤                             │
│                               ↓                              │
│                          [MIX + FX]                          │
│                               ↓                              │
│                    ┌──────────┴──────────┐                  │
│                    ↓                     ↓                   │
│              BUS A1 (CABLE)         BUS A2 (Cuffie)         │
│                    │                     │                   │
└────────────────────┼─────────────────────┼──────────────────┘
                     ↓                     ↓
            Discord/OBS Input      Monitoraggio Audio
```

## Modifiche Necessarie

### 1. AudioMixer: Modalità "Virtual Output"

Aggiungere la possibilità di inviare l'output a un callback invece che a un device fisico:

```python
class AudioMixer:
    def __init__(self, ..., virtual_output_callback=None):
        self.virtual_output_callback = virtual_output_callback
        # Se c'è callback, invia audio lì invece che ai device
        
    def audio_callback(self, outdata, frames, time, status):
        # Genera mix audio
        mix = self._generate_mix(frames)
        
        if self.virtual_output_callback:
            # Invia al ProMixer
            self.virtual_output_callback(mix)
        else:
            # Invia ai device fisici
            outdata[:] = mix
```

### 2. ProMixer: Canale Input Virtuale

Creare un canale che riceve audio da Python invece che da device fisico:

```python
class VirtualInputChannel(MixerChannel):
    def __init__(self, name: str, sample_rate: int):
        super().__init__(name, "virtual", sample_rate)
        self.input_buffer = queue.Queue(maxsize=10)
        
    def push_audio(self, audio: np.ndarray):
        """Riceve audio dalla soundboard"""
        try:
            self.input_buffer.put_nowait(audio)
        except queue.Full:
            pass  # Dropa frame se buffer pieno
```

### 3. Connessione

Nel main.py:

```python
# Crea ProMixer
self.pro_mixer = ProMixer(sample_rate=48000)

# Configura bus
self.pro_mixer.set_bus_device('A1', 61)   # CABLE Input
self.pro_mixer.set_bus_device('A2', 105)  # Cuffie

# Crea canale soundboard nel mixer
soundboard_channel = VirtualInputChannel("Soundboard", 48000)
self.pro_mixer.channels['SOUNDBOARD'] = soundboard_channel

# Routing: soundboard va su entrambi i bus
self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A1', True)
self.pro_mixer.set_channel_routing('SOUNDBOARD', 'A2', True)

# Crea AudioMixer che invia al canale
def soundboard_output_callback(audio):
    soundboard_channel.push_audio(audio)

self.mixer = AudioMixer(
    sample_rate=48000,
    virtual_output_callback=soundboard_output_callback
)
```

## Vantaggi

✅ Routing flessibile (puoi decidere dove va l'audio)
✅ Processing centralizzato (EQ, compressione sul mix finale)
✅ Volume indipendente per Discord e cuffie
✅ Nessun CABLE extra necessario
✅ Stessa architettura di Voicemeeter

## Alternative

### Opzione B: Soundboard usa direttamente i bus

Invece di creare un canale virtuale, la soundboard scrive direttamente nei bus A1/A2:

```python
class AudioMixer:
    def __init__(self, ..., mixer_buses: Dict[str, OutputBus]):
        self.mixer_buses = mixer_buses
        
    def audio_callback(self, ...):
        mix = self._generate_mix(frames)
        
        # Invia a tutti i bus configurati
        for bus in self.mixer_buses.values():
            bus.add_audio(mix)
```

Più semplice ma meno flessibile (no processing per canale).

## Implementazione Consigliata

**Opzione 1** (con canale virtuale) - più potente e professionale
- Permette EQ/compressore sulla soundboard separatamente dal mic
- Routing più flessibile
- Architettura scalabile

Vuoi che implemento questa integrazione?
