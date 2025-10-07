import time
import gc
from _thread import allocate_lock

from modules.calc_v_speed import get_v_speed
from modules.util import convert_to_altitude
from modules.frontend import display_v_speed
import modules.global_state as global_state

# Import config variables
from config import (
    MEASUREMENT_FREQUENCY,
    MINIMAL_DELAY,
    INTEGRATION_INTERVAL,
    POSTIVE_BEEP_THRESHOLD,
    NEGATIVE_BEEP_THRESHOLD,    
    INTERVAL_MS
)

def main():
    """
    Main vario application - reads sensors and calculates vertical speed
    
    Prerequisites: boot.py must have successfully initialized all hardware
    """
    
    # Get initialized components from boot.py
    vario_state = global_state.vario_state
    ms5611_sensor = global_state.ms5611_object
    bmi160_sensor = global_state.bmi160_object
    audio_system = global_state.audio_system
    
    # Simple validation - if boot.py failed, we can't continue
    if not vario_state:
        print("FATAL: VarioState not initialized by boot.py")
        return
        
    if not ms5611_sensor or not ms5611_sensor.is_initialized:
        vario_state.log("FATAL: MS5611 sensor not available - cannot run vario")
        return
    
    # Log what we have available
    vario_state.log("=== MAIN APPLICATION STARTING ===")
    vario_state.log(f"MS5611 Sensor: {'✓ Ready' if ms5611_sensor.is_initialized else '✗ Failed'}")
    vario_state.log(f"BMI160 Sensor: {'✓ Ready' if (bmi160_sensor and bmi160_sensor.is_initialized) else '✗ Not Available'}")
    vario_state.log(f"Audio System: {'✓ Ready' if (audio_system and audio_system.is_initialized) else '✗ Not Available'}")
    
    # Start audio feedback if available
    v_speed_lock = allocate_lock()
    if audio_system and audio_system.is_initialized:
        audio_system.start_beep_handler(vario_state, v_speed_lock, POSTIVE_BEEP_THRESHOLD, NEGATIVE_BEEP_THRESHOLD)
        vario_state.log("Audio feedback enabled")
    else:
        vario_state.log("Audio feedback disabled - continuing without sound")
    
    # Start main measurement loop
    run_vario_loop(vario_state, ms5611_sensor, bmi160_sensor, v_speed_lock)


def run_vario_loop(vario_state, ms5611_sensor, bmi160_sensor, v_speed_lock):
    """
    Main vario measurement loop
    
    Runs continuously at MEASUREMENT_FREQUENCY Hz
    Reads barometric pressure and calculates vertical speed
    """
    vario_state.last_measurement_time = time.ticks_ms()
    vario_state.log(f"Starting vario loop at {MEASUREMENT_FREQUENCY} Hz")
    
    while True:
        if vario_state.turned_on:
            measure_and_calculate(vario_state, ms5611_sensor, bmi160_sensor, v_speed_lock)
        time.sleep_ms(1)  # Small delay to prevent CPU overload


def measure_and_calculate(vario_state, ms5611_sensor, bmi160_sensor, v_speed_lock):
    """
    Single measurement cycle: read sensors, calculate altitude and vertical speed
    """
    current_time = time.ticks_ms()
    
    # Check if it's time for next measurement
    if time.ticks_diff(current_time, vario_state.last_measurement_time) < INTERVAL_MS:
        return  # Not time yet
    
    try:
        # Read barometric pressure
        pressure = ms5611_sensor.read_pressure()
        altitude = convert_to_altitude(pressure, vario_state.estimated_local_pressure)
        
        # Update altitude history (sliding window)
        vario_state.altitude_log.append(altitude)
        vario_state.altitude_log.pop(0)
        
        # Calculate vertical speed (thread-safe)
        with v_speed_lock:
            vario_state.v_speed = round(
                get_v_speed(vario_state.altitude_log, vario_state.last_v_speed, 
                           MEASUREMENT_FREQUENCY, MINIMAL_DELAY), 2
            )
        
        # Calculate integrated vertical speed (smoothed over longer time)
        vario_state.integrated_v_speed = round(
            (altitude - vario_state.altitude_log[0]) / INTEGRATION_INTERVAL, 2
        )
        
        # Display updates (only when values change)
        if vario_state.v_speed != vario_state.last_v_speed:
            display_v_speed(vario_state.v_speed, vario_state)
        
        # Update state for next cycle
        vario_state.last_v_speed = vario_state.v_speed
        vario_state.last_integrated_v_speed = vario_state.integrated_v_speed
        vario_state.last_measurement_time += INTERVAL_MS
        vario_state.measurement_count += 1
        
        # Periodic garbage collection (every 2 seconds)
        if vario_state.measurement_count % (2 * MEASUREMENT_FREQUENCY) == 0:
            gc.collect()
            vario_state.measurement_count = 0
            
    except Exception as e:
        vario_state.log(f"Measurement error: {e}")
        # Keep timing even if measurement fails
        vario_state.last_measurement_time += INTERVAL_MS


# Start the application
if __name__ == "__main__":
    main()