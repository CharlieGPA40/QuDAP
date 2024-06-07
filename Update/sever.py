from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return "Server is running."

@app.route('/send_update', methods=['POST'])
def send_update():
    message = request.json.get('message', 'Default update message')
    socketio.emit('update', {'message': message})
    return 'Update sent!', 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
