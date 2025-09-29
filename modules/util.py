import urequests

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


def setup_sound_toggle(vario_state):
    """
    Setup external interrupt for BOOT button to toggle sound on/off.
    Also initializes onboard LED to show sound status.
    
    Args:
        vario_state: VarioState object containing sound_enabled flag
        
    Returns:
        tuple: (boot_button, onboard_led) for reference if needed
    """
    from machine import Pin
    import time
    
    # Initialize BOOT button (GPIO 0) and onboard LED (GPIO 2)
    boot_button = Pin(0, Pin.IN, Pin.PULL_UP)  # BOOT button is active-low
    onboard_led = Pin(2, Pin.OUT)  # Onboard LED
    
    
    # Debounce timer
    last_interrupt_time = [0]  # Use list to allow modification in nested function
    
    def toggle_sound_interrupt(pin):
        """
        Interrupt callback to toggle vario_state.sound_enabled and update LED.
        """
        current_time = time.ticks_ms()
        
        # Debounce: Ignore interrupts that occur within 300ms of the last one
        if time.ticks_diff(current_time, last_interrupt_time[0]) > 300:
            vario_state.sound_enabled = not vario_state.sound_enabled
            onboard_led.value(vario_state.sound_enabled)
            vario_state.log(f"Sound {'enabled' if vario_state.sound_enabled else 'disabled'}")
            last_interrupt_time[0] = current_time
    
    # Attach interrupt to BOOT button (triggers on button press - falling edge)
    boot_button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_sound_interrupt)

    vario_state.log("Sound toggle setup complete - Press BOOT button to toggle sound on/off")

    return boot_button, onboard_led

def send_to_websocket(endpoint, message):
    """
    Send a message via the existing WebSocket connection.
    Args:
        endpoint (str): Not used, kept for compatibility
        message (str): The message to send.
    """
    try:
        import boot  # Import boot to access ws_connection
        import urandom as random
        
        if boot.ws_connection is None:
            return  # No connection available, skip silently
        
        # Send the message (simple text frame)
        message_bytes = message.encode('utf-8')
        frame = bytearray([0x81])  # Text frame, final fragment
        
        if len(message_bytes) < 126:
            frame.append(0x80 | len(message_bytes))  # Mask bit + length
        else:
            frame.append(0x80 | 126)  # Mask bit + extended length indicator
            frame.extend(len(message_bytes).to_bytes(2, 'big'))
        
        # Add masking key (4 bytes)
        mask = bytes([random.getrandbits(8) for _ in range(4)])
        frame.extend(mask)
        
        # Mask the payload
        masked_payload = bytearray()
        for i, byte in enumerate(message_bytes):
            masked_payload.append(byte ^ mask[i % 4])
        
        frame.extend(masked_payload)
        boot.ws_connection.send(frame)
        
    except Exception as e:
        # Silently fail to avoid disrupting the main program
        pass