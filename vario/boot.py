# boot.py - ESP32 Vario System Boot Sequence
# Handles system initialization, networking, and hardware setup

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
    """Initialize the core VarioState object with system parameters"""
    print("Initializing VarioState...")
    
    # Create VarioState with configured parameters
    vario_state = VarioState(
        base_pressure=BASE_PRESSURE,
        measurement_frequency=MEASUREMENT_FREQUENCY,
        integration_interval=INTEGRATION_INTERVAL
    )
    
    print("VarioState initialized successfully")
    return vario_state


def setup_remote_debugging(vario_state):
    """Setup WiFi and WebSocket connection for remote debugging"""
    print("Remote debugging enabled - connecting to WiFi and WebSocket...")
    
    # Create network manager
    network_mgr = NetworkManager(
        wifi_ssid=WIFI_SSID,
        wifi_password=WIFI_PASSWORD,
        websocket_host=WEBSOCKET_HOST,
        websocket_port=WEBSOCKET_PORT
    )
    
    # Attempt WebSocket connection
    websocket_sock, wlan = network_mgr.setup_websocket()
    
    if websocket_sock:
        # Configure VarioState for WebSocket logging
        vario_state.websocket_sock = websocket_sock
        vario_state.websocket_enabled = True
        
        # Send initial boot message
        vario_state.log("ESP32 Vario system booted - WebSocket logging enabled")
        vario_state.log(f"Network IP: {wlan.ifconfig()[0]}")
        
        return True, network_mgr
    else:
        print("WebSocket connection failed - using console logging only")
        vario_state.websocket_enabled = False
        return False, None


def setup_standalone_mode(vario_state):
    """Setup vario for standalone operation (no networking)"""
    print("Remote debugging disabled - running in standalone mode")
    
    # Disable WebSocket logging
    vario_state.websocket_enabled = False
    vario_state.websocket_sock = None
    
    # Log to console that we're in standalone mode
    vario_state.log("ESP32 Vario system booted - Standalone mode (no remote logging)")
    
    return True, None


def main_boot_sequence():
    """Main boot sequence orchestrator"""
    
    # =================================================================
    # BOOT HEADER
    # =================================================================
    print(BOOT_MESSAGES['separator'])
    if ENABLE_REMOTE_DEBUG:
        print(BOOT_MESSAGES['remote_debug'])
    else:
        print(BOOT_MESSAGES['standalone'])
    print(BOOT_MESSAGES['separator'])
    
    # =================================================================
    # STEP 1: Initialize Core VarioState
    # =================================================================
    vario_state = initialize_vario_state()
    global_state.vario_state = vario_state
    
    # =================================================================
    # STEP 2: Setup Networking (Conditional)
    # =================================================================
    network_mgr = None
    if ENABLE_REMOTE_DEBUG:
        remote_debug_success, network_mgr = setup_remote_debugging(vario_state)
    else:
        remote_debug_success, network_mgr = setup_standalone_mode(vario_state)
    
    # =================================================================
    # STEP 3: Initialize Hardware Components
    # =================================================================
    hardware_mgr = HardwareManager(vario_state, BUZZER_PIN)
    hardware_success = hardware_mgr.initialize_all_hardware()
    
    # Store hardware info in global state for main.py access
    sensor_info = hardware_mgr.get_sensor_info()
    global_state.sensor_object = sensor_info['sensor_object']
    global_state.audio_system = sensor_info['audio_system']
    global_state.hardware_initialized = sensor_info['initialized']
    
    # =================================================================
    # STEP 4: Final Boot Status
    # =================================================================
    if ENABLE_REMOTE_DEBUG:
        if remote_debug_success:
            print(STATUS_MESSAGES['remote_active'])
        else:
            print(STATUS_MESSAGES['remote_failed'])
    else:
        print(STATUS_MESSAGES['standalone'])
    
    # Final memory cleanup
    gc.collect()
    
    return hardware_success and (remote_debug_success or not ENABLE_REMOTE_DEBUG)


# =============================================================================
# BOOT EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Execute main boot sequence
    boot_success = main_boot_sequence()
    
    if boot_success:
        print("🎉 Boot sequence completed successfully!")
    else:
        print("⚠️ Boot sequence completed with warnings - check logs above")
        
    print("Starting main application...")
    
    # Import and run main application
    try:
        import main
    except ImportError as e:
        print(f"Failed to import main application: {e}")
    except Exception as e:
        print(f"Error in main application: {e}")



