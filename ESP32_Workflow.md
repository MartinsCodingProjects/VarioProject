# ESP32 Development Workflow

This document outlines the workflow for developing and managing code on the ESP32, including flashing the firmware and uploading files.

## Prerequisites

1. **Install Python**: Ensure Python is installed on your system.
2. **Install mpremote**: Use the following command to install mpremote:
   ```
   pip install mpremote
   ```
3. **Install esptool**: Use the following command to install esptool:
   ```
   pip install esptool
   ```

## Flashing the ESP32 Firmware

To flash the ESP32 firmware, follow these steps:

1. **Download the MicroPython Firmware**:
   - Visit the [MicroPython Downloads page](https://micropython.org/download/esp32/) and download the appropriate firmware for your ESP32 board.

2. **Erase the Flash**:
   ```
   esptool --port COM4 erase_flash
   ```

3. **Write the Firmware**:
   ```
   esptool --port COM4 write_flash -z 0x1000 firmware.bin
   ```
   Replace `firmware.bin` with the path to the downloaded firmware file.

## Uploading Files to the ESP32

Use the `upload_to_esp32.py` script to upload only relevant files to the ESP32:

1. Run the script:
   ```
   python upload_to_esp32.py
   ```

2. The script will exclude unnecessary files (e.g., `.git`, `__pycache__`) and upload only the required files.

## Debugging and Testing

1. **Connect to the ESP32 REPL**:
   ```
   mpremote connect COM4 repl
   ```

2. **Run a Specific File**:
   ```
   mpremote connect COM4 run main.py
   ```

3. **Check the File System**:
   ```
   mpremote connect COM4 fs ls
   ```

## Notes

- Replace `COM4` with the appropriate port for your ESP32.
- Ensure the ESP32 is in bootloader mode when flashing firmware.
- Use the `upload_to_esp32.py` script to avoid uploading unnecessary files.