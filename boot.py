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

# Global WebSocket connection
ws_connection = None

def setup_websocket_connection(debug_server):
    global ws_connection
    import usocket as socket
    import uhashlib as hashlib
    import ubinascii as binascii
    import urandom as random
    
    try:
        # Wait for Wi-Fi connection
        while not wifi_connected:
            time.sleep(0.1)
        
        print("Setting up WebSocket connection...")
        host = debug_server
        port = 5000
        path = "ws"
        
        # Create socket connection
        s = socket.socket()
        s.connect((host, port))
        
        # Generate WebSocket key
        key = binascii.b2a_base64(bytes([random.getrandbits(8) for _ in range(16)]))[:-1]
        
        # Send WebSocket handshake
        handshake = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key.decode()}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        s.send(handshake.encode())
        
        # Read handshake response
        response = s.recv(1024)
        if b"101 Switching Protocols" not in response:
            raise Exception("WebSocket handshake failed")
        
        ws_connection = s
        print("WebSocket connection established!")
        
    except Exception as e:
        print(f"Failed to setup WebSocket: {e}")
        ws_connection = None

# Connect to your Wi-Fi network
start_new_thread(connect_to_wifi, ("JellyfishSSID", "N0Fr33Wifi!"))

# Setup WebSocket connection after Wi-Fi (in separate thread)
start_new_thread(setup_websocket_connection, ("192.168.178.119",))

# Main script can continue running here
print("Main script is running...")