# ESP32 Vario Project

This project is an open-source variometer (vertical speed indicator) and logger for gliding, paragliding, and other air sports, built on the ESP32 platform.  
It features high-frequency barometric altitude measurement, fast 6-axis motion sensing, and audio feedback.

---

## Features

- **MS5611 Barometric Pressure Sensor** (I2C)
  - High-resolution altitude readings at up to 50 Hz
- **BMI160 6-axis Gyro/Accelerometer** (SPI)
  - Fast, responsive motion and orientation sensing (up to 1600 Hz)
- **Passive Buzzer**
  - Audio feedback for climb/sink rates
- **OLED/Display Support**
  - (Optional) Real-time display of altitude and vario data
- **Remote Debugging**
  - Optional WiFi/WebSocket debug logging
- **Modular, Class-Based Code**
  - Clean separation of hardware, logic, and UI
- **Threaded Audio**
  - Responsive beeping without blocking measurements

---

## Wiring

### MS5611 (Barometer, I2C)
- VCC → 3V3
- GND → GND
- SCL → GPIO 22 (I2C Clock)
- SDA → GPIO 21 (I2C Data)
- CSB → 3V3 (I2C mode)
- SDO, PS → Leave unconnected

### BMI160 (Gyro/Accel, SPI)
- VIN/3V3 → 3V3
- GND → GND
- SCX/SCK → GPIO 18 (SPI Clock)
- SDX/MOSI → GPIO 23 (SPI MOSI)
- SDO/MISO → GPIO 19 (SPI MISO)
- CS → GPIO 5 (SPI Chip Select)
- INT1/INT2 → (Optional) GPIO 25/26 for interrupts
- SAO → Leave unconnected (not needed in SPI mode)
- OCS → Leave unconnected

### Passive Buzzer
- + → GPIO 4 (PWM capable)
- - → GND

---

## Project Structure

```
VarioProject/
├── vario/
│   ├── boot.py
│   ├── main.py
│   ├── config.py
│   └── modules/
│       ├── audio.py
│       ├── boot_config.py
│       ├── calc_v_speed.py
│       ├── frontend.py
│       ├── global_state.py
│       ├── hardware_manager.py
│       ├── network_manager.py
│       ├── sensor.py
│       ├── util.py
│       └── variostate.py
├── wiring.md
└── README.md
```

---

## Getting Started

1. **Wire the hardware** as described above.
2. **Configure your WiFi and debug settings** in `vario/modules/boot_config.py` and `vario/config.py`.
3. **Upload the code** to your ESP32 using [mpremote](https://github.com/micropython/micropython/tree/master/tools/mpremote):
   ```bash
   mpremote connect COM4 fs cp -r ./vario :
   ```
4. **Reset the ESP32**. The system will boot, initialize sensors, and start the main vario logic.

---

## Usage

- **Audio Feedback:** The buzzer will beep according to climb/sink rates.
- **Remote Debugging:** If enabled, logs are sent via WebSocket to your PC.
- **Display (optional):** If connected, shows real-time altitude and vario data.

---

## Customization

- **Sensor Pins:** Change pin assignments in `wiring.md` and `config.py` if needed.
- **Measurement Rate:** Adjust `MEASUREMENT_FREQUENCY` in `config.py`.
- **Audio Profile:** Modify `audio.py` for custom beep patterns.
- **Add Sensors:** Extend `sensor.py` and `hardware_manager.py` for more hardware.

---

## License

MIT License

---

## Credits

- [MS5611 datasheet](https://www.te.com/usa-en/product-CAT-BLPS0036.html)
- [BMI160 datasheet](https://www.bosch-sensortec.com/products/motion-sensors/imus/bmi160/)
- [MicroPython](https://micropython.org/)