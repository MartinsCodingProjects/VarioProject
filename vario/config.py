# Config

# Measurement configuration
MEASUREMENT_FREQUENCY = 50
MEASUREMENT_INTERVAL = 1 / MEASUREMENT_FREQUENCY # seconds
INTERVAL_MS = int(MEASUREMENT_INTERVAL * 1000)  # Convert to milliseconds
BASE_PRESSURE = 1013.25  # hPa, sea level standard atmospheric pressure

# Filter and integration settings
MINIMAL_DELAY = 0.1  # seconds
INTEGRATION_INTERVAL = 12.0  # seconds for integrated vertical speed

# Audio configuration
POSTIVE_BEEP_THRESHOLD = 0.1
NEGATIVE_BEEP_THRESHOLD = -1
BUZZER_PIN = 4