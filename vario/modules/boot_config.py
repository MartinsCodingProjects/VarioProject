# boot_config.py - Boot configuration and constants

# =============================================================================
# BOOT CONFIGURATION
# =============================================================================

# Remote Debugging Configuration
ENABLE_REMOTE_DEBUG = False  # Set to False to disable WiFi/WebSocket and run standalone

# WiFi Configuration (only used if ENABLE_REMOTE_DEBUG = True)
WIFI_SSID = "JellyfishSSID"
WIFI_PASSWORD = "N0Fr33Wifi!"

# WebSocket Server Configuration (only used if ENABLE_REMOTE_DEBUG = True)
WEBSOCKET_HOST = "192.168.178.119"  # Replace with your PC's IP address
WEBSOCKET_PORT = 5474

# Boot Messages
BOOT_MESSAGES = {
    'remote_debug': "ESP32 Vario Boot Sequence (Remote Debug Mode)",
    'standalone': "ESP32 Vario Boot Sequence (Standalone Mode)",
    'separator': "=" * 50
}

# Boot Status Messages
STATUS_MESSAGES = {
    'remote_active': "Boot sequence completed - Remote debugging active - starting main application...",
    'remote_failed': "Boot sequence completed - Remote debugging failed, using console only - starting main application...",
    'standalone': "Boot sequence completed - Standalone mode - starting main application..."
}