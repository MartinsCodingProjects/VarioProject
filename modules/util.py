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
