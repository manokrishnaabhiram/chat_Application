# Realtime Chat Application

A realtime chat application built with Python (Flask-SocketIO) backend and MongoDB for data persistence. Features include user authentication, chat rooms, and real-time messaging.

## Features

- Real-time messaging using WebSocket
- User authentication with JWT tokens
- Chat rooms (public and private)
- **Private rooms with unique Room IDs**
- **Join private rooms by entering Room ID**
- **Separate "Private Sessions" category for private rooms**
- Message history
- Online user status
- Responsive web interface

## Technology Stack

- **Backend**: Python, Flask, Flask-SocketIO
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript, Socket.IO
- **Authentication**: JWT (JSON Web Tokens)

## Database Schema

### Collections Overview

The application uses MongoDB with the following collections:

#### 1. Users Collection
```json
{
  "_id": ObjectId,
  "username": "string (unique)",
  "email": "string (unique)",
  "password_hash": "string",
  "display_name": "string",
  "avatar_url": "string (optional)",
  "is_online": "boolean",
  "last_seen": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Indexes:**
- `username`: unique index
- `email`: unique index
- `is_online`: index for quick online user queries

#### 2. Chat Rooms Collection
```json
{
  "_id": ObjectId,
  "name": "string",
  "description": "string (optional)",
  "type": "string (public/private)",
  "room_id": "string (8-character alphanumeric, only for private rooms)",
  "owner_id": ObjectId,
  "members": [
    {
      "user_id": ObjectId,
      "joined_at": "datetime",
      "role": "string (admin/member)"
    }
  ],
  "max_members": "number (optional)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Indexes:**
- `name`: index
- `type`: index
- `room_id`: unique index (for private rooms)
- `owner_id`: index
- `members.user_id`: index

#### 3. Messages Collection
```json
{
  "_id": ObjectId,
  "room_id": ObjectId,
  "sender_id": ObjectId,
  "content": "string",
  "message_type": "string (text/image/file)",
  "file_url": "string (optional)",
  "reply_to": ObjectId (optional),
  "edited": "boolean",
  "edited_at": "datetime (optional)",
  "deleted": "boolean",
  "deleted_at": "datetime (optional)",
  "timestamp": "datetime"
}
```

**Indexes:**
- `room_id`: index for room message queries
- `sender_id`: index
- `timestamp`: index for chronological ordering
- Compound index: `{room_id: 1, timestamp: -1}` for efficient room message pagination

#### 4. User Sessions Collection
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "session_token": "string",
  "socket_id": "string (optional)",
  "ip_address": "string",
  "user_agent": "string",
  "is_active": "boolean",
  "created_at": "datetime",
  "expires_at": "datetime"
}
```

**Indexes:**
- `user_id`: index
- `session_token`: unique index
- `expires_at`: TTL index for automatic cleanup

#### 5. Private Messages Collection
```json
{
  "_id": ObjectId,
  "sender_id": ObjectId,
  "receiver_id": ObjectId,
  "content": "string",
  "message_type": "string (text/image/file)",
  "file_url": "string (optional)",
  "read": "boolean",
  "read_at": "datetime (optional)",
  "edited": "boolean",
  "edited_at": "datetime (optional)",
  "deleted": "boolean",
  "deleted_at": "datetime (optional)",
  "timestamp": "datetime"
}
```

**Indexes:**
- Compound index: `{sender_id: 1, receiver_id: 1, timestamp: -1}`
- `receiver_id`: index
- `read`: index

### Relationships

1. **Users ↔ Chat Rooms**: Many-to-many relationship through the `members` array in chat rooms
2. **Users ↔ Messages**: One-to-many relationship (one user can send many messages)
3. **Chat Rooms ↔ Messages**: One-to-many relationship (one room can have many messages)
4. **Users ↔ Private Messages**: Many-to-many relationship for direct messaging
5. **Users ↔ Sessions**: One-to-many relationship for multiple device support

### Data Storage Format

All data is stored in JSON format in MongoDB, which natively supports JSON documents. The application uses:

- **BSON**: Binary JSON format used internally by MongoDB
- **UTC Timestamps**: All datetime fields are stored in UTC
- **ObjectId**: MongoDB's native 12-byte identifier for documents
- **Embedded Documents**: For complex structures like room members
- **Arrays**: For storing lists like room members and message references

## Setup Instructions

### Prerequisites

1. Python 3.8+
2. MongoDB 4.4+
3. pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chat_Application
```

