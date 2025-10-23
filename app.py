import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

# Initialize SocketIO with eventlet async mode (avoid gevent/eventlet mix)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='eventlet'
)

# Store active rooms and users
rooms = {}

@app.route('/')
def index():
    print("Index route accessed")
    return render_template('index.html')

# Test route to verify Flask is working
@app.route('/test')
def test():
    return "Flask is working! ✓"

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'sid': request.sid, 'message': 'Connected successfully!'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    # Remove user from all rooms
    for room_code in list(rooms.keys()):
        if request.sid in rooms[room_code]['users']:
            rooms[room_code]['users'].remove(request.sid)
            emit('user_left', {'sid': request.sid}, room=room_code)
            if len(rooms[room_code]['users']) == 0:
                del rooms[room_code]
                print(f"Room {room_code} deleted (empty)")

@socketio.on('join_room')
def handle_join_room(data):
    print(f"Join room request: {data}")
    room_code = data['room_code']
    username = data['username']
    
    join_room(room_code)
    
    if room_code not in rooms:
        rooms[room_code] = {
            'users': [],
            'video_state': {
                'url': '',
                'time': 0,
                'playing': False
            }
        }
        print(f"Created new room: {room_code}")
    
    rooms[room_code]['users'].append(request.sid)
    
    # Send current room state to new user
    emit('room_joined', {
        'room_code': room_code,
        'user_count': len(rooms[room_code]['users']),
        'video_state': rooms[room_code]['video_state']
    })
    
    # Notify others in room
    emit('user_joined', {
        'username': username,
        'sid': request.sid,
        'user_count': len(rooms[room_code]['users'])
    }, room=room_code, skip_sid=request.sid)
    
    print(f'User {username} ({request.sid}) joined room {room_code}. Total users: {len(rooms[room_code]["users"])}')

@socketio.on('leave_room')
def handle_leave_room(data):
    room_code = data['room_code']
    leave_room(room_code)
    
    if room_code in rooms and request.sid in rooms[room_code]['users']:
        rooms[room_code]['users'].remove(request.sid)
        emit('user_left', {
            'sid': request.sid,
            'user_count': len(rooms[room_code]['users'])
        }, room=room_code)
        
        if len(rooms[room_code]['users']) == 0:
            del rooms[room_code]
            print(f"Room {room_code} deleted (empty)")

@socketio.on('chat_message')
def handle_chat_message(data):
    print(f"Chat message: {data}")
    room_code = data['room_code']
    username = data['username']
    message = data['message']
    
    emit('chat_message', {
        'username': username,
        'message': message,
        'timestamp': data.get('timestamp')
    }, room=room_code)

@socketio.on('video_play')
def handle_video_play(data):
    print(f"Video play: {data}")
    room_code = data['room_code']
    current_time = data.get('time', 0)
    
    if room_code in rooms:
        rooms[room_code]['video_state']['playing'] = True
        rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_play', {
        'time': current_time,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_pause')
def handle_video_pause(data):
    print(f"Video pause: {data}")
    room_code = data['room_code']
    current_time = data.get('time', 0)
    
    if room_code in rooms:
        rooms[room_code]['video_state']['playing'] = False
        rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_pause', {
        'time': current_time,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_seek')
def handle_video_seek(data):
    room_code = data['room_code']
    current_time = data['time']
    
    if room_code in rooms:
        rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_seek', {
        'time': current_time
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_load')
def handle_video_load(data):
    print(f"Video load: {data}")
    room_code = data['room_code']
    video_url = data['url']
    
    if room_code in rooms:
        rooms[room_code]['video_state']['url'] = video_url
        rooms[room_code]['video_state']['time'] = 0
        rooms[room_code]['video_state']['playing'] = False
    
    emit('video_load', {
        'url': video_url,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

# WebRTC Signaling
@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    print(f"WebRTC offer from {request.sid}")
    target_sid = data['target_sid']
    
    emit('webrtc_offer', {
        'offer': data['offer'],
        'sender_sid': request.sid
    }, room=target_sid)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    print(f"WebRTC answer from {request.sid}")
    target_sid = data['target_sid']
    
    emit('webrtc_answer', {
        'answer': data['answer'],
        'sender_sid': request.sid
    }, room=target_sid)

@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):
    target_sid = data['target_sid']
    
    emit('webrtc_ice_candidate', {
        'candidate': data['candidate'],
        'sender_sid': request.sid
    }, room=target_sid)

if __name__ == '__main__':
    print("=" * 50)
    print("Starting Watch Party Server...")
    print("Open your browser to: http://localhost:5000")
    print("=" * 50)
    # Development run (eventlet)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)