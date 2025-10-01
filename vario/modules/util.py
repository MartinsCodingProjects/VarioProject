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


def setup_toggle_button(vario_state):
    """
    Setup external interrupt for BOOT button to toggle the main loop on/off.
    Also toggles sound_enabled and onboard LED state.

    Args:
        vario_state: VarioState object containing turned_on and sound_enabled flags

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

    def toggle_main_loop_interrupt(pin):
        """
        Interrupt callback to toggle vario_state.turned_on, vario_state.sound_enabled, and onboard LED.
        """
        current_time = time.ticks_ms()

        # Debounce: Ignore interrupts that occur within 300ms of the last one
        if time.ticks_diff(current_time, last_interrupt_time[0]) > 300:
            # Toggle main loop state
            vario_state.turned_on = not vario_state.turned_on

            # Toggle sound state
            vario_state.sound_enabled = not vario_state.sound_enabled

            # Toggle onboard LED state
            onboard_led.value(not onboard_led.value())

            # Log the changes
            vario_state.log(f"Vario {'started' if vario_state.turned_on else 'stopped'}")
            vario_state.log(f"Sound {'enabled' if vario_state.sound_enabled else 'disabled'}")

            # Update last interrupt time
            last_interrupt_time[0] = current_time

    # Attach interrupt to BOOT button (triggers on button press - falling edge)
    boot_button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_main_loop_interrupt)

    vario_state.log("Toggle button setup complete - Press BOOT button to start/stop the vario and toggle sound")

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