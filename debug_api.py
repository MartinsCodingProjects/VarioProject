#!/usr/bin/env python3
"""
Minimalistic WebSocket server for ESP32 remote debugging
Runs on port 5474 and prints messages from connected ESP32 devices
"""

import asyncio
import websockets
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store connected clients
connected_clients = set()

async def handle_client(websocket, path):
    """Handle incoming WebSocket connections"""
    client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"New client connected: {client_addr}")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] ESP32 ({client_addr}): {message}")
            
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_addr}")
    except Exception as e:
        logger.error(f"Error handling client {client_addr}: {e}")
    finally:
        connected_clients.discard(websocket)

async def main():
    """Start the WebSocket server"""
    host = "0.0.0.0"  # Listen on all interfaces
    port = 5474
    
    print(f"Starting WebSocket server on {host}:{port}")
    print("Waiting for ESP32 connections...")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        async with websockets.serve(handle_client, host, port):
            # Keep the server running
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())