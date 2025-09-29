from flask import Flask
from flask_socketio import SocketIO, emit
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vario_debug_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Vario Debug Console</title>
    <style>
        body { font-family: monospace; background-color: #1e1e1e; color: #ffffff; margin: 20px; }
        #messages { height: 80vh; overflow-y: scroll; border: 1px solid #555; padding: 10px; background-color: #2d2d2d; }
        .timestamp { color: #888; }
        .message { margin: 2px 0; }
    </style>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
</head>
<body>
    <h1>Vario Real-time Debug Console</h1>
    <div id="messages"></div>
    
    <script>
        const socket = io();
        const messages = document.getElementById('messages');
        
        socket.on('vario_log', function(data) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            const timestamp = new Date().toLocaleTimeString();
            messageDiv.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${data.message}`;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        });
        
        socket.on('connect', function() {
            console.log('Connected to debug server');
        });
    </script>
</body>
</html>'''

@socketio.on('connect')
def handle_connect():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] Client disconnected')

@socketio.on('vario_message')
def handle_vario_message(data):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = data.get('message', 'No message')
    print(f'[{timestamp}] Vario: {message}')
    # Broadcast to all connected clients (like the web interface)
    emit('vario_log', {'message': message, 'timestamp': timestamp}, broadcast=True)

if __name__ == '__main__':
    print("Starting Vario Debug Server...")
    print("WebSocket endpoint: ws://0.0.0.0:5000/ws")
    print("Web interface: http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)