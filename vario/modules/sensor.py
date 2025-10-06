import machine, time

class MS5611Sensor:
    """MS5611 Barometric Pressure Sensor Driver (I2C Mode)"""
    
    def __init__(self, scl_pin=22, sda_pin=21, i2c_address=0x77):
        """Initialize MS5611 sensor with configurable I2C pins and address"""
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.i2c_address = i2c_address
        
        # Hardware references
        self.i2c = None
        self.calibration = None
        self.is_initialized = False
    
    def _init_i2c(self):
        """Initialize I2C communication with MS5611 sensor"""
        # Configure I2C bus with specific settings for MS5611
        self.i2c = machine.I2C(0,
                              scl=machine.Pin(self.scl_pin),
                              sda=machine.Pin(self.sda_pin),
                              freq=400000)  # 400kHz I2C frequency
        
        # Check if sensor is present
        devices = self.i2c.scan()
        if self.i2c_address not in devices:
            raise RuntimeError(f"MS5611 not found at I2C address 0x{self.i2c_address:02X}")
    
    def _reset(self):
        """Send reset command to MS5611 sensor"""
        self.i2c.writeto(self.i2c_address, bytearray([0x1E]))  # Send reset command
        time.sleep_ms(3)  # Wait for reset to complete
    
    def _read_prom(self, addr):
        """Read calibration data from sensor's PROM memory"""
        self.i2c.writeto(self.i2c_address, bytearray([addr]))  # Send PROM read address
        data = self.i2c.readfrom(self.i2c_address, 2)          # Read 2 bytes of calibration data
        return int.from_bytes(data, 'big')  # Convert bytes to integer
    
    def _read_calibration(self):
        """Read and validate sensor calibration data"""
        try:
            # Read sensor calibration data (factory programmed values)
            c1 = self._read_prom(0xA2)  # Pressure sensitivity
            c2 = self._read_prom(0xA4)  # Pressure offset
            c3 = self._read_prom(0xA6)  # Temperature coefficient of pressure sensitivity
            c4 = self._read_prom(0xA8)  # Temperature coefficient of pressure offset
            c5 = self._read_prom(0xAA)  # Reference temperature
            c6 = self._read_prom(0xAC)  # Temperature coefficient of temperature
            
            # Basic validation - all values should be non-zero
            calibration = (c1, c2, c3, c4, c5, c6)
            if all(c > 0 for c in calibration):
                self.calibration = calibration
                return True
            else:
                raise ValueError("Invalid calibration values detected")
                
        except Exception as e:
            raise RuntimeError(f"Failed to read calibration: {e}")
    
    def initialize(self):
        """Initialize the MS5611 sensor completely"""
        try:
            # Initialize I2C communication
            self._init_i2c()
            
            # Reset sensor
            self._reset()
            
            # Read and validate calibration
            self._read_calibration()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.is_initialized = False
            raise RuntimeError(f"MS5611 initialization failed: {e}")
    
    def read_pressure(self):
        """Get calibrated pressure reading in mbar"""
        if not self.is_initialized:
            raise RuntimeError("Sensor not initialized")
        
        c1, c2, c3, c4, c5, c6 = self.calibration
        
        # Start pressure conversion with OSR=1024 (fast, good precision)
        self.i2c.writeto(self.i2c_address, bytearray([0x46]))  # Pressure conversion command
        time.sleep_ms(4)  # Wait for conversion (3.3ms + margin)
        
        # Read pressure ADC value
        self.i2c.writeto(self.i2c_address, bytearray([0x00]))  # ADC read command
        data = self.i2c.readfrom(self.i2c_address, 3)          # Read 3 bytes (24-bit result)
        d1 = int.from_bytes(data, 'big')  # Raw pressure
        
        # Start temperature conversion
        self.i2c.writeto(self.i2c_address, bytearray([0x56]))  # Temperature conversion command
        time.sleep_ms(4)  # Wait for conversion
        
        # Read temperature ADC value
        self.i2c.writeto(self.i2c_address, bytearray([0x00]))  # ADC read command
        data = self.i2c.readfrom(self.i2c_address, 3)          # Read 3 bytes
        d2 = int.from_bytes(data, 'big')  # Raw temperature
        
        # Calculate calibrated pressure using MS5611 formulas
        dT = d2 - c5 * 256
        temp = 2000 + dT * c6 // 8388608
        
        off = c2 * 65536 + (c4 * dT) // 128
        sens = c1 * 32768 + (c3 * dT) // 256
        
        pressure = (d1 * sens // 2097152 - off) // 32768
        
        return pressure / 100.0  # Convert to mbar
    
    def get_info(self):
        """Get sensor information for debugging"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        c1, c2, c3, c4, c5, c6 = self.calibration
        return {
            "status": "initialized",
            "calibration": {
                "C1": c1, "C2": c2, "C3": c3,
                "C4": c4, "C5": c5, "C6": c6
            },
            "pins": {
                "scl": self.scl_pin, "sda": self.sda_pin
            },
            "i2c_address": f"0x{self.i2c_address:02X}"
        }
