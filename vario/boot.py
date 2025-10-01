import network
import time
import usocket as socket
import uhashlib as hashlib
import ubinascii as binascii
import urandom as random

# Global variables
wifi_connected = False
ws_connection = None

def connect_to_wifi(ssid, password):
    """
    Connect to Wi-Fi synchronously.
    """
    global wifi_connected
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(0.1)

    wifi_connected = True
    print("Connected to Wi-Fi!")
    print("IP Address:", wlan.ifconfig()[0])

def setup_websocket_connection(host, port=5474):
    """
    Setup WebSocket connection to debug server.
    """
    global ws_connection
    
    try:
        print(f"Connecting to WebSocket server at {host}:{port}")
        
        # First test basic TCP connectivity
        print("Testing basic TCP connection...")
        s = socket.socket()
        s.settimeout(10)  # 10 second timeout
        
        print(f"Attempting to connect to {host}:{port}...")
        s.connect((host, port))
        print("✅ TCP connection successful!")
        
        # Generate WebSocket key
        key_bytes = bytes([random.getrandbits(8) for _ in range(16)])
        key = binascii.b2a_base64(key_bytes)[:-1]  # Remove trailing newline
        
        print("Sending WebSocket handshake...")
        
        # Send WebSocket handshake
        handshake = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key.decode()}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        s.send(handshake.encode())
        print("Handshake sent, waiting for response...")
        
        # Read handshake response with timeout
        s.settimeout(5)
        response = s.recv(1024)
        response_str = response.decode()
        
        print("Server response:")
        print(response_str[:200] + "..." if len(response_str) > 200 else response_str)
        
        if b"101 Switching Protocols" in response:
            ws_connection = s
            print("✅ WebSocket handshake successful!")
            
            # Send initial message
            send_websocket_message("ESP32 connected and ready!")
            
            return True
        else:
            print("❌ WebSocket handshake failed!")
            s.close()
            return False
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print(f"Error type: {type(e)}")
        try:
            s.close()
        except:
            pass
        return False

def send_websocket_message(message):
    """
    Send message through WebSocket connection
    """
    global ws_connection
    
    if not ws_connection:
        print("No WebSocket connection available")
        return False
    
    try:
        # Create WebSocket frame (simple text frame)
        message_bytes = message.encode('utf-8')
        frame = bytearray()
        frame.append(0x81)  # Text frame, final fragment
        
        # Add payload length
        payload_length = len(message_bytes)
        if payload_length < 126:
            frame.append(0x80 | payload_length)  # Masked bit + length
        else:
            print("Message too long for simple implementation")
            return False
        
        # Add masking key (4 bytes)
        mask = bytes([random.getrandbits(8) for _ in range(4)])
        frame.extend(mask)
        
        # Add masked payload
        masked_payload = bytes(message_bytes[i] ^ mask[i % 4] for i in range(len(message_bytes)))
        frame.extend(masked_payload)
        
        ws_connection.send(bytes(frame))
        print(f"Sent: {message}")
        return True
        
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False

# Main execution
if __name__ == "__main__":
    print("ESP32 Boot Script Starting...")
    
    # Connect to Wi-Fi
    connect_to_wifi("JellyfishSSID", "N0Fr33Wifi!")
    
    # Setup WebSocket connection after Wi-Fi is connected
    if wifi_connected:
        success = setup_websocket_connection("192.168.178.119", 5474)
        
        if success:
            print("🎉 Boot script completed successfully!")
            # You can add more debug messages here
            time.sleep(2)
            send_websocket_message("Boot sequence completed")
        else:
            print("❌ Failed to establish WebSocket connection")
    else:
        print("❌ Wi-Fi connection failed")
    
    print("Main script is running...")