2. **Quick Start** (use the startup scripts):
   - **Windows**: Double-click `start.bat` or run in Command Prompt
   - **Linux/Mac**: Run `chmod +x start.sh && ./start.sh`

3. **Manual Installation**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Update MongoDB connection string and JWT secrets
   - Example `.env` file:
   ```
   MONGO_URI=mongodb://localhost:27017/chat_app
   JWT_SECRET_KEY=your-super-secret-jwt-key-here
   FLASK_SECRET_KEY=your-flask-secret-key-here
   FLASK_ENV=development
   PORT=5000
   ```

5. **Set up MongoDB**:
   - Install MongoDB locally or use MongoDB Atlas
   - Create a database named `chat_app`
   - (Optional) Run the seeder script to create sample data:
   ```bash
   python utils/seed_data.py
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Access the application**:
   - Open your browser and navigate to `http://localhost:5000`
   - Register a new account or use sample credentials (if seeded):
     - Username: `admin`, Password: `admin123`
     - Username: `john_doe`, Password: `password123`

### Sample Data

To populate your database with sample data, run:
```bash
python utils/seed_data.py
```

This will create:
- Sample users with login credentials
- Sample chat rooms (General, Technology, Random, Team Private)
- Sample messages
- Database indexes for optimal performance

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/profile` - Get user profile

### Chat Rooms
- `GET /api/rooms` - Get all accessible rooms (public + user's private rooms)
- `GET /api/rooms/public` - Get all public rooms only
- `GET /api/rooms/private` - Get user's private rooms only
- `POST /api/rooms` - Create a new room
- `POST /api/rooms/join-by-id` - Join a private room using room ID
- `GET /api/rooms/:id` - Get room details
- `POST /api/rooms/:id/join` - Join a room
- `DELETE /api/rooms/:id/leave` - Leave a room

### Messages
- `GET /api/rooms/:id/messages` - Get room messages
- `GET /api/users/:id/messages` - Get private messages

### WebSocket Events

#### Client to Server
- `join_room` - Join a chat room
- `leave_room` - Leave a chat room
- `send_message` - Send a message
- `typing` - User typing indicator
- `stop_typing` - Stop typing indicator

#### Server to Client
- `message` - New message received
- `user_joined` - User joined room
- `user_left` - User left room
- `typing` - User is typing
- `stop_typing` - User stopped typing
- `online_users` - List of online users

## Private Rooms with Unique Room IDs

### Overview
Private rooms are secure chat spaces that can only be accessed by invited members or users who know the unique Room ID. Each private room is assigned an 8-character alphanumeric Room ID when created.

### Key Features

#### 1. Room ID Generation
- **Automatic Generation**: When a private room is created, the system automatically generates a unique 8-character alphanumeric Room ID
- **Format**: Consists of uppercase letters (A-Z) and numbers (0-9), e.g., `A7K2M9P1`
- **Uniqueness**: Each Room ID is guaranteed to be unique across the entire system
- **Case Insensitive**: Users can enter Room IDs in any case (upper/lower)

#### 2. Room Access Methods
- **Creator Access**: Room creator automatically becomes a member with admin privileges
- **Room ID Entry**: Any user can join a private room by entering the correct Room ID
- **Direct Invitation**: Room admins can share the Room ID with other users

#### 3. User Interface Features

#### Room Categories
- **Public Rooms**: Listed under "Chat Rooms" section for all users to see
- **Private Sessions**: Listed under "Private Sessions" section, visible only to room members
- **Room ID Display**: Private room creators can see their Room ID displayed after the room name (marked with 👑)

#### Room ID Entry
- **Join by Room ID**: Dedicated input field accessible to all users
- **Easy Access**: Room ID entry option always visible in the sidebar
- **Instant Join**: Immediate access upon entering valid Room ID

#### Security & Privacy
- **Member-Only Visibility**: Private rooms only appear in the room list for current members
- **Access Control**: Non-members cannot see private room content or messages
- **Room ID Visibility**: Only room creators can see and share Room IDs (marked with 👑 crown icon)
- **Secure IDs**: Room IDs are cryptographically secure and difficult to guess

### Usage Examples

#### Creating a Private Room
1. Click "Create Room" button
2. Select "Private" as room type
3. Enter room name and description
4. Room is created with auto-generated Room ID (e.g., `A7K2M9P1`)
5. Share Room ID with intended participants

#### Joining a Private Room
1. Obtain Room ID from room creator or another member
2. Click "Join by Room ID" in the sidebar
3. Enter the 8-character Room ID
4. Instantly join the private room and start chatting

#### Managing Private Rooms
1. Room appears in "Private Sessions" category
2. Room ID is displayed after room name for the creator only (marked with 👑)
3. Room ID is shown in the room header when the creator joins the room
4. Only room creator can copy and share the Room ID
5. Other members can participate but cannot see the Room ID

## Project Structure

```
chat_Application/
├── app.py                 # Main Flask application with SocketIO
├── config.py              # Application configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Environment variables (create from .env.example)
├── .gitignore           # Git ignore file
├── start.bat            # Windows startup script
├── start.sh             # Linux/Mac startup script
├── static/              # Static files
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   └── js/
│       └── app.js       # Client-side JavaScript
├── templates/           # HTML templates
│   └── index.html       # Main chat interface
├── utils/               # Utility functions
│   └── seed_data.py     # Database seeder script
└── README.md            # This documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
It is a Realtime chart application

