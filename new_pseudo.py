## config
import time
import gc

MEASUREMENT_FREQUENCY = 50
MEASUREMENT_INTERVAL = 1 / MEASUREMENT_FREQUENCY # seconds
BASE_PRESSURE = 1013.25  # hPa, sea level standard atmospheric pressure
MINIMAL_DELAY = 0.1  # seconds
INTEGRATION_INTERVAL = 12.0  # seconds for integrated vertical speed

# Global variables
v_speed = 0.00 # rounded to 2 decimal places, m/s
last_v_speed = 0.00 # rounded to 2 decimal places, m/s

integrated_v_speed = 0.00 # rounded to 2 decimal places, m/s
last_integrated_v_speed = 0.00 # rounded to 2 decimal places, m/s

estimated_local_pressure = BASE_PRESSURE  # Initial pressure for altitude calculations

altitude_log = [0] * int(INTEGRATION_INTERVAL * MEASUREMENT_FREQUENCY)

def get_v_speed(altitude_log):
    """
    Calculate the vertical speed based on altitude changes over time.
    - uses different filters to smooth out readings
    - smooths data
    - get rid of noises
    - uses multiple intervals to calculate a more stable vertical speed
    - applies a low-pass filter to the result
    - reduces the impact of sudden spikes or drops in altitude
    - combines data from multiple sensors (if available, later on)

    Args:
        altitude_log (list): A list of recent altitude readings.
    Returns:
        float: The vertical speed in m/s.

    todo:
    - log timestamp for each altitude reading
    - use timestamps to calculate exact time differences and get correct altitude entries
    - implement a more sophisticated filtering algorithm (e.g., Kalman filter) for better accuracy
    """
    
    if len(altitude_log) < 2:
        return 0.0  # Not enough data to calculate vertical speed
    

    # Calculate differences over multiple intervals
    short_term_diff = altitude_log[-1] - altitude_log[-MINIMAL_DELAY * MEASUREMENT_FREQUENCY]  # minimal interval
    mid_term_diff = altitude_log[-1] - altitude_log[-MEASUREMENT_FREQUENCY/2] # 0.5s interval
    long_term_diff = altitude_log[-1] - altitude_log[-(2*MEASUREMENT_FREQUENCY)] # 2s interval

    # simpel estimation for starting out - will be improved with more data and testing
    # weighted average of the different intervals
    v_speed = ((3 * short_term_diff) + (2 * mid_term_diff) + (1 * long_term_diff)) / 6  # Weighted average
    # Apply a simple low-pass filter to smooth out the vertical speed
    alpha = 0.7  # Smoothing factor (0 < alpha < 1)
    global last_v_speed
    v_speed = alpha * v_speed + (1 - alpha) * last_v_speed
    return v_speed

def pressure_measurement():
    """
    Measure the current pressure from the sensor.
    Returns:
        float: The current pressure in mbar.
    """
    pass

def convert_to_altitude(pressure, base_pressure):
    """
    Convert pressure in mbar to altitude in meters using the barometric formula.
    Args:
        pressure (float): The current pressure in mbar.
        base_pressure (float): The reference sea-level pressure in mbar.
    Returns:
        float: The altitude in meters.
    """
    # Barometric formula
    return (1 - (pressure / base_pressure) ** 0.190284) * 145366.45 / 3.28084  # Convert feet to meters

def display_v_speed(v_speed):
    """
    Display the current vertical speed
    used for visual feedback and audio cues (later on)
    """
    print(f"Vertical Speed: {v_speed:.2f} m/s")

def display_integrated_v_speed(integrated_v_speed):
    """
    Display the integrated vertical speed
    """
    print(f"Integrated Vertical Speed: {integrated_v_speed:.2f} m/s")

def run_vario():
    """ESP32 optimized vario loop with precise timing control"""
    global v_speed, last_v_speed, integrated_v_speed, last_integrated_v_speed
    global altitude_log, estimated_local_pressure
    
    last_measurement_time = time.ticks_ms()
    interval_ms = int(MEASUREMENT_INTERVAL * 1000)  # Convert to milliseconds
    measurement_count = 0
    
    print(f"Starting vario at {MEASUREMENT_FREQUENCY} Hz (interval: {interval_ms} ms)")
    
    while True:
        current_time = time.ticks_ms()
        
        # Check if it's time for next measurement
        if time.ticks_diff(current_time, last_measurement_time) >= interval_ms:
            try:
                # Your vario logic here
                measured_pressure = pressure_measurement()
                altitude = convert_to_altitude(measured_pressure, estimated_local_pressure)

                # add new measurements to logs and drop oldest entry
                altitude_log.append(altitude)
                altitude_log.pop(0)

                v_speed = round(get_v_speed(altitude_log), 2)
                integrated_v_speed = round(altitude - altitude_log[0] / INTEGRATION_INTERVAL, 2)

                if v_speed != last_v_speed:
                    display_v_speed(v_speed)
                if integrated_v_speed != last_integrated_v_speed:
                    display_integrated_v_speed(integrated_v_speed)

                last_integrated_v_speed = integrated_v_speed
                last_v_speed = v_speed
                
                # Update last measurement time
                last_measurement_time += interval_ms
                measurement_count += 1
                
                # Optional: Garbage collection every 100 measurements (every 2 seconds at 50Hz)
                if measurement_count % (2 * MEASUREMENT_FREQUENCY) == 0:
                    gc.collect()
                    
            except Exception as e:
                print(f"Measurement error: {e}")
                # Continue timing even if measurement fails
                last_measurement_time += interval_ms
        
        # Small sleep to prevent CPU overload while maintaining timing accuracy
        time.sleep_ms(1)

# Start the vario
if __name__ == "__main__":
    run_vario()