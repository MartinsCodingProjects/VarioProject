import time
import gc
from machine import Pin
from _thread import start_new_thread, allocate_lock

from modules.calc_v_speed import get_v_speed
from modules.util import convert_to_altitude, setup_sound_toggle
from modules.frontend import display_v_speed, display_integrated_v_speed
from modules.sensor import init_ms5611, ms5611_pressure_measurement
from modules.audio import handle_beep, init_buzzer

from modules.variostate import VarioState

# Import config variables
from config import (
    MEASUREMENT_FREQUENCY,
    MEASUREMENT_INTERVAL,
    BASE_PRESSURE,
    MINIMAL_DELAY,
    INTEGRATION_INTERVAL,
    POSTIVE_BEEP_THRESHOLD,
    NEGATIVE_BEEP_THRESHOLD,    
    BUZZER_PIN,
    INTERVAL_MS
)

# Initialize global state variables
vario_state = VarioState(BASE_PRESSURE, MEASUREMENT_FREQUENCY, INTEGRATION_INTERVAL)

# Initialize hardware with calibration
## Baro sensor
spi, cs, calibration = init_ms5611(vario_state) # init and calibration of baro sensor
c1, c2, c3, c4, c5, c6 = calibration
vario_state.log("MS5611 sensor initialized with calibration")
## Buzzer
vario_state.buzzer_pwm = init_buzzer(BUZZER_PIN,vario_state)
vario_state.log("Buzzer initialized and Audio ready!")
# Setup sound toggle functionality
boot_button, onboard_led = setup_sound_toggle(vario_state)

# Store references in vario_state if needed
vario_state.boot_button = boot_button
vario_state.onboard_led = onboard_led




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
        current_time = time.ticks_ms()

        # Check if it's time for next measurement
        if time.ticks_diff(current_time, vario_state.last_measurement_time) >= INTERVAL_MS:
            try:
                # Your vario logic here
                measured_pressure = ms5611_pressure_measurement(spi, cs, c1, c2, c3, c4, c5, c6)
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

        # Small sleep to prevent CPU overload while maintaining timing accuracy
        time.sleep_ms(1)

# Start the vario
if __name__ == "__main__":
    run_vario()