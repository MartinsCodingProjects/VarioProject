from time import sleep
from machine import Pin, PWM

def init_buzzer(buzzer_pin = 4):
    """
    Initialize the passive buzzer on GPIO 4
    Must be called before using any audio functions
    """
    
    try:
        # Create PWM object on GPIO 4
        pin = Pin(buzzer_pin, Pin.OUT)
        pwm = PWM(pin)
        pwm.freq(1000)  # Default frequency
        pwm.duty(0) # Start with the buzzer off
        print(f"Buzzer initialized on GPIO {buzzer_pin}")
        return pwm
    except Exception as e:
        print(f"Buzzer initialization failed: {e}")
        return None

def play_tone(frequency, duration, buzzer_pwm):
    """
    Play a tone at given frequency for given duration (in milliseconds)
    frequency: Hz (0 = silence)
    duration: milliseconds
    """
    
    if buzzer_pwm is None:
        print("Buzzer not initialized! Call init_buzzer() first.")
        return
    
    if frequency > 0 and duration > 0:
        # Set frequency and start tone (50% duty cycle for good volume)
        buzzer_pwm.freq(int(frequency))
        buzzer_pwm.duty(512)  # 50% duty cycle (0-1023 range)
        sleep(duration / 1000.0)  # Convert ms to seconds
        buzzer_pwm.duty(0)  # Stop tone
        print(f"Beeped: {frequency} Hz for {duration} ms")
    else:
        # Silence - ensure buzzer is off
        buzzer_pwm.duty(0)
        if duration > 0:
            sleep(duration / 1000.0)

def handle_beep(v_speed_lock, vario_state, positiv_threshold = 0.2, negativ_threshold=-1):
    """
    Makes one beep and a pause after the beep, if v_speed meets set criterias
    Beep and pauses lenght and frequency depend on v_speed

    There is a silent zone for low values of v_speed (each positiv and negativ values)
    then there will be threshols, for when the positiv and negativ beeps start

    positiv beeping if v_speed > positiv_threshold starts with longer beep and pause, with middle pitch values.
    beeps get faster and pitch gets higher with increasing v_speed

    negativ beeping, starting with v_speed < negativ_theshold, is no beeping but continues note (pause = 0), with low pitch values
    if v_speed decrease pitch gets lower
    """
    last_v_speed = 0  # Cache the last known v_speed for fallback
    
    print("Beep handler thread started")

    while True:
        # Try to acquire the lock without blocking
        if v_speed_lock.acquire():
            try:
                # Read the latest v_speed in a thread-safe manner
                v_speed = vario_state.v_speed
                last_v_speed = v_speed  # Update the cached value
            finally:
                # Always release the lock after accessing v_speed
                v_speed_lock.release()
        else:
            # If the lock is held by the main thread, use the last known v_speed
            v_speed = last_v_speed

        # Only play sounds if sound is enabled
        if vario_state.sound_enabled:
            vario_state.onboard_led.value(1)  # Turn on LED when sound is enabled
            # Get tone parameters based on v_speed
            tone, duration, pause = map_vspeed_to_tone(v_speed)

            # Play the tone if within active thresholds
            if v_speed > positiv_threshold or v_speed < negativ_threshold:
                play_tone(tone, duration, vario_state.buzzer_pwm)
                if pause > 0:
                    sleep(pause / 1000.0)  # Convert ms to seconds
        else:
            vario_state.onboard_led.value(0)  # Turn off LED when sound is disabled
            # If sound is disabled, just add a small delay to prevent busy waiting
            sleep(0.1)

def map_vspeed_to_tone(v):
    """
    Map vertical speed to audio parameters
    Returns: (frequency_hz, duration_ms, pause_ms)

    Todo: Adjust these mappings based on desired audio feedback characteristics
    """
    if v > 1.5:
        return (1800, 100, 50)  # fast beep, high pitch for strong lift
    elif v > 1.0:
        return (1600, 120, 80)
    elif v > 0.5:
        return (1400, 150, 150)
    elif v > 0.1:  # weak lift
        return (1200, 200, 300)
    elif v < -2.0:  # strong sink - continuous low tone
        return (300, 500, 0)   # no pause = continuous
    elif v < -1.0:
        return (400, 400, 50)
    elif v < -0.5:
        return (500, 300, 100)
    else:
        return (0, 0, 200)  # silence in neutral zone
