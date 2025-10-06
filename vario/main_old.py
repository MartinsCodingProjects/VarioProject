import time
import gc
from _thread import start_new_thread, allocate_lock

from modules.calc_v_speed import get_v_speed
from modules.util import convert_to_altitude
from modules.frontend import display_v_speed, display_integrated_v_speed
from modules.sensor import MS5611Sensor
from modules.audio import handle_beep
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

# Initialize sensor variables and calibration coefficients
sensor_object = None
spi = None
cs = None
calibration = None
c1 = c2 = c3 = c4 = c5 = c6 = None  # Calibration coefficients

if hardware_initialized:
    # Access hardware components initialized in boot.py
    sensor_object = global_state.sensor_object  # New class-based sensor
    spi = global_state.sensor_spi               # Legacy fallback
    cs = global_state.sensor_cs                 # Legacy fallback
    calibration = global_state.sensor_calibration  # Legacy fallback
    
    if sensor_object and sensor_object.is_initialized:
        vario_state.log("Main application using modern MS5611Sensor class from boot.py")
    elif calibration is not None:
        try:
            c1, c2, c3, c4, c5, c6 = calibration
            vario_state.log("Main application using legacy sensor functions from boot.py")
        except (ValueError, TypeError) as e:
            vario_state.log(f"Error unpacking calibration data: {e}")
            calibration = None
    
if not hardware_initialized or (not sensor_object and calibration is None):
    vario_state.log("Warning: Sensor not properly initialized in boot.py, attempting fallback initialization")
    try:
        # Fallback hardware initialization
        spi, cs, calibration = init_ms5611(vario_state)
        c1, c2, c3, c4, c5, c6 = calibration
        vario_state.log("Fallback sensor initialization completed")
    except Exception as e:
        vario_state.log(f"Critical error: Failed to initialize sensor in fallback mode: {e}")
        raise SystemExit("Cannot proceed without sensor initialization")


# Create lock
v_speed_lock = allocate_lock()

# Start thread with positional arguments
start_new_thread(handle_beep, (v_speed_lock, vario_state, POSTIVE_BEEP_THRESHOLD, NEGATIVE_BEEP_THRESHOLD))

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