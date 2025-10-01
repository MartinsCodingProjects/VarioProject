import machine, time

def init_spi():
    """Initialize SPI communication with MS5611 sensor"""
    # Configure SPI bus with specific settings for MS5611
    spi = machine.SPI(1, 
                     baudrate=1000000,      # 1MHz clock speed
                     polarity=0,            # Clock idle state = low
                     phase=0,               # Data sampled on rising edge
                     bits=8,                # 8-bit data
                     firstbit=machine.SPI.MSB,  # Most significant bit first
                     sck=machine.Pin(18),   # SPI clock pin
                     mosi=machine.Pin(23),  # Master out, slave in
                     miso=machine.Pin(19))  # Master in, slave out
    
    # Chip select pin - controls when we talk to the sensor
    cs = machine.Pin(5, machine.Pin.OUT)
    cs.value(1)  # Start deselected (high = not talking to sensor)
    
    return spi, cs

def ms5611_reset(spi, cs):
    """Send reset command to MS5611 sensor"""
    cs.value(0)                    # Select sensor (pull CS low)
    spi.write(bytearray([0x1E]))   # Send reset command
    cs.value(1)                    # Deselect sensor
    time.sleep_ms(3)               # Wait for reset to complete

def ms5611_read_prom(spi, cs, addr):
    """Read calibration data from sensor's PROM memory"""
    cs.value(0)                    # Select sensor
    spi.write(bytearray([addr]))   # Send PROM read address
    data = spi.read(2)             # Read 2 bytes of calibration data
    cs.value(1)                    # Deselect sensor
    return int.from_bytes(data, 'big')  # Convert bytes to integer

def ms5611_pressure_measurement(spi, cs, c1, c2, c3, c4, c5, c6):
    """Get calibrated pressure reading in mbar"""
    # Start pressure conversion with OSR=1024 (fast, good precision)
    cs.value(0)
    spi.write(bytearray([0x46]))   # Pressure conversion command
    cs.value(1)
    time.sleep_ms(4)               # Wait for conversion (3.3ms + margin)
    
    # Read pressure ADC value
    cs.value(0)
    spi.write(bytearray([0x00]))   # ADC read command
    data = spi.read(3)             # Read 3 bytes (24-bit result)
    cs.value(1)
    d1 = int.from_bytes(data, 'big')  # Raw pressure
    
    # Start temperature conversion
    cs.value(0)
    spi.write(bytearray([0x56]))   # Temperature conversion command
    cs.value(1)
    time.sleep_ms(4)               # Wait for conversion
    
    # Read temperature ADC value
    cs.value(0)
    spi.write(bytearray([0x00]))   # ADC read command
    data = spi.read(3)             # Read 3 bytes
    cs.value(1)
    d2 = int.from_bytes(data, 'big')  # Raw temperature
    
    # Calculate calibrated pressure using MS5611 formulas
    dT = d2 - c5 * 256
    temp = 2000 + dT * c6 // 8388608
    
    off = c2 * 65536 + (c4 * dT) // 128
    sens = c1 * 32768 + (c3 * dT) // 256
    
    pressure = (d1 * sens // 2097152 - off) // 32768
    
    return pressure / 100.0  # Convert to mbar

def init_ms5611(vario_state):
    """Initialize MS5611 and read calibration data"""
    spi, cs = init_spi()
    ms5611_reset(spi, cs)
    
    # Read sensor calibration data (factory programmed values)
    vario_state.log("Reading calibration data...")
    c1 = ms5611_read_prom(spi, cs, 0xA2)  # Pressure sensitivity
    c2 = ms5611_read_prom(spi, cs, 0xA4)  # Pressure offset
    c3 = ms5611_read_prom(spi, cs, 0xA6)  # Temperature coefficient of pressure sensitivity
    c4 = ms5611_read_prom(spi, cs, 0xA8)  # Temperature coefficient of pressure offset
    c5 = ms5611_read_prom(spi, cs, 0xAA)  # Reference temperature
    c6 = ms5611_read_prom(spi, cs, 0xAC)  # Temperature coefficient of temperature
    
    vario_state.log(f"Calibration: C1={c1}, C2={c2}, C3={c3}, C4={c4}, C5={c5}, C6={c6}")
    
    return spi, cs, (c1, c2, c3, c4, c5, c6)