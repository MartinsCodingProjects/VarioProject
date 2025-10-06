# ESP32 Vario Wiring

## MS5611 Barometric Pressure Sensor (I2C)
VCC → 3V3
GND → GND
SCL → GPIO 22 (I2C Clock Line)
SDA → GPIO 21 (I2C Data Line)
CSB → 3V3 (for I2C mode)
SDO → Leave unconnected (not needed in I2C mode)
PS → Leave unconnected (not needed in I2C mode)

## BMI160 6-axis Gyro/Accelerometer (SPI)
VIN → 3V3
GND → GND
SCX → GPIO 18 (SPI Clock Line)
SDX → GPIO 23 (SPI Data Line - MOSI)
SDO → GPIO 19 (SPI Data Out - MISO)
CS → GPIO 5 (Chip Select)
SAO → Leave unconnected (not needed in SPI mode)
INT1 → Optional, GPIO 25 (for motion detection or data-ready interrupts)
INT2 → Optional, GPIO 26 (for additional interrupt functionality)
OCS, SDA, SCL → Leave unconnected (not needed in SPI mode)

## Passive Buzzer (PWM Audio Feedback)
Buzzer + → GPIO 4 (PWM capable)
Buzzer - → GND

### Pin Usage Summary:
- GPIO 18, 19, 23, 5: SPI for BMI160 (cannot be shared)
- GPIO 21, 22: I2C for MS5611 (shared I2C bus)
- GPIO 4: PWM for buzzer (dedicated)
- GPIO 25, 26: Optional interrupt pins for BMI160
- 3V3, GND: Power rails (shared)

### Why Use Interrupts for the BMI160?
Interrupts are optional but can be useful for:
1. **Motion Detection**: The BMI160 can generate an interrupt when motion is detected (e.g., for wake-on-motion functionality)
2. **Data-Ready Signals**: The BMI160 can signal when new accelerometer or gyroscope data is available, reducing the need for constant polling
3. **Power Optimization**: Interrupts allow the ESP32 to sleep and wake only when necessary, saving power

If you don't need these features, you can leave the INT1 and INT2 pins unconnected.

### Why Passive Buzzer?
- **Passive buzzer**: Can generate any frequency via PWM (needed for variable pitch vario tones)
- **Active buzzer**: Fixed frequency only (~2kHz), just on/off - not suitable for vario audio

### Why SPI for BMI160 and I2C for MS5611?
- **SPI for BMI160**: SPI is faster and allows the BMI160 to output data at very high rates (up to 1600 Hz for gyro, 800 Hz for accel). This enables ultra-fast, responsive motion detection and advanced filtering
- **I2C for MS5611**: The MS5611 is typically sampled at lower rates (10–50 Hz) for altitude/pressure measurements. I2C is fast enough for these rates and only uses two pins, simplifying wiring

### Why GPIO 4?
- **PWM capable**: Can generate variable frequency signals
- **No conflicts**: Doesn't interfere with SPI pins
- **Available**: Not used by ESP32 system functions
- **Good drive capability**: Can directly drive small buzzer

### Alternative Pins (if needed):
- **Buzzer (PWM)**: Default GPIO 4, alternatives: GPIO 2, GPIO 16, GPIO 17
- **Interrupts (BMI160)**: Default GPIO 25 (INT1), GPIO 26 (INT2), alternatives: any free GPIO pins

### Pin Sharing NOT Possible:
SPI pins (18, 19, 23, 5) cannot be shared with other devices as they use specific timing and protocols. The buzzer needs its own dedicated PWM pin.