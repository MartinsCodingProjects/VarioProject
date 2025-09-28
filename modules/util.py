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
            print(f"Sound {'enabled' if vario_state.sound_enabled else 'disabled'}")
            last_interrupt_time[0] = current_time
    
    # Attach interrupt to BOOT button (triggers on button press - falling edge)
    boot_button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_sound_interrupt)
    
    print("Sound toggle setup complete - Press BOOT button to toggle sound on/off")
    
    return boot_button, onboard_led
