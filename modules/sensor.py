def init_spi():
    import machine
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
    import time
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

def ms5611_pressure_measurement(spi, cs):
    """Start pressure conversion and read result"""
    # Start pressure conversion with OSR=1024 (fast, good precision)
    cs.value(0)
    spi.write(bytearray([0x46]))   # Pressure conversion command
    cs.value(1)
    time.sleep_ms(4)               # Wait for conversion (3.3ms + margin)
    
    # Read the converted value
    cs.value(0)
    spi.write(bytearray([0x00]))   # ADC read command
    data = spi.read(3)             # Read 3 bytes (24-bit result)
    cs.value(1)
    return int.from_bytes(data, 'big')