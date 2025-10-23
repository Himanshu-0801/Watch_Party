import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    MAX_ROOMS = int(os.environ.get('MAX_ROOMS', 100))
    MAX_USERS_PER_ROOM = int(os.environ.get('MAX_USERS_PER_ROOM', 10))

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize SocketIO with eventlet async mode (avoid gevent/eventlet mix)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,    # Added timeout settings
    ping_interval=25,   # Added interval settings
    transports=['websocket', 'polling']  # Explicit transport options
)

# Instead of single rooms dict, split into two for better management
active_rooms = {}  # Tracks room membership
user_rooms = {}    # Tracks user metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/')
def index():
    logger.info("Index route accessed")
    return render_template('index.html')

# Test route to verify Flask is working
@app.route('/test')
def test():
    return "Flask is working! ✓"

@app.route('/health')
def health():
    return {'status': 'healthy', 'rooms': len(active_rooms), 'users': len(user_rooms)}, 200

@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')
    emit('connected', {'sid': request.sid, 'message': 'Connected successfully!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')
    # Remove user from all rooms
    for room_code in list(active_rooms.keys()):
        if request.sid in active_rooms[room_code]['users']:
            active_rooms[room_code]['users'].remove(request.sid)
            emit('user_left', {'sid': request.sid}, room=room_code)
            if len(active_rooms[room_code]['users']) == 0:
                del active_rooms[room_code]
                logger.info(f"Room {room_code} deleted (empty)")

@socketio.on('join_room')
def handle_join_room(data):
    try:
        room_code = data.get('room_code')
        username = data.get('username', 'Anonymous')
        
        if not room_code:
            raise ValueError("Room code is required")
            
        join_room(room_code)
        
        if room_code not in active_rooms:
            active_rooms[room_code] = {
                'users': [],
                'video_state': {
                    'url': '',
                    'time': 0,
                    'playing': False
                }
            }
            logger.info(f"Created new room: {room_code}")
        
        active_rooms[room_code]['users'].append(request.sid)
        
        # Send current room state to new user
        emit('room_joined', {
            'room_code': room_code,
            'user_count': len(active_rooms[room_code]['users']),
            'video_state': active_rooms[room_code]['video_state']
        })
        
        # Notify others in room
        emit('user_joined', {
            'username': username,
            'sid': request.sid,
            'user_count': len(active_rooms[room_code]['users'])
        }, room=room_code, skip_sid=request.sid)
        
        logger.info(f'User {username} ({request.sid}) joined room {room_code}. Total users: {len(active_rooms[room_code]["users"])}')
    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")
        emit('error', {'message': 'Failed to join room'})

@socketio.on('leave_room')
def handle_leave_room(data):
    room_code = data['room_code']
    leave_room(room_code)
    
    if room_code in active_rooms and request.sid in active_rooms[room_code]['users']:
        active_rooms[room_code]['users'].remove(request.sid)
        emit('user_left', {
            'sid': request.sid,
            'user_count': len(active_rooms[room_code]['users'])
        }, room=room_code)
        
        if len(active_rooms[room_code]['users']) == 0:
            del active_rooms[room_code]
            logger.info(f"Room {room_code} deleted (empty)")

@socketio.on('chat_message')
def handle_chat_message(data):
    logger.info(f"Chat message: {data}")
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
    logger.info(f"Video play: {data}")
    room_code = data['room_code']
    current_time = data.get('time', 0)
    
    if room_code in active_rooms:
        active_rooms[room_code]['video_state']['playing'] = True
        active_rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_play', {
        'time': current_time,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_pause')
def handle_video_pause(data):
    logger.info(f"Video pause: {data}")
    room_code = data['room_code']
    current_time = data.get('time', 0)
    
    if room_code in active_rooms:
        active_rooms[room_code]['video_state']['playing'] = False
        active_rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_pause', {
        'time': current_time,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_seek')
def handle_video_seek(data):
    room_code = data['room_code']
    current_time = data['time']
    
    if room_code in active_rooms:
        active_rooms[room_code]['video_state']['time'] = current_time
    
    emit('video_seek', {
        'time': current_time
    }, room=room_code, skip_sid=request.sid)

@socketio.on('video_load')
def handle_video_load(data):
    logger.info(f"Video load: {data}")
    room_code = data['room_code']
    video_url = data['url']
    
    if room_code in active_rooms:
        active_rooms[room_code]['video_state']['url'] = video_url
        active_rooms[room_code]['video_state']['time'] = 0
        active_rooms[room_code]['video_state']['playing'] = False
    
    emit('video_load', {
        'url': video_url,
        'username': data.get('username')
    }, room=room_code, skip_sid=request.sid)

# WebRTC Signaling
@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    logger.info(f"WebRTC offer from {request.sid}")
    target_sid = data['target_sid']
    
    emit('webrtc_offer', {
        'offer': data['offer'],
        'sender_sid': request.sid
    }, room=target_sid)

@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    logger.info(f"WebRTC answer from {request.sid}")
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
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=port, 
                 debug=False, 
                 allow_unsafe_werkzeug=True)