## How to Run the Application

Follow these step-by-step instructions to run the chat application on your system:

### Prerequisites

1. **Python 3.7 or higher** installed on your system
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **MongoDB** (Optional - uses default local connection)
   - Install MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Or use MongoDB Atlas (cloud) by setting the `MONGO_URI` environment variable

### Step-by-Step Setup

#### Step 1: Clone or Download the Repository
```bash
git clone https://github.com/manokrishnaabhiram/chat_Application.git
cd chat_Application
```
Or download and extract the ZIP file.

#### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**If you encounter SSL/eventlet errors, also install:**
```bash
pip install gevent-websocket
```

#### Step 3: Set Up Environment Variables (Optional)
Create a `.env` file in the project root (optional - the app works with defaults):
```env
FLASK_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
MONGO_URI=mongodb://localhost:27017/chat_app
PORT=5000
FLASK_ENV=development
```

#### Step 4: Start MongoDB (If using local MongoDB)
- **Windows**: Start MongoDB service from Services or run `mongod`
- **Mac/Linux**: Run `sudo systemctl start mongod` or `brew services start mongodb`

#### Step 5: Run the Application

**Option A: Using Python directly**
```bash
python app.py
```

**Option B: Using the provided scripts**
- **Windows**: Double-click `start.bat` or run it from command prompt
- **Linux/Mac**: Run `./start.sh` (make it executable first: `chmod +x start.sh`)

#### Step 6: Access the Application

Once the server starts successfully, you'll see output like:
```
Server initialized for threading.
Database indexes created successfully
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.19.155.112:5000
```

**Access URLs:**
- **Local access**: http://localhost:5000 or http://127.0.0.1:5000
- **Network access**: http://[your-ip-address]:5000 (replace with your actual IP)
- **From other devices**: Use your computer's IP address on port 5000

### Troubleshooting

#### Common Issues and Solutions:

1. **SSL/eventlet errors**:
   ```bash
   pip install gevent-websocket
   ```

2. **MongoDB connection errors**:
   - Ensure MongoDB is running
   - Check the `MONGO_URI` in your `.env` file
   - Default connection: `mongodb://localhost:27017/chat_app`

3. **Port already in use**:
   - Change the PORT in `.env` file
   - Or kill the process using port 5000: `netstat -ano | findstr :5000` (Windows)

4. **Permission errors on Linux/Mac**:
   ```bash
   chmod +x start.sh
   ```

5. **Python not found**:
   - Ensure Python is installed and added to PATH
   - Try `python3` instead of `python`

### Development Mode Features

When running in development mode (default):
- **Debug mode enabled**: Automatic reloading on code changes
- **Detailed error messages**: Helpful for debugging
- **SocketIO logging**: Real-time connection logs
- **CORS enabled**: Allows connections from any origin

### Production Deployment Notes

For production deployment:
1. Set `FLASK_ENV=production` in environment variables
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
   ```
3. Set up proper MongoDB authentication and security
4. Configure a reverse proxy (Nginx/Apache)
5. Use HTTPS for secure communication

### First Time Usage

1. Open the application in your web browser
2. Register a new account with username, email, and password
3. Login with your credentials
4. Join existing chat rooms or create new ones
5. Start chatting in real-time!

The application automatically creates necessary database indexes and sets up the required collections on first run.
