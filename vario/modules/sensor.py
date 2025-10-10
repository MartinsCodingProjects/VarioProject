import machine, time

class MS5611Sensor:
    """MS5611 Barometric Pressure Sensor Driver (I2C Mode)"""
    
    def __init__(self, scl_pin=22, sda_pin=21, i2c_address=0x76):
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
        # Use readfrom_mem for compatibility with test script
        data = self.i2c.readfrom_mem(self.i2c_address, addr, 2)
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
        self.i2c.writeto(self.i2c_address, bytearray([0x48]))  # Pressure conversion command (matches test script)
        time.sleep_ms(10)  # Wait for conversion (10ms as in test script)
        
        # Read pressure ADC value
        d1 = int.from_bytes(self.i2c.readfrom_mem(self.i2c_address, 0x00, 3), 'big')  # Use readfrom_mem
        
        # Start temperature conversion
        self.i2c.writeto(self.i2c_address, bytearray([0x58]))  # Temperature conversion command (matches test script)
        time.sleep_ms(10)  # Wait for conversion
        
        # Read temperature ADC value
        d2 = int.from_bytes(self.i2c.readfrom_mem(self.i2c_address, 0x00, 3), 'big')  # Use readfrom_mem
        
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


class BMI160Sensor:
    """BMI160 6-axis Gyro/Accelerometer Sensor Driver (I2C Mode)"""
    
    def __init__(self, scl_pin=22, sda_pin=21, i2c_address=0x68, int1_pin=None, int2_pin=None):
        """Initialize BMI160 sensor with configurable I2C pins and address"""
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.i2c_address = i2c_address
        self.int1_pin = int1_pin
        self.int2_pin = int2_pin
        
        # Hardware references
        self.i2c = None
        self.is_initialized = False
        
        # BMI160 register addresses
        self.BMI160_CHIP_ID = 0x00
        self.BMI160_ACCEL_CONFIG = 0x40
        self.BMI160_GYRO_CONFIG = 0x42
        self.BMI160_CMD = 0x7E
        self.BMI160_ACCEL_DATA = 0x12
        self.BMI160_GYRO_DATA = 0x0C
        
        # Commands
        self.CMD_ACCEL_NORMAL = 0x11
        self.CMD_GYRO_NORMAL = 0x15
        self.CMD_SOFT_RESET = 0xB6
        
        # Expected chip ID
        self.CHIP_ID_VALUE = 0xD1
    
    def _init_i2c(self):
        """Initialize I2C communication with BMI160 sensor"""
        # Configure I2C bus with specific settings for BMI160
        self.i2c = machine.I2C(0,
                              scl=machine.Pin(self.scl_pin),
                              sda=machine.Pin(self.sda_pin),
                              freq=400000)  # 400kHz I2C frequency
        
        # Check if sensor is present
        devices = self.i2c.scan()
        if self.i2c_address not in devices:
            raise RuntimeError(f"BMI160 not found at I2C address 0x{self.i2c_address:02X}")
        
        # Configure interrupt pins if provided
        if self.int1_pin:
            self.int1 = machine.Pin(self.int1_pin, machine.Pin.IN)
        if self.int2_pin:
            self.int2 = machine.Pin(self.int2_pin, machine.Pin.IN)
    
    def _read_register(self, reg_addr):
        """Read a single register from BMI160"""
        data = self.i2c.readfrom_mem(self.i2c_address, reg_addr, 1)
        return data[0]
    
    def _write_register(self, reg_addr, value):
        """Write a single register to BMI160"""
        self.i2c.writeto_mem(self.i2c_address, reg_addr, bytearray([value]))
        time.sleep_ms(1)  # Small delay after write
    
    def _read_multiple_registers(self, reg_addr, num_bytes):
        """Read multiple registers from BMI160"""
        data = self.i2c.readfrom_mem(self.i2c_address, reg_addr, num_bytes)
        return data
    
    def _soft_reset(self):
        """Perform soft reset of BMI160"""
        self._write_register(self.BMI160_CMD, self.CMD_SOFT_RESET)
        time.sleep_ms(15)  # Wait for reset to complete
    
    def _check_chip_id(self):
        """Verify BMI160 chip ID"""
        chip_id = self._read_register(self.BMI160_CHIP_ID)
        if chip_id != self.CHIP_ID_VALUE:
            raise RuntimeError(f"BMI160 not found. Expected chip ID 0x{self.CHIP_ID_VALUE:02X}, got 0x{chip_id:02X}")
        return True
    
    def _configure_sensor(self):
        """Configure BMI160 accelerometer and gyroscope"""
        # Enable accelerometer in normal mode
        self._write_register(self.BMI160_CMD, self.CMD_ACCEL_NORMAL)
        time.sleep_ms(5)
        
        # Enable gyroscope in normal mode
        self._write_register(self.BMI160_CMD, self.CMD_GYRO_NORMAL)
        time.sleep_ms(80)  # Gyro needs more time to start
        
        # Configure accelerometer: ±4g range, 100Hz ODR
        self._write_register(self.BMI160_ACCEL_CONFIG, 0x28)
        
        # Configure gyroscope: ±500°/s range, 100Hz ODR
        self._write_register(self.BMI160_GYRO_CONFIG, 0x28)
    
    def initialize(self):
        """Initialize the BMI160 sensor completely"""
        try:
            # Initialize I2C communication
            self._init_i2c()
            
            # Soft reset sensor
            self._soft_reset()
            
            # Check chip ID
            self._check_chip_id()
            
            # Configure sensor
            self._configure_sensor()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.is_initialized = False
            raise RuntimeError(f"BMI160 initialization failed: {e}")
    
    def read_accel(self):
        """Read accelerometer data (x, y, z in g)"""
        if not self.is_initialized:
            raise RuntimeError("Sensor not initialized")
        
        # Read 6 bytes of accelerometer data
        data = self._read_multiple_registers(self.BMI160_ACCEL_DATA, 6)
        
        # Convert to signed 16-bit values
        accel_x = int.from_bytes(data[0:2], 'little', signed=True)
        accel_y = int.from_bytes(data[2:4], 'little', signed=True)
        accel_z = int.from_bytes(data[4:6], 'little', signed=True)
        
        # Convert to g (±4g range, 16-bit resolution)
        scale = 4.0 / 32768.0
        return (accel_x * scale, accel_y * scale, accel_z * scale)
    
    def read_gyro(self):
        """Read gyroscope data (x, y, z in °/s)"""
        if not self.is_initialized:
            raise RuntimeError("Sensor not initialized")
        
        # Read 6 bytes of gyroscope data
        data = self._read_multiple_registers(self.BMI160_GYRO_DATA, 6)
        
        # Convert to signed 16-bit values
        gyro_x = int.from_bytes(data[0:2], 'little', signed=True)
        gyro_y = int.from_bytes(data[2:4], 'little', signed=True)
        gyro_z = int.from_bytes(data[4:6], 'little', signed=True)
        
        # Convert to °/s (±500°/s range, 16-bit resolution)
        scale = 500.0 / 32768.0
        return (gyro_x * scale, gyro_y * scale, gyro_z * scale)
    
    def read_all(self):
        """Read both accelerometer and gyroscope data"""
        accel = self.read_accel()
        gyro = self.read_gyro()
        return {"accel": accel, "gyro": gyro}
    
    def get_info(self):
        """Get sensor information for debugging"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        # Read chip ID for verification
        chip_id = self._read_register(self.BMI160_CHIP_ID)
        
        return {
            "status": "initialized",
            "chip_id": f"0x{chip_id:02X}",
            "pins": {
                "scl": self.scl_pin,
                "sda": self.sda_pin
            },
            "i2c_address": f"0x{self.i2c_address:02X}",
            "interrupts": {
                "int1": self.int1_pin,
                "int2": self.int2_pin
            },
            "config": {
                "accel_range": "±4g",
                "gyro_range": "±500°/s",
                "sample_rate": "100Hz"
            }
        }
