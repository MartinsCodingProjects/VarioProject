# network_manager.py - WiFi and WebSocket connection management

import network
import socket
import time
import ubinascii
import urandom

class NetworkManager:
    """Manages WiFi and WebSocket connections for the ESP32 Vario"""
    
    def __init__(self, wifi_ssid, wifi_password, websocket_host, websocket_port):
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        self.wlan = None
        self.websocket_sock = None
    
    def connect_wifi(self):
        """Connect to WiFi network with timeout and status reporting"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        if self.wlan.isconnected():
            print("Already connected to WiFi")
            return self.wlan
        
        print(f"Connecting to WiFi: {self.wifi_ssid}")
        self.wlan.connect(self.wifi_ssid, self.wifi_password)
        
        # Wait for connection with timeout
        timeout = 0
        while not self.wlan.isconnected() and timeout < 20:
            print(".", end="")
            time.sleep(1)
            timeout += 1
        
        if self.wlan.isconnected():
            config = self.wlan.ifconfig()
            print(f"\nWiFi connected!")
            print(f"IP: {config[0]}")
            print(f"Subnet: {config[1]}")
            print(f"Gateway: {config[2]}")
            print(f"DNS: {config[3]}")
            return self.wlan
        else:
            print("\nFailed to connect to WiFi")
            return None
    
    def _create_websocket_key(self):
        """Generate a random WebSocket key for handshake"""
        key = ubinascii.b2a_base64(bytes([urandom.getrandbits(8) for _ in range(16)])).decode().strip()
        return key
    
    def _websocket_handshake(self, sock, path="/"):
        """Perform WebSocket handshake with the server"""
        key = self._create_websocket_key()
        
        # Create handshake request
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.websocket_host}:{self.websocket_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        
        # Send handshake
        sock.send(request.encode())
        
        # Read response
        response = sock.recv(1024).decode()
        
        if "101 Switching Protocols" in response and "Upgrade: websocket" in response:
            print("WebSocket handshake successful!")
            return True
        else:
            print(f"WebSocket handshake failed: {response}")
            return False
    
    def setup_websocket(self):
        """Setup WebSocket connection after WiFi is established"""
        # Connect to WiFi first
        if not self.connect_wifi():
            print("Cannot proceed without WiFi connection")
            return None, None
        
        try:
            print(f"Connecting to WebSocket server: ws://{self.websocket_host}:{self.websocket_port}/")
            
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout
            sock.connect((self.websocket_host, self.websocket_port))
            
            # Perform WebSocket handshake
            if not self._websocket_handshake(sock):
                print("Failed to establish WebSocket connection")
                sock.close()
                return None, None
            
            print("WebSocket connected successfully!")
            self.websocket_sock = sock
            return sock, self.wlan
            
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            print("Please check:")
            print("1. PC WebSocket server is running")
            print("2. PC IP address is correct")
            print("3. Port 5474 is not blocked by firewall")
            return None, None
    
    def disconnect(self):
        """Clean disconnection of WebSocket and WiFi"""
        if self.websocket_sock:
            try:
                self.websocket_sock.close()
                print("WebSocket disconnected")
            except:
                pass
        
        if self.wlan:
            try:
                self.wlan.disconnect()
                self.wlan.active(False)
                print("WiFi disconnected")
            except:
                pass