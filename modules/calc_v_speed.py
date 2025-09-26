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
    

    # Calculate differences over multiple intervals
    short_term_diff = altitude_log[-1] - altitude_log[-MINIMAL_DELAY * MEASUREMENT_FREQUENCY]  # minimal interval
    mid_term_diff = altitude_log[-1] - altitude_log[-MEASUREMENT_FREQUENCY/2] # 0.5s interval
    long_term_diff = altitude_log[-1] - altitude_log[-(2*MEASUREMENT_FREQUENCY)] # 2s interval

    # simpel estimation for starting out - will be improved with more data and testing
    # weighted average of the different intervals
    v_speed = ((3 * short_term_diff) + (2 * mid_term_diff) + (1 * long_term_diff)) / 6  # Weighted average
    # Apply a simple low-pass filter to smooth out the vertical speed
    alpha = 0.7  # Smoothing factor (0 < alpha < 1)
    v_speed = alpha * v_speed + (1 - alpha) * last_v_speed
    return v_speed
