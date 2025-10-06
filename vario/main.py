import time
import gc
from _thread import start_new_thread, allocate_lock

from modules.calc_v_speed import get_v_speed
from modules.util import convert_to_altitude
from modules.frontend import display_v_speed, display_integrated_v_speed
from modules.sensor import MS5611Sensor
from modules.audio import AudioSystem
import modules.global_state as global_state

# Import config variables
from config import (
    MEASUREMENT_FREQUENCY,
    MINIMAL_DELAY,
    INTEGRATION_INTERVAL,
    POSTIVE_BEEP_THRESHOLD,
    NEGATIVE_BEEP_THRESHOLD,    
    INTERVAL_MS,
    BASE_PRESSURE
)

# Access the global vario_state initialized in boot.py
vario_state = global_state.vario_state

if vario_state is None:
    # Fallback: create vario_state if not available from boot.py
    from modules.variostate import VarioState
    vario_state = VarioState(BASE_PRESSURE, MEASUREMENT_FREQUENCY, INTEGRATION_INTERVAL)
    global_state.vario_state = vario_state
    print("Warning: vario_state not found from boot.py, created new instance")

# Check if hardware was successfully initialized in boot.py
hardware_initialized = global_state.hardware_initialized
sensor_object = global_state.sensor_object
audio_system = global_state.audio_system

if not hardware_initialized or not sensor_object or not sensor_object.is_initialized:
    vario_state.log("Warning: Sensor not properly initialized in boot.py, attempting emergency initialization")
    try:
        # Emergency sensor initialization with I2C configuration
        sensor_object = MS5611Sensor(scl_pin=22, sda_pin=21, i2c_address=0x77)
        sensor_object.initialize()
        vario_state.log("Emergency sensor initialization completed")
    except Exception as e:
        vario_state.log(f"Critical error: Failed to initialize sensor: {e}")
        raise SystemExit("Cannot proceed without sensor initialization")
else:
    vario_state.log("Main application using MS5611Sensor class from boot.py")

# Initialize audio system if not available from boot.py
if not audio_system or not audio_system.is_initialized:
    vario_state.log("Warning: AudioSystem not available from boot.py, attempting emergency initialization")
    try:
        from config import BUZZER_PIN
        audio_system = AudioSystem(BUZZER_PIN)
        audio_system.initialize()
        vario_state.log("Emergency AudioSystem initialization completed")
    except Exception as e:
        vario_state.log(f"Warning: AudioSystem initialization failed: {e}")
        audio_system = None
else:
    vario_state.log("Main application using AudioSystem from boot.py")

# Create lock
v_speed_lock = allocate_lock()

# Start audio beep handler if audio system is available
if audio_system and audio_system.is_initialized:
    audio_system.start_beep_handler(vario_state, v_speed_lock, POSTIVE_BEEP_THRESHOLD, NEGATIVE_BEEP_THRESHOLD)
else:
    vario_state.log("Warning: Audio feedback disabled - AudioSystem not available")

def run_vario():
    """ESP32 optimized vario loop with precise timing control"""
    global vario_state
    
    vario_state.last_measurement_time = time.ticks_ms()
    
    vario_state.log(f"Starting vario at {MEASUREMENT_FREQUENCY} Hz (interval: {INTERVAL_MS} ms)")
    
    # Main loop Thread for measurements
    while True:
        if vario_state.turned_on:
            mainloop_function()
        # Small sleep to prevent CPU overload while maintaining timing accuracy
        time.sleep_ms(1)

def mainloop_function():
        current_time = time.ticks_ms()

        # Check if it's time for next measurement
        if time.ticks_diff(current_time, vario_state.last_measurement_time) >= INTERVAL_MS:
            try:
                # Read pressure using the MS5611Sensor class
                measured_pressure = sensor_object.read_pressure()
                altitude = convert_to_altitude(measured_pressure, vario_state.estimated_local_pressure)

                # add new measurements to logs and drop oldest entry
                vario_state.altitude_log.append(altitude)
                vario_state.altitude_log.pop(0)

                # Update v_speed in a thread-safe manner
                with v_speed_lock:
                    vario_state.v_speed = round(
                        get_v_speed(vario_state.altitude_log, vario_state.last_v_speed, MEASUREMENT_FREQUENCY, MINIMAL_DELAY), 2
                    )

                vario_state.integrated_v_speed = round((altitude - vario_state.altitude_log[0]) / INTEGRATION_INTERVAL, 2)

                if vario_state.v_speed != vario_state.last_v_speed:
                    display_v_speed(vario_state.v_speed, vario_state)
                # if vario_state.integrated_v_speed != vario_state.last_integrated_v_speed:
                   # display_integrated_v_speed(vario_state.integrated_v_speed, vario_state)

                vario_state.last_integrated_v_speed = vario_state.integrated_v_speed
                vario_state.last_v_speed = vario_state.v_speed

                # Update last measurement time
                vario_state.last_measurement_time += INTERVAL_MS
                vario_state.measurement_count += 1

                # Optional: Garbage collection every 100 measurements (every 2 seconds at 50Hz)
                if vario_state.measurement_count % (2 * MEASUREMENT_FREQUENCY) == 0:
                    gc.collect()
                    vario_state.measurement_count = 0  # Reset count after GC

            except Exception as e:
                vario_state.log(f"Measurement error: {e}")
                # Continue timing even if measurement fails
                vario_state.last_measurement_time += INTERVAL_MS

# Start the vario
if __name__ == "__main__":
    run_vario()