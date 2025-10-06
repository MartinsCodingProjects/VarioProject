class VarioState:
    def __init__(self, base_pressure, measurement_frequency, integration_interval):
        self.turned_on = False  # Vario state
        self.v_speed = 0.00  # Vertical speed (m/s)
        self.last_v_speed = 0.00
        self.integrated_v_speed = 0.00
        self.last_integrated_v_speed = 0.00
        self.estimated_local_pressure = base_pressure
        self.altitude_log = [0] * int(integration_interval * measurement_frequency)
        self.measurement_count = 0
        self.last_measurement_time = 0
        self.boot_button = None  # GPIO Pin object for BOOT button, initialized in main.py
        self.onboard_led = None  # GPIO Pin object for onboard LED, initialized in main.py
        self.sound_enabled = False  # Sound state, toggled by BOOT button
        
        # WebSocket logging (initialized in boot.py)
        self.websocket_sock = None
        self.websocket_enabled = False

    def log(self, message):
        """
        Enhanced logging method that supports both console and WebSocket
        """
        import time
        timestamp = time.ticks_ms()
        formatted_msg = f"[{timestamp}ms] {message}"
        
        # Always print to console
        print(formatted_msg)
        
        # Send to WebSocket if available
        if self.websocket_enabled and self.websocket_sock:
            try:
                self._send_websocket_frame(formatted_msg)
            except Exception as e:
                print(f"WebSocket logging failed: {e}")
                self.websocket_enabled = False  # Disable on error
    
    def _send_websocket_frame(self, message):
        """Send WebSocket frame (copied from boot.py)"""
        try:
            message_bytes = message.encode('utf-8')
            message_length = len(message_bytes)
            
            # Create frame header
            frame = bytearray()
            frame.append(0x81)  # FIN=1, opcode=1 (text)
            
            # Add payload length
            if message_length < 126:
                frame.append(message_length | 0x80)  # MASK=1
            elif message_length < 65536:
                frame.append(126 | 0x80)  # MASK=1
                frame.extend(message_length.to_bytes(2, 'big'))
            else:
                frame.append(127 | 0x80)  # MASK=1
                frame.extend(message_length.to_bytes(8, 'big'))
            
            # Add masking key
            mask_key = bytes([0x12, 0x34, 0x56, 0x78])
            frame.extend(mask_key)
            
            # Mask the payload
            masked_payload = bytearray()
            for i, byte in enumerate(message_bytes):
                masked_payload.append(byte ^ mask_key[i % 4])
            
            frame.extend(masked_payload)
            
            # Send frame
            self.websocket_sock.send(frame)
            return True
            
        except Exception as e:
            print(f"Error sending WebSocket frame: {e}")
            return False
