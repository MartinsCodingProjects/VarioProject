# hardware_manager.py - Hardware initialization and management

import gc
from modules.sensor import MS5611Sensor
from modules.audio import AudioSystem
from modules.util import setup_toggle_button

class HardwareManager:
    """Manages all hardware component initialization for the ESP32 Vario"""
    
    def __init__(self, vario_state, buzzer_pin):
        self.vario_state = vario_state
        self.buzzer_pin = buzzer_pin
        self.hardware_initialized = False
        
        # Hardware component references
        self.ms5611_sensor = None
        self.audio_system = None
    
    def initialize_sensor(self):
        """Initialize MS5611 barometric pressure sensor"""
        try:
            self.vario_state.log("Initializing MS5611 barometric sensor (I2C mode)...")
            
            # Create and initialize MS5611 sensor object with I2C configuration
            self.ms5611_sensor = MS5611Sensor(scl_pin=22, sda_pin=21, i2c_address=0x77)
            self.ms5611_sensor.initialize()
            
            # Get sensor info for logging
            sensor_info = self.ms5611_sensor.get_info()
            calibration = sensor_info['calibration']
            pins = sensor_info['pins']
            i2c_addr = sensor_info['i2c_address']
            
            self.vario_state.log(f"MS5611 sensor initialized successfully!")
            self.vario_state.log(f"I2C Configuration: SCL=GPIO{pins['scl']}, SDA=GPIO{pins['sda']}, Address={i2c_addr}")
            self.vario_state.log(f"Calibration: C1={calibration['C1']}, C2={calibration['C2']}, C3={calibration['C3']}, C4={calibration['C4']}, C5={calibration['C5']}, C6={calibration['C6']}")
            
            return True
                
        except Exception as e:
            self.vario_state.log(f"Failed to initialize MS5611 sensor: {e}")
            return False
    
    def initialize_buzzer(self):
        """Initialize buzzer for audio feedback"""
        try:
            self.vario_state.log(f"Initializing AudioSystem on GPIO {self.buzzer_pin}...")
            
            # Create and initialize AudioSystem
            self.audio_system = AudioSystem(self.buzzer_pin)
            self.audio_system.initialize()
            
            self.vario_state.log("AudioSystem initialized and ready!")
            return True
            
        except Exception as e:
            self.vario_state.log(f"Failed to initialize AudioSystem: {e}")
            return False
    
    def initialize_user_interface(self):
        """Initialize user interface components (buttons, LEDs)"""
        try:
            self.vario_state.log("Initializing user interface components...")
            
            # Setup boot button and onboard LED
            boot_button, onboard_led = setup_toggle_button(self.vario_state)
            
            # Store references in vario_state
            self.vario_state.boot_button = boot_button
            self.vario_state.onboard_led = onboard_led
            
            self.vario_state.log("User interface initialized - Press BOOT button to start/stop vario and toggle sound")
            return True
            
        except Exception as e:
            self.vario_state.log(f"Failed to initialize user interface: {e}")
            return False
    
    def initialize_all_hardware(self):
        """Initialize all hardware components in sequence"""
        self.vario_state.log("=== Starting Hardware Initialization ===")
        
        # Initialize components in order of importance
        sensor_ok = self.initialize_sensor()
        buzzer_ok = self.initialize_buzzer()
        ui_ok = self.initialize_user_interface()
        
        # Determine overall hardware status
        self.hardware_initialized = sensor_ok  # Sensor is critical
        
        if self.hardware_initialized:
            self.vario_state.log("=== Hardware Initialization COMPLETED ===")
            if not buzzer_ok:
                self.vario_state.log("Warning: Audio system not available")
            if not ui_ok:
                self.vario_state.log("Warning: User interface not fully available")
        else:
            self.vario_state.log("=== Hardware Initialization FAILED ===")
            self.vario_state.log("Critical error: Cannot proceed without barometric sensor")
        
        # Cleanup memory after initialization
        gc.collect()
        
        return self.hardware_initialized
    
    def get_sensor_info(self):
        """Get sensor initialization info for sharing with main application"""
        return {
            'sensor_object': self.ms5611_sensor,
            'audio_system': self.audio_system,
            'initialized': self.hardware_initialized
        }
