#!/usr/bin/env python3
"""
Simple WebSocket client to test connection to the debug server
"""
import socket
import base64
import hashlib
import struct
import threading
import time

def create_websocket_key():
    """Generate a random WebSocket key"""
    import os
    return base64.b64encode(os.urandom(16)).decode()

def websocket_handshake(host, port, path="/"):
    """Perform WebSocket handshake"""
    key = create_websocket_key()
    
    # Create HTTP upgrade request
    request = f"""GET {path} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {key}\r
Sec-WebSocket-Version: 13\r
\r
"""
    
    try:
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        # Send handshake
        sock.send(request.encode())
        
        # Receive response
        response = sock.recv(1024).decode()
        print("Server response:")
        print(response)
        
        if "101 Switching Protocols" in response:
            print("\n✅ WebSocket handshake successful!")
            
            # Send a test message
            test_message = "Hello from test client!"
            frame = create_websocket_frame(test_message)
            sock.send(frame)
            print(f"Sent test message: {test_message}")
            
            # Try to receive response
            try:
                response_data = sock.recv(1024)
                if response_data:
                    message = parse_websocket_frame(response_data)
                    if message:
                        print(f"Received response: {message}")
            except:
                pass
            
            return True
        else:
            print("\n❌ WebSocket handshake failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        sock.close()

def create_websocket_frame(message):
    """Create WebSocket frame for sending message"""
    message_bytes = message.encode('utf-8')
    frame = bytearray()
    frame.append(0x81)  # Text frame, final fragment
    
    payload_length = len(message_bytes)
    if payload_length < 126:
        frame.append(0x80 | payload_length)  # Masked bit + length
    else:
        frame.append(0xFE)  # 126 + masked bit
        frame.extend(struct.pack(">H", payload_length))
    
    # Add masking key (4 bytes)
    import os
    mask = os.urandom(4)
    frame.extend(mask)
    
    # Add masked payload
    masked_payload = bytes(message_bytes[i] ^ mask[i % 4] for i in range(len(message_bytes)))
    frame.extend(masked_payload)
    
    return bytes(frame)

def parse_websocket_frame(data):
    """Parse incoming WebSocket frame"""
    if len(data) < 2:
        return None
    
    byte1, byte2 = data[0], data[1]
    masked = byte2 & 0x80
    payload_length = byte2 & 0x7F
    
    header_length = 2
    if payload_length == 126:
        header_length = 4
    elif payload_length == 127:
        header_length = 10
    
    if masked:
        header_length += 4
    
    if len(data) < header_length:
        return None
    
    if payload_length == 126:
        payload_length = struct.unpack(">H", data[2:4])[0]
    elif payload_length == 127:
        payload_length = struct.unpack(">Q", data[2:10])[0]
    
    if len(data) < header_length + payload_length:
        return None
    
    payload_data = data[header_length:header_length + payload_length]
    
    if masked:
        mask = data[header_length - 4:header_length]
        payload_data = bytes(payload_data[i] ^ mask[i % 4] for i in range(len(payload_data)))
    
    return payload_data.decode('utf-8', errors='ignore')

if __name__ == "__main__":
    host = "192.168.178.119"
    port = 5474
    
    print(f"Testing WebSocket connection to ws://{host}:{port}")
    print("-" * 50)
    
    success = websocket_handshake(host, port)
    
    if success:
        print("🎉 WebSocket connection test passed!")
        print("The ESP32 should be able to connect successfully.")
    else:
        print("❌ WebSocket connection test failed!")
        print("Check if the server is running and accessible.")