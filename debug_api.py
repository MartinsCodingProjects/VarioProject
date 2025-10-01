#!/usr/bin/env python3
"""
Simple WebSocket server for ESP32 debugging
"""
import socket
import hashlib
import base64
import struct
import threading
import datetime

def websocket_key_hash(key):
    """Generate WebSocket accept key"""
    magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    return base64.b64encode(hashlib.sha1((key + magic_string).encode()).digest()).decode()

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

def create_websocket_frame(message):
    """Create WebSocket frame for sending message"""
    message_bytes = message.encode('utf-8')
    frame = bytearray()
    frame.append(0x81)  # Text frame, final fragment
    
    payload_length = len(message_bytes)
    if payload_length < 126:
        frame.append(payload_length)
    elif payload_length < 65536:
        frame.append(126)
        frame.extend(struct.pack(">H", payload_length))
    else:
        frame.append(127)
        frame.extend(struct.pack(">Q", payload_length))
    
    frame.extend(message_bytes)
    return bytes(frame)

def handle_client(client_socket, address):
    """Handle WebSocket client connection"""
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Client connected from {address}")
    
    try:
        # Read HTTP upgrade request
        request = client_socket.recv(1024).decode()
        lines = request.split('\n')
        
        # Find WebSocket key
        websocket_key = None
        for line in lines:
            if line.startswith('Sec-WebSocket-Key:'):
                websocket_key = line.split(':')[1].strip()
                break
        
        if not websocket_key:
            print("No WebSocket key found in request")
            client_socket.close()
            return
        
        # Send WebSocket handshake response
        accept_key = websocket_key_hash(websocket_key)
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n"
            "\r\n"
        )
        
        client_socket.send(response.encode())
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] WebSocket handshake completed")
        
        # Send welcome message
        welcome_msg = create_websocket_frame("WebSocket connection established!")
        client_socket.send(welcome_msg)
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                message = parse_websocket_frame(data)
                if message:
                    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] ESP32: {message}")
                    
                    # Echo message back
                    echo_msg = create_websocket_frame(f"Received: {message}")
                    client_socket.send(echo_msg)
                    
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
                
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Client {address} disconnected")

def start_websocket_server(host='0.0.0.0', port=5474):
    """Start the WebSocket server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Simple WebSocket server listening on ws://{host}:{port}")
        print("Waiting for ESP32 connections...")
        
        while True:
            client_socket, address = server_socket.accept()
            # Handle each client in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Bind to all interfaces so ESP32 can connect from any network
    start_websocket_server('0.0.0.0', 5474)