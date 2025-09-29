class VarioState:
    def __init__(self, base_pressure, measurement_frequency, integration_interval):
        self.v_speed = 0.00  # Vertical speed (m/s)
        self.last_v_speed = 0.00
        self.integrated_v_speed = 0.00
        self.last_integrated_v_speed = 0.00
        self.estimated_local_pressure = base_pressure
        self.altitude_log = [0] * int(integration_interval * measurement_frequency)
        self.measurement_count = 0
        self.last_measurement_time = 0
        self.buzzer_pwm = None  # PWM object for buzzer, initialized in init_buzzer(), passed to audio functions
        self.boot_button = None  # GPIO Pin object for BOOT button, initialized in main.py
        self.onboard_led = None  # GPIO Pin object for onboard LED, initialized in main.py
        self.sound_enabled = False  # Sound state, toggled by BOOT button
        self.debug_server = "192.168.178.119"  # Placeholder for debug server, if implemented

    def log(self, message):
        """
        Log a message to the terminal and send it via WebSocket.
        """
        print(message)  # Print to the terminal
        try:
            from modules.util import send_to_websocket  # Import the send_to_websocket function
            send_to_websocket(f"ws://{self.debug_server}:5000/ws", message)  # Send via WebSocket
        except Exception as e:
            print(f"Failed to send log via WebSocket: {e}")
