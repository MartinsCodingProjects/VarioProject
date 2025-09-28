# ESP32 Vario Wiring

## MS5611 Barometric Pressure Sensor (SPI)
VCC → 3V3
GND → GND
SCL → GPIO 18 (SCK)
SDA → GPIO 23 (MOSI)
CSB → GPIO 5 (CS)
SDO → GPIO 19 (MISO)
PS → GND (for SPI mode)

## Passive Buzzer (PWM Audio Feedback)
Buzzer + → GPIO 4 (PWM capable)
Buzzer - → GND

### Pin Usage Summary:
- GPIO 18, 19, 23: SPI for MS5611 (cannot be shared)
- GPIO 5: Chip Select for MS5611 (cannot be shared)
- GPIO 4: PWM for buzzer (dedicated)
- 3V3, GND: Power rails (shared)

### Why Passive Buzzer?
- **Passive buzzer**: Can generate any frequency via PWM (needed for variable pitch vario tones)
- **Active buzzer**: Fixed frequency only (~2kHz), just on/off - not suitable for vario audio

### Why GPIO 4?
- **PWM capable**: Can generate variable frequency signals
- **No conflicts**: Doesn't interfere with SPI pins
- **Available**: Not used by ESP32 system functions
- **Good drive capability**: Can directly drive small buzzer

### Alternative Pins (if GPIO 4 is needed elsewhere):
- GPIO 2 (has built-in LED, but usable for PWM)
- GPIO 16, 17 (free GPIOs with PWM)
- GPIO 21, 22 (I2C pins by default, but free if not using I2C)

### Pin Sharing NOT Possible:
SPI pins (18, 19, 23, 5) cannot be shared with other devices as they use specific timing and protocols. The buzzer needs its own dedicated PWM pin.