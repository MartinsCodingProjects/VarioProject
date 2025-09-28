def get_v_speed(altitude_log, last_v_speed=0.0, 
                MEASUREMENT_FREQUENCY=50, MINIMAL_DELAY=0.1):
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
    
    # Indices for different time intervals
    short_idx = -int(MINIMAL_DELAY * MEASUREMENT_FREQUENCY)  # -5 (0.1s * 50Hz)
    mid_idx = -int(MEASUREMENT_FREQUENCY * 0.5)              # -25 (0.5s * 50Hz)  
    long_idx = -int(2 * MEASUREMENT_FREQUENCY)               # -100 (2.0s * 50Hz)
    
    # Calculate altitude differences
    short_term_diff = altitude_log[-1] - altitude_log[short_idx]
    mid_term_diff = altitude_log[-1] - altitude_log[mid_idx]  
    long_term_diff = altitude_log[-1] - altitude_log[long_idx]
    
    # Convert to velocities (divide by time intervals)
    short_v = short_term_diff / MINIMAL_DELAY      # m/s over 0.1s
    mid_v = mid_term_diff / 0.5                    # m/s over 0.5s
    long_v = long_term_diff / 2.0                  # m/s over 2.0s
    
    # Weighted average
    v_speed = (3 * short_v + 2 * mid_v + 1 * long_v) / 6
    
    # Low-pass filter
    alpha = 0.7
    v_speed = alpha * v_speed + (1 - alpha) * last_v_speed
    
    return v_speed
