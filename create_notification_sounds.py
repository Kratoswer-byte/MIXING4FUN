"""
Crea i suoni di notifica per soundboard attiva/disattiva
"""
import numpy as np
import soundfile as sf

def create_activation_sound():
    """Crea un suono ascendente per l'attivazione (ding positivo)"""
    sample_rate = 44100
    duration = 0.3  # 300ms
    
    # Due note ascendenti: C5 (523 Hz) -> G5 (784 Hz)
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Prima nota (150ms)
    freq1 = 523
    t1 = t[:int(sample_rate * 0.15)]
    note1 = np.sin(2 * np.pi * freq1 * t1)
    
    # Seconda nota (150ms)
    freq2 = 784
    t2 = t[int(sample_rate * 0.15):int(sample_rate * 0.3)]
    note2 = np.sin(2 * np.pi * freq2 * (t2 - t2[0]))
    
    # Unisci
    sound = np.concatenate([note1, note2])
    
    # Envelope per fade in/out morbido
    envelope = np.ones_like(sound)
    fade_samples = int(sample_rate * 0.02)  # 20ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    
    sound = sound * envelope * 0.3  # Volume 30%
    
    # Stereo
    sound_stereo = np.column_stack([sound, sound])
    
    sf.write('soundboard_on.wav', sound_stereo, sample_rate)
    print("✓ Creato: soundboard_on.wav")

def create_deactivation_sound():
    """Crea un suono discendente per la disattivazione (ding negativo)"""
    sample_rate = 44100
    duration = 0.3  # 300ms
    
    # Due note discendenti: G5 (784 Hz) -> C5 (523 Hz)
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Prima nota (150ms)
    freq1 = 784
    t1 = t[:int(sample_rate * 0.15)]
    note1 = np.sin(2 * np.pi * freq1 * t1)
    
    # Seconda nota (150ms)
    freq2 = 523
    t2 = t[int(sample_rate * 0.15):int(sample_rate * 0.3)]
    note2 = np.sin(2 * np.pi * freq2 * (t2 - t2[0]))
    
    # Unisci
    sound = np.concatenate([note1, note2])
    
    # Envelope per fade in/out morbido
    envelope = np.ones_like(sound)
    fade_samples = int(sample_rate * 0.02)  # 20ms fade
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
    
    sound = sound * envelope * 0.3  # Volume 30%
    
    # Stereo
    sound_stereo = np.column_stack([sound, sound])
    
    sf.write('soundboard_off.wav', sound_stereo, sample_rate)
    print("✓ Creato: soundboard_off.wav")

if __name__ == "__main__":
    print("🔊 Creazione suoni notifica...")
    create_activation_sound()
    create_deactivation_sound()
    print("\n✅ Suoni creati con successo!")
    print("   - soundboard_on.wav  (attivazione)")
    print("   - soundboard_off.wav (disattivazione)")
