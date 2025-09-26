import time
import gc

from modules.calc_v_speed import get_v_speed
from modules.util import convert_to_altitude
from modules.frontend import display_v_speed, display_integrated_v_speed
from modules.sensor import init_spi, ms5611_reset, ms5611_read_prom, ms5611_pressure_measurement

## config
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

# Initialize hardware
spi, cs = init_spi()
ms5611_reset(spi, cs)
print("MS5611 sensor initialized")

# Read sensor calibration data (factory programmed values)
print("Reading calibration data...")
c1 = ms5611_read_prom(spi, cs, 0xA2)  # Pressure sensitivity
c2 = ms5611_read_prom(spi, cs, 0xA4)  # Pressure offset
c3 = ms5611_read_prom(spi, cs, 0xA6)  # Temperature coefficient of pressure sensitivity
c4 = ms5611_read_prom(spi, cs, 0xA8)  # Temperature coefficient of pressure offset
c5 = ms5611_read_prom(spi, cs, 0xAA)  # Reference temperature
c6 = ms5611_read_prom(spi, cs, 0xAC)  # Temperature coefficient of temperature

print(f"Calibration: C1={c1}, C2={c2}, C3={c3}, C4={c4}, C5={c5}, C6={c6}")
print("Vario ready - no calibration needed!")
print("-" * 50)


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
                measured_pressure = ms5611_pressure_measurement(spi, cs)
                altitude = convert_to_altitude(measured_pressure, estimated_local_pressure)

                # add new measurements to logs and drop oldest entry
                altitude_log.append(altitude)
                altitude_log.pop(0)

                v_speed = round(get_v_speed(altitude_log, last_v_speed, MEASUREMENT_FREQUENCY, MINIMAL_DELAY), 2)
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