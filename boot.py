import network
import time
from _thread import start_new_thread

# Global variable to track Wi-Fi connection status
wifi_connected = False

def connect_to_wifi(ssid, password):
    global wifi_connected
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(0.1)  # Wait for connection

    wifi_connected = True
    print("Connected to Wi-Fi!")
    print("IP Address:", wlan.ifconfig()[0])

# Connect to your Wi-Fi network
start_new_thread(connect_to_wifi, ("JellyfishSSID", "N0Fr33Wifi!"))
# Main script can continue running here
print("Main script is running...")