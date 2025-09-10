from machine import Pin, PWM
import time

# Passive Buzzer pin configuration
BUZZER_PIN = 27

def play_tone(pwm, frequency, duration):
    """Play a tone at a specific frequency for a given duration"""
    try:
        # Try different methods for setting duty cycle
        if hasattr(pwm, 'duty'):
            pwm.freq(frequency)
            pwm.duty(512)  # 50% duty cycle
        elif hasattr(pwm, 'duty_u16'):
            pwm.freq(frequency)
            pwm.duty_u16(32768)  # 50% duty cycle for 16-bit
        else:
            # Fallback method using on/off
            pwm = PWM(Pin(BUZZER_PIN), freq=frequency)
        
        time.sleep(duration)
        
        # Turn off the buzzer
        if hasattr(pwm, 'duty'):
            pwm.duty(0)
        elif hasattr(pwm, 'duty_u16'):
            pwm.duty_u16(0)
        else:
            pwm.deinit()
    
    except Exception as e:
        print(f"Error playing tone: {e}")

def test_passive_buzzer():
    """Comprehensive passive buzzer test"""
    print("=== Passive Buzzer Test ===")
    
    # Create PWM object with more flexible initialization
    try:
        buzzer = PWM(Pin(BUZZER_PIN))
    except TypeError:
        # Some boards might require different initialization
        buzzer = PWM(Pin(BUZZER_PIN), freq=1000)
    
    print("\n1. Frequency Sweep Test")
    # Sweep through frequencies
    frequency_ranges = [
        (100, 500),   # Low frequencies
        (500, 1500),  # Mid frequencies
        (1500, 4000)  # High frequencies
    ]
    
    for start, end in frequency_ranges:
        print(f"\nSweeping from {start} Hz to {end} Hz")
        for freq in range(start, end, 100):
            print(f"Testing {freq} Hz")
            play_tone(buzzer, freq, 0.1)
            time.sleep(0.05)
    
    print("\n2. Musical Scale Test")
    # Simple musical scale (C4 to C5)
    notes = [
        261,  # C4
        294,  # D4
        330,  # E4
        349,  # F4
        392,  # G4
        440,  # A4
        494,  # B4
        523   # C5
    ]
    
    for note in notes:
        print(f"Playing note: {note} Hz")
        play_tone(buzzer, note, 0.3)
        time.sleep(0.1)
    
    print("\n3. Alarm Patterns")
    # Different alarm-like patterns
    patterns = [
        # Rising alarm
        [(200, 0.2), (400, 0.2), (600, 0.2), (800, 0.2)],
        # Falling alarm
        [(800, 0.1), (600, 0.1), (400, 0.1), (200, 0.1)],
        # Alternating frequencies
        [(500, 0.1), (1000, 0.1), (500, 0.1), (1000, 0.1)]
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nAlarm Pattern {i}")
        for freq, duration in pattern:
            print(f"Frequency: {freq} Hz, Duration: {duration}s")
            play_tone(buzzer, freq, duration)
            time.sleep(0.05)
    
    # Final test - constant tone
    print("\n4. Constant Tone Test")
    print("Steady 1000 Hz tone for 1 second")
    play_tone(buzzer, 1000, 1)
    
    # Cleanup
    try:
        buzzer.deinit()
    except Exception as e:
        print(f"Error during deinit: {e}")
    
    print("\n=== Passive Buzzer Test Complete ===")

def main():
    try:
        test_passive_buzzer()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during buzzer test: {e}")
    finally:
        # Ensure buzzer is properly deinitialized
        try:
            PWM(Pin(BUZZER_PIN)).deinit()
        except:
            pass

if __name__ == "__main__":
    main()