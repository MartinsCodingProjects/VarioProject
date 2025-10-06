from time import sleep
from machine import Pin, PWM
from _thread import start_new_thread

class AudioSystem:
    """Class-based audio system for ESP32 Vario buzzer management"""
    
    def __init__(self, buzzer_pin=4):
        """Initialize AudioSystem with specified buzzer pin"""
        self.buzzer_pin = buzzer_pin
        self.buzzer_pwm = None
        self.is_initialized = False
        self.beep_thread_running = False
        
    def initialize(self):
        """Initialize the buzzer PWM system"""
        try:
            # Create PWM object on specified GPIO pin
            pin = Pin(self.buzzer_pin, Pin.OUT)
            self.buzzer_pwm = PWM(pin)
            self.buzzer_pwm.freq(1000)  # Default frequency
            self.buzzer_pwm.duty(0)     # Start with buzzer off
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.is_initialized = False
            raise RuntimeError(f"AudioSystem initialization failed: {e}")
    
    def play_tone(self, frequency, duration):
        """Play a tone at given frequency for given duration (in milliseconds)"""
        if not self.is_initialized:
            raise RuntimeError("AudioSystem not initialized")
        
        if frequency > 0 and duration > 0:
            # Set frequency and start tone (50% duty cycle for good volume)
            self.buzzer_pwm.freq(int(frequency))
            self.buzzer_pwm.duty(512)  # 50% duty cycle (0-1023 range)
            sleep(duration / 1000.0)   # Convert ms to seconds
            self.buzzer_pwm.duty(0)    # Stop tone
        else:
            # Silence - ensure buzzer is off
            self.buzzer_pwm.duty(0)
            if duration > 0:
                sleep(duration / 1000.0)
    
    def stop_all_sounds(self):
        """Immediately stop all audio output"""
        if self.is_initialized and self.buzzer_pwm:
            self.buzzer_pwm.duty(0)
    
    def start_beep_handler(self, vario_state, v_speed_lock, positive_threshold=0.2, negative_threshold=-1):
        """Start the beep handler thread for continuous audio feedback"""
        if not self.is_initialized:
            raise RuntimeError("AudioSystem not initialized")
        
        if self.beep_thread_running:
            return  # Already running
        
        self.beep_thread_running = True
        start_new_thread(self._beep_handler_thread, 
                        (vario_state, v_speed_lock, positive_threshold, negative_threshold))
    
    def _beep_handler_thread(self, vario_state, v_speed_lock, positive_threshold, negative_threshold):
        """Internal beep handler thread function"""
        last_v_speed = 0  # Cache for fallback
        
        vario_state.log("AudioSystem beep handler thread started")
        
        while True:
            # Check if vario is turned on
            if not vario_state.turned_on:
                sleep(0.1)
                continue
            
            # Thread-safe v_speed reading
            if v_speed_lock.acquire():
                try:
                    v_speed = vario_state.v_speed
                    last_v_speed = v_speed
                finally:
                    v_speed_lock.release()
            else:
                v_speed = last_v_speed  # Use cached value if lock is busy
            
            # Handle audio and LED feedback
            if vario_state.sound_enabled:
                vario_state.onboard_led.value(1)  # LED on when sound enabled
                
                # Get tone parameters and play if within thresholds
                tone, duration, pause = self._map_vspeed_to_tone(v_speed)
                
                if v_speed > positive_threshold or v_speed < negative_threshold:
                    self.play_tone(tone, duration)
                    if pause > 0:
                        sleep(pause / 1000.0)
            else:
                vario_state.onboard_led.value(0)  # LED off when sound disabled
                sleep(0.1)  # Prevent busy waiting
    
    def _map_vspeed_to_tone(self, v_speed):
        """Map vertical speed to audio parameters (frequency_hz, duration_ms, pause_ms)"""
        if v_speed > 1.5:
            return (1800, 100, 50)    # Fast beep, high pitch for strong lift
        elif v_speed > 1.0:
            return (1600, 120, 80)
        elif v_speed > 0.5:
            return (1400, 150, 150)
        elif v_speed > 0.1:           # Weak lift
            return (1200, 200, 300)
        elif v_speed < -2.0:          # Strong sink - continuous low tone
            return (300, 500, 0)      # No pause = continuous
        elif v_speed < -1.0:
            return (400, 400, 50)
        elif v_speed < -0.5:
            return (500, 300, 100)
        else:
            return (0, 0, 200)        # Silence in neutral zone
    
    def get_info(self):
        """Get audio system information for debugging"""
        return {
            "status": "initialized" if self.is_initialized else "not_initialized",
            "buzzer_pin": self.buzzer_pin,
            "thread_running": self.beep_thread_running
        }

