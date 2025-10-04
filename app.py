from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from functools import wraps
import json
import random
import string

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading')

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/chat_app')
client = MongoClient(mongo_uri)
db = client.chat_app

# Collections
users_collection = db.users
rooms_collection = db.chat_rooms
messages_collection = db.messages
sessions_collection = db.user_sessions
private_messages_collection = db.private_messages

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
JWT_ALGORITHM = 'HS256'

# Store active users and their socket IDs
active_users = {}

# Utility functions
def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Check if a password matches its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_room_id():
    """Generate a unique 8-character alphanumeric room ID for private rooms"""
    characters = string.ascii_uppercase + string.digits
    while True:
        room_id = ''.join(random.choice(characters) for _ in range(8))
        # Check if room_id already exists
        if not rooms_collection.find_one({'room_id': room_id}):
            return room_id

def generate_token(user_id):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid'}), 401
        
        try:
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if not user:
                return jsonify({'error': 'User not found'}), 401
        except InvalidId:
            return jsonify({'error': 'Invalid user ID'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def socketio_token_required(f):
    """Decorator for SocketIO events to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_data = session.get('auth_data')
        if not auth_data or not auth_data.get('user_id'):
            emit('error', {'message': 'Authentication required'})
            return
        
        try:
            user = users_collection.find_one({'_id': ObjectId(auth_data['user_id'])})
            if not user:
                emit('error', {'message': 'User not found'})
                return
        except InvalidId:
            emit('error', {'message': 'Invalid user ID'})
            return
        
        return f(user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        display_name = data.get('display_name', username)
        
        # Check if user already exists
        if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Create new user
        user_doc = {
            'username': username,
            'email': email,
            'password_hash': hash_password(password),
            'display_name': display_name,
            'avatar_url': data.get('avatar_url', ''),
            'is_online': False,
            'last_seen': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_doc)
        user_id = result.inserted_id
        
        # Generate token
        token = generate_token(user_id)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': str(user_id),
                'username': username,
                'email': email,
                'display_name': display_name
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user
        user = users_collection.find_one({'username': username})
        if not user or not check_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Update user status
        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'is_online': True,
                    'last_seen': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Generate token
        token = generate_token(user['_id'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'display_name': user['display_name'],
                'avatar_url': user.get('avatar_url', '')
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@token_required
def logout():
    """User logout endpoint"""
    try:
        user = request.current_user
        
        # Update user status
        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'is_online': False,
                    'last_seen': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Logout successful'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile"""
    try:
        user = request.current_user
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'display_name': user['display_name'],
                'avatar_url': user.get('avatar_url', ''),
                'is_online': user['is_online'],
                'last_seen': user['last_seen'].isoformat(),
                'created_at': user['created_at'].isoformat()
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms', methods=['GET'])
@token_required
def get_rooms():
    """Get all accessible rooms (public + user's private rooms)"""
    try:
        user = request.current_user
        
        # Get all public rooms
        public_rooms = list(rooms_collection.find({'type': 'public', 'is_active': True}))
        
        # Get user's private rooms (where user is a member)
        private_rooms = list(rooms_collection.find({
            'type': 'private',
            'is_active': True,
            'members.user_id': user['_id']
        }))
        
        # Combine and format rooms
        all_rooms = []
        
        # Add public rooms
        for room in public_rooms:
            room_data = {
                'id': str(room['_id']),
                'name': room['name'],
                'description': room.get('description', ''),
                'type': room['type'],
                'member_count': len(room.get('members', [])),
                'created_at': room['created_at'].isoformat()
            }
            all_rooms.append(room_data)
        
        # Add private rooms (with room_id for members)
        for room in private_rooms:
            room_data = {
                'id': str(room['_id']),
                'name': room['name'],
                'description': room.get('description', ''),
                'type': room['type'],
                'room_id': room.get('room_id'),
                'owner_id': str(room['owner_id']),
                'member_count': len(room.get('members', [])),
                'created_at': room['created_at'].isoformat()
            }
            all_rooms.append(room_data)
        
        return jsonify({'rooms': all_rooms}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/public', methods=['GET'])
@token_required
def get_public_rooms():
    """Get all public rooms"""
    try:
        rooms = list(rooms_collection.find({'type': 'public', 'is_active': True}))
        
        room_list = []
        for room in rooms:
            room_data = {
                'id': str(room['_id']),
                'name': room['name'],
                'description': room.get('description', ''),
                'type': room['type'],
                'member_count': len(room.get('members', [])),
                'created_at': room['created_at'].isoformat()
            }
            room_list.append(room_data)
        
        return jsonify({'rooms': room_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/private', methods=['GET'])
@token_required
def get_private_rooms():
    """Get user's private rooms"""
    try:
        user = request.current_user
        
        # Get user's private rooms (where user is a member)
        rooms = list(rooms_collection.find({
            'type': 'private',
            'is_active': True,
            'members.user_id': user['_id']
        }))
        
        room_list = []
        for room in rooms:
            room_data = {
                'id': str(room['_id']),
                'name': room['name'],
                'description': room.get('description', ''),
                'type': room['type'],
                'room_id': room.get('room_id'),
                'owner_id': str(room['owner_id']),
                'member_count': len(room.get('members', [])),
                'created_at': room['created_at'].isoformat()
            }
            room_list.append(room_data)
        
        return jsonify({'rooms': room_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/join-by-id', methods=['POST'])
@token_required
def join_room_by_id():
    """Join a private room using room ID"""
    try:
        data = request.get_json()
        user = request.current_user
        
        if not data or not data.get('room_id'):
            return jsonify({'error': 'Room ID is required'}), 400
        
        room_id = data['room_id'].strip().upper()  # Convert to uppercase for consistency
        
        if len(room_id) != 8:
            return jsonify({'error': 'Invalid room ID format. Room ID must be 8 characters long.'}), 400
        
        # Find the private room with this room_id
        room = rooms_collection.find_one({
            'room_id': room_id,
            'type': 'private',
            'is_active': True
        })
        
        if not room:
            return jsonify({'error': 'Room not found. Please check the Room ID and try again.'}), 404
        
        # Check if user is already a member
        is_member = any(member['user_id'] == user['_id'] for member in room.get('members', []))
        
        if is_member:
            return jsonify({
                'message': 'You are already a member of this room',
                'room': {
                    'id': str(room['_id']),
                    'name': room['name'],
                    'room_id': room_id
                }
            }), 200
        
        # Add user to room members
        rooms_collection.update_one(
            {'_id': room['_id']},
            {
                '$push': {
                    'members': {
                        'user_id': user['_id'],
                        'joined_at': datetime.utcnow(),
                        'role': 'member'
                    }
                }
            }
        )
        
        return jsonify({
            'message': 'Successfully joined the private room!',
            'room': {
                'id': str(room['_id']),
                'name': room['name'],
                'description': room.get('description', ''),
                'room_id': room_id
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms', methods=['POST'])
@token_required
def create_room():
    """Create a new chat room"""
    try:
        data = request.get_json()
        user = request.current_user
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Room name is required'}), 400
        
        name = data['name'].strip()
        description = data.get('description', '').strip()
        room_type = data.get('type', 'public')
        
        if room_type not in ['public', 'private']:
            return jsonify({'error': 'Room type must be public or private'}), 400
        
        # Check if room name already exists (only for public rooms)
        if room_type == 'public' and rooms_collection.find_one({'name': name, 'type': 'public'}):
            return jsonify({'error': 'Public room name already exists'}), 409
        
        # Generate room ID for private rooms
        room_id = None
        if room_type == 'private':
            room_id = generate_room_id()
        
        # Create room
        room_doc = {
            'name': name,
            'description': description,
            'type': room_type,
            'owner_id': user['_id'],
            'members': [{
                'user_id': user['_id'],
                'joined_at': datetime.utcnow(),
                'role': 'admin'
            }],
            'max_members': data.get('max_members'),
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Add room_id field for private rooms
        if room_type == 'private':
            room_doc['room_id'] = room_id
        
        result = rooms_collection.insert_one(room_doc)
        room_object_id = result.inserted_id
        
        response_data = {
            'message': 'Room created successfully',
            'room': {
                'id': str(room_object_id),
                'name': name,
                'description': description,
                'type': room_type
            }
        }
        
        # Include room_id in response for private rooms
        if room_type == 'private':
            response_data['room']['room_id'] = room_id
        
        return jsonify(response_data), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/<room_id>/messages', methods=['GET'])
@token_required
def get_room_messages(room_id):
    """Get messages for a specific room"""
    try:
        # Validate room_id
        try:
            room_object_id = ObjectId(room_id)
        except InvalidId:
            return jsonify({'error': 'Invalid room ID'}), 400
        
        # Check if user has access to room
        user = request.current_user
        room = rooms_collection.find_one({'_id': room_object_id})
        
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        
        # Check if user is member of the room
        is_member = any(member['user_id'] == user['_id'] for member in room.get('members', []))
        if not is_member and room['type'] == 'private':
            return jsonify({'error': 'Access denied'}), 403
        
        # Get messages with pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit
        
        messages = list(messages_collection.find(
            {'room_id': room_object_id, 'deleted': {'$ne': True}}
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        # Get sender information for each message
        message_list = []
        for message in reversed(messages):  # Reverse to get chronological order
            sender = users_collection.find_one({'_id': message['sender_id']})
            message_data = {
                'id': str(message['_id']),
                'content': message['content'],
                'sender': {
                    'id': str(sender['_id']),
                    'username': sender['username'],
                    'display_name': sender['display_name']
                } if sender else None,
                'timestamp': message['timestamp'].isoformat(),
                'edited': message.get('edited', False)
            }
            message_list.append(message_data)
        
        return jsonify({'messages': message_list}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SocketIO Events
@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate user for SocketIO connection"""
    try:
        token = data.get('token')
        if not token:
            emit('auth_error', {'message': 'Token required'})
            return
        
        user_id = verify_token(token)
        if not user_id:
            emit('auth_error', {'message': 'Invalid token'})
            return
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            emit('auth_error', {'message': 'User not found'})
            return
        
        # Store auth data in session
        session['auth_data'] = {'user_id': user_id, 'username': user['username']}
        
        # Update user online status
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'is_online': True, 'last_seen': datetime.utcnow()}}
        )
        
        # Store active user
        active_users[request.sid] = {
            'user_id': user_id,
            'username': user['username'],
            'display_name': user['display_name']
        }
        
        emit('authenticated', {'message': 'Authentication successful', 'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name']
        }})
        
        # Broadcast user online status
        socketio.emit('user_online', {
            'user_id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name']
        })
        
    except Exception as e:
        emit('auth_error', {'message': str(e)})

@socketio.on('join_room')
@socketio_token_required
def handle_join_room(user, data):
    """Handle user joining a room"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            emit('error', {'message': 'Room ID required'})
            return
        
        # Validate room
        try:
            room_object_id = ObjectId(room_id)
        except InvalidId:
            emit('error', {'message': 'Invalid room ID'})
            return
        
        room = rooms_collection.find_one({'_id': room_object_id})
        if not room:
            emit('error', {'message': 'Room not found'})
            return
        
        # Check if user is already a member
        is_member = any(member['user_id'] == user['_id'] for member in room.get('members', []))
        
        if not is_member:
            # Add user to room members
            rooms_collection.update_one(
                {'_id': room_object_id},
                {
                    '$push': {
                        'members': {
                            'user_id': user['_id'],
                            'joined_at': datetime.utcnow(),
                            'role': 'member'
                        }
                    }
                }
            )
        
        # Join the SocketIO room
        join_room(room_id)
        
        emit('room_joined', {'room_id': room_id, 'room_name': room['name']})
        
        # Notify other users in the room
        emit('user_joined_room', {
            'user_id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name'],
            'room_id': room_id
        }, room=room_id, include_self=False)
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('leave_room')
@socketio_token_required
def handle_leave_room(user, data):
    """Handle user leaving a room"""
    try:
        room_id = data.get('room_id')
        if not room_id:
            emit('error', {'message': 'Room ID required'})
            return
        
        # Leave the SocketIO room
        leave_room(room_id)
        
        emit('room_left', {'room_id': room_id})
        
        # Notify other users in the room
        emit('user_left_room', {
            'user_id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name'],
            'room_id': room_id
        }, room=room_id, include_self=False)
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('send_message')
@socketio_token_required
def handle_send_message(user, data):
    """Handle sending a message"""
    try:
        room_id = data.get('room_id')
        content = data.get('content', '').strip()
        
        if not room_id or not content:
            emit('error', {'message': 'Room ID and content are required'})
            return
        
        # Validate room
        try:
            room_object_id = ObjectId(room_id)
        except InvalidId:
            emit('error', {'message': 'Invalid room ID'})
            return
        
        room = rooms_collection.find_one({'_id': room_object_id})
        if not room:
            emit('error', {'message': 'Room not found'})
            return
        
        # Create message document
        message_doc = {
            'room_id': room_object_id,
            'sender_id': user['_id'],
            'content': content,
            'message_type': 'text',
            'edited': False,
            'deleted': False,
            'timestamp': datetime.utcnow()
        }
        
        # Save message to database
        result = messages_collection.insert_one(message_doc)
        message_id = result.inserted_id
        
        # Prepare message data for broadcasting
        message_data = {
            'id': str(message_id),
            'room_id': room_id,
            'content': content,
            'sender': {
                'id': str(user['_id']),
                'username': user['username'],
                'display_name': user['display_name']
            },
            'timestamp': message_doc['timestamp'].isoformat()
        }
        
        # Broadcast message to all users in the room
        socketio.emit('new_message', message_data, room=room_id)
        
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('typing')
@socketio_token_required
def handle_typing(user, data):
    """Handle typing indicator"""
    room_id = data.get('room_id')
    if room_id:
        emit('user_typing', {
            'user_id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name'],
            'room_id': room_id
        }, room=room_id, include_self=False)

@socketio.on('stop_typing')
@socketio_token_required
def handle_stop_typing(user, data):
    """Handle stop typing indicator"""
    room_id = data.get('room_id')
    if room_id:
        emit('user_stop_typing', {
            'user_id': str(user['_id']),
            'username': user['username'],
            'display_name': user['display_name'],
            'room_id': room_id
        }, room=room_id, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')
    
    # Remove user from active users
    if request.sid in active_users:
        user_data = active_users[request.sid]
        user_id = user_data['user_id']
        
        # Update user online status
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_online': False, 'last_seen': datetime.utcnow()}}
        )
        
        # Broadcast user offline status
        socketio.emit('user_offline', {
            'user_id': user_id,
            'username': user_data['username']
        })
        
        del active_users[request.sid]

if __name__ == '__main__':
    # Create indexes for better performance
    try:
        # Users collection indexes
        users_collection.create_index('username', unique=True)
        users_collection.create_index('email', unique=True)
        users_collection.create_index('is_online')
        
        # Rooms collection indexes
        rooms_collection.create_index('name')
        rooms_collection.create_index('type')
        rooms_collection.create_index('room_id', unique=True, sparse=True)  # Sparse index for room_id (only private rooms)
        rooms_collection.create_index('owner_id')
        rooms_collection.create_index('members.user_id')
        
        # Messages collection indexes
        messages_collection.create_index('room_id')
        messages_collection.create_index('sender_id')
        messages_collection.create_index('timestamp')
        messages_collection.create_index([('room_id', 1), ('timestamp', -1)])
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)