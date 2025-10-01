def display_v_speed(v_speed, vario_state):
    """
    Display the current vertical speed
    used for visual feedback and audio cues (later on)
    """
    vario_state.log(f"Vertical Speed: {v_speed:.2f} m/s")

def display_integrated_v_speed(integrated_v_speed, vario_state):
    """
    Display the integrated vertical speed
    """
    vario_state.log(f"Integrated Vertical Speed: {integrated_v_speed:.2f} m/s")
