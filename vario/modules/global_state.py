"""
Global State Module

This module provides shared variables between boot.py and main.py
All hardware and system objects are initialized in boot.py and accessed in main.py

For beginners: Think of this as a "shared storage box" where boot.py puts
all the initialized hardware, and main.py takes it out to use it.
"""

# === CORE SYSTEM ===
vario_state = None          # Main system state (measurements, settings, logging)

# === SENSORS ===
ms5611_object = None        # Barometric pressure sensor (CRITICAL - required for vario)
bmi160_object = None        # Motion sensor (OPTIONAL - for advanced features)

# === ACTUATORS ===
audio_system = None         # Buzzer system (OPTIONAL - for audio feedback)

# === STATUS FLAGS ===
hardware_initialized = False   # True if all critical hardware is working


def get_status_summary():
    """
    Helper function for debugging - shows what's available
    """
    status = {
        'vario_state': vario_state is not None,
        'ms5611_sensor': ms5611_object is not None and ms5611_object.is_initialized,
        'bmi160_sensor': bmi160_object is not None and bmi160_object.is_initialized,
        'audio_system': audio_system is not None and audio_system.is_initialized,
        'hardware_ok': hardware_initialized
    }
    return status