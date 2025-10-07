# boot.py - ESP32 Vario System Boot Sequence
# Handles ALL initialization - networking, sensors, audio
# main.py should only run if boot.py succeeds

import time
import gc
import modules.global_state as global_state

# Import configuration and managers
from modules.boot_config import (
    ENABLE_REMOTE_DEBUG, 
    WIFI_SSID, 
    WIFI_PASSWORD,
    WEBSOCKET_HOST, 
    WEBSOCKET_PORT,
    BOOT_MESSAGES,
    STATUS_MESSAGES
)
from modules.network_manager import NetworkManager
from modules.hardware_manager import HardwareManager
from modules.variostate import VarioState

# Import system configuration
from config import (
    BASE_PRESSURE,
    MEASUREMENT_FREQUENCY,
    INTEGRATION_INTERVAL,
    BUZZER_PIN
)


def initialize_vario_state():
    """
    Step 1: Create the main vario state object
    This holds all measurement data and system status
    """
    print("📊 STEP 1: Initializing VarioState...")
    
    vario_state = VarioState(
        base_pressure=BASE_PRESSURE,
        measurement_frequency=MEASUREMENT_FREQUENCY,
        integration_interval=INTEGRATION_INTERVAL
    )
    
    print("✓ VarioState created successfully")
    return vario_state


def setup_networking(vario_state):
    """
    Step 2: Setup WiFi and WebSocket (if remote debugging enabled)
    Returns: (success, network_manager)
    """
    if not ENABLE_REMOTE_DEBUG:
        print("📡 STEP 2: Remote debugging disabled - running standalone")
        vario_state.websocket_enabled = False
        vario_state.log("ESP32 Vario booted in standalone mode")
        return True, None
    
    print("📡 STEP 2: Setting up remote debugging...")
    
    network_mgr = NetworkManager(
        wifi_ssid=WIFI_SSID,
        wifi_password=WIFI_PASSWORD,
        websocket_host=WEBSOCKET_HOST,
        websocket_port=WEBSOCKET_PORT
    )
    
    websocket_sock, wlan = network_mgr.setup_websocket()
    
    if websocket_sock:
        vario_state.websocket_sock = websocket_sock
        vario_state.websocket_enabled = True
        vario_state.log("ESP32 Vario booted with remote debugging")
        vario_state.log(f"Network IP: {wlan.ifconfig()[0]}")
        print("✓ Remote debugging active")
        return True, network_mgr
    else:
        print("⚠️ Remote debugging failed - continuing standalone")
        vario_state.websocket_enabled = False
        return True, None  # Not fatal - we can run without it


def setup_hardware(vario_state):
    """
    Step 3: Initialize all hardware (sensors, audio)
    This is CRITICAL - vario cannot run without working sensors
    Returns: (success, hardware_info)
    """
    print("🔧 STEP 3: Initializing hardware...")
    
    # Create hardware manager
    hardware_mgr = HardwareManager(vario_state, BUZZER_PIN)
    
    # Initialize all hardware
    success = hardware_mgr.initialize_all_hardware()
    hardware_info = hardware_mgr.get_sensor_info()
    
    # Check critical components
    ms5611_ok = hardware_info['sensor_object'] and hardware_info['sensor_object'].is_initialized
    bmi160_ok = hardware_info['bmi160_object'] and hardware_info['bmi160_object'].is_initialized
    audio_ok = hardware_info['audio_system'] and hardware_info['audio_system'].is_initialized
    
    # Log hardware status
    print(f"   MS5611 Barometer: {'✓ OK' if ms5611_ok else '✗ FAILED'}")
    print(f"   BMI160 Motion:    {'✓ OK' if bmi160_ok else '⚠️ Optional'}")
    print(f"   Audio System:     {'✓ OK' if audio_ok else '⚠️ Optional'}")
    
    if not ms5611_ok:
        print("🚨 CRITICAL: MS5611 barometer is required for vario operation!")
        return False, hardware_info
    
    print("✓ Hardware initialization complete")
    return True, hardware_info


def store_in_global_state(vario_state, hardware_info, network_mgr):
    """
    Step 4: Store all initialized objects in global state for main.py
    This is how main.py gets access to all the hardware
    """
    print("💾 STEP 4: Storing objects in global state...")
    
    # Store core objects
    global_state.vario_state = vario_state
    global_state.ms5611_object = hardware_info['sensor_object']
    global_state.bmi160_object = hardware_info['bmi160_object']
    global_state.audio_system = hardware_info['audio_system']
    global_state.hardware_initialized = hardware_info['initialized']
    
    print("✓ All objects stored in global state")


def main_boot_sequence():
    """
    Complete boot sequence - handles everything needed to run the vario
    
    If this function returns True, main.py can safely start
    If this function returns False, system cannot operate
    """
    
    print(BOOT_MESSAGES['separator'])
    if ENABLE_REMOTE_DEBUG:
        print(BOOT_MESSAGES['remote_debug'])
    else:
        print(BOOT_MESSAGES['standalone'])
    print(BOOT_MESSAGES['separator'])
    
    try:
        # Step 1: Core system state
        vario_state = initialize_vario_state()
        
        # Step 2: Networking (optional)
        network_success, network_mgr = setup_networking(vario_state)
        
        # Step 3: Hardware (critical)
        hardware_success, hardware_info = setup_hardware(vario_state)
        
        if not hardware_success:
            print("🚨 BOOT FAILED: Critical hardware not available")
            return False
        
        # Step 4: Make everything available to main.py
        store_in_global_state(vario_state, hardware_info, network_mgr)
        
        # Final cleanup
        gc.collect()
        
        print("🎉 BOOT SUCCESS: System ready for operation!")
        return True
        
    except Exception as e:
        print(f"🚨 BOOT FAILED: Unexpected error: {e}")
        return False


# =============================================================================
# BOOT EXECUTION
# =============================================================================
if __name__ == "__main__":
    boot_success = main_boot_sequence()
    
    if boot_success:
        print("Starting main vario application...")
        try:
            import main
        except Exception as e:
            print(f"🚨 MAIN APPLICATION FAILED: {e}")
    else:
        print("🚨 CANNOT START: Boot sequence failed")
        print("Check wiring and configuration, then reset ESP32")



