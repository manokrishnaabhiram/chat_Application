// Global variables
let socket;
let currentUser = null;
let currentRoom = null;
let currentRoomData = null;
let authToken = null;
let typingTimer = null;
let isTyping = false;

// DOM elements
const loginModal = document.getElementById('loginModal');
const chatContainer = document.getElementById('chatContainer');
const loginForm = document.getElementById('loginFormSubmit');
const registerForm = document.getElementById('registerFormSubmit');
const createRoomForm = document.getElementById('createRoomForm');
const messageInput = document.getElementById('messageInput');
const messagesContainer = document.getElementById('messagesContainer');
const roomList = document.getElementById('roomList');
const privateRoomList = document.getElementById('privateRoomList');
const onlineUsersList = document.getElementById('onlineUsersList');
const currentUserName = document.getElementById('currentUserName');
const currentRoomName = document.getElementById('currentRoomName');
const roomMembersCount = document.getElementById('roomMembersCount');
const roomIdDisplay = document.getElementById('roomIdDisplay');
const roomIdValue = document.getElementById('roomIdValue');
const messageInputContainer = document.getElementById('messageInputContainer');
const typingIndicator = document.getElementById('typingIndicator');
const typingText = document.getElementById('typingText');
const roomIdInput = document.getElementById('roomIdInput');

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Check for stored auth token
    const storedToken = localStorage.getItem('chat_auth_token');
    if (storedToken) {
        authToken = storedToken;
        // Verify token with server
        verifyTokenAndLogin();
    }

    // Set up event listeners
    setupEventListeners();
});

// Event listeners setup
function setupEventListeners() {
    // Auth forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    createRoomForm.addEventListener('submit', handleCreateRoom);

    // Message input
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // Typing indicators
    messageInput.addEventListener('input', handleTyping);
    messageInput.addEventListener('blur', stopTyping);

    // Room ID input
    if (roomIdInput) {
        roomIdInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                joinRoomById();
            }
        });
        
        // Auto-uppercase input
        roomIdInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    // Prevent form submission on enter for other inputs
    document.querySelectorAll('input').forEach(input => {
        if (input.id !== 'messageInput') {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && input.type !== 'submit') {
                    e.preventDefault();
                }
            });
        }
    });
}

// Authentication functions
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('chat_auth_token', authToken);
            showToast('Login successful!', 'success');
            showChatInterface();
            initializeSocket();
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const displayName = document.getElementById('registerDisplayName').value.trim();
    const password = document.getElementById('registerPassword').value;

    if (!username || !email || !password) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username, 
                email, 
                password,
                display_name: displayName || username
            })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('chat_auth_token', authToken);
            showToast('Registration successful!', 'success');
            showChatInterface();
            initializeSocket();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

async function verifyTokenAndLogin() {
    try {
        const response = await fetch('/api/profile', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showChatInterface();
            initializeSocket();
        } else {
            // Token is invalid, remove it
            localStorage.removeItem('chat_auth_token');
            authToken = null;
        }
    } catch (error) {
        console.error('Token verification error:', error);
        localStorage.removeItem('chat_auth_token');
        authToken = null;
    }
}

function logout() {
    if (socket) {
        socket.disconnect();
    }
    
    fetch('/api/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    });

    localStorage.removeItem('chat_auth_token');
    authToken = null;
    currentUser = null;
    currentRoom = null;
    
    chatContainer.style.display = 'none';
    loginModal.classList.add('active');
    
    // Reset forms
    document.getElementById('loginFormSubmit').reset();
    document.getElementById('registerFormSubmit').reset();
    
    showToast('Logged out successfully', 'success');
}

// UI functions
function showTab(tabName) {
    // Remove active class from all tabs and forms
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    
    // Add active class to selected tab and form
    event.target.classList.add('active');
    document.getElementById(tabName + 'Form').classList.add('active');
}

function showChatInterface() {
    loginModal.classList.remove('active');
    chatContainer.style.display = 'flex';
    currentUserName.textContent = currentUser.display_name;
    
    // Load initial data
    loadRooms();
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Socket.IO functions
function initializeSocket() {
    socket = io();
    
    // Connection events
    socket.on('connect', function() {
        console.log('Connected to server');
        // Authenticate with server
        socket.emit('authenticate', { token: authToken });
    });

    socket.on('authenticated', function(data) {
        console.log('Authenticated:', data);
        showToast('Connected to chat server', 'success');
    });

    socket.on('auth_error', function(data) {
        console.error('Authentication error:', data);
        showToast('Authentication failed: ' + data.message, 'error');
        logout();
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showToast('Disconnected from server', 'warning');
    });

    // Room events
    socket.on('room_joined', function(data) {
        console.log('Joined room:', data);
        loadRoomMessages(data.room_id);
        messageInputContainer.style.display = 'block';
    });

    socket.on('room_left', function(data) {
        console.log('Left room:', data);
        if (currentRoom === data.room_id) {
            currentRoom = null;
            currentRoomName.textContent = 'Select a room to start chatting';
            roomMembersCount.textContent = '';
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <i class="fas fa-comments"></i>
                    <h3>Welcome to Chat App!</h3>
                    <p>Select a room from the sidebar to start chatting</p>
                </div>
            `;
            messageInputContainer.style.display = 'none';
        }
    });

    socket.on('user_joined_room', function(data) {
        if (currentRoom === data.room_id) {
            addSystemMessage(`${data.display_name} joined the room`);
        }
    });

    socket.on('user_left_room', function(data) {
        if (currentRoom === data.room_id) {
            addSystemMessage(`${data.display_name} left the room`);
        }
    });

    // Message events
    socket.on('new_message', function(data) {
        if (currentRoom === data.room_id) {
            addMessage(data);
        }
    });

    // Typing events
    socket.on('user_typing', function(data) {
        if (currentRoom === data.room_id && data.user_id !== currentUser.id) {
            showTypingIndicator(data.display_name);
        }
    });

    socket.on('user_stop_typing', function(data) {
        if (currentRoom === data.room_id && data.user_id !== currentUser.id) {
            hideTypingIndicator();
        }
    });

    // User status events
    socket.on('user_online', function(data) {
        updateUserStatus(data.user_id, true);
    });

    socket.on('user_offline', function(data) {
        updateUserStatus(data.user_id, false);
    });

    // Error events
    socket.on('error', function(data) {
        console.error('Socket error:', data);
        showToast(data.message || 'An error occurred', 'error');
    });
}

// Room functions
async function loadRooms() {
    try {
        const response = await fetch('/api/rooms', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayRooms(data.rooms);
        } else {
            showToast('Failed to load rooms', 'error');
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
        showToast('Network error loading rooms', 'error');
    }
}

function displayRooms(rooms) {
    // Separate public and private rooms
    const publicRooms = rooms.filter(room => room.type === 'public');
    const privateRooms = rooms.filter(room => room.type === 'private');
    
    // Display public rooms
    roomList.innerHTML = '';
    publicRooms.forEach(room => {
        const roomElement = createRoomElement(room);
        roomList.appendChild(roomElement);
    });
    
    // Display private rooms
    privateRoomList.innerHTML = '';
    privateRooms.forEach(room => {
        const roomElement = createRoomElement(room);
        privateRoomList.appendChild(roomElement);
    });
    
    // Show message if no rooms exist
    if (publicRooms.length === 0) {
        roomList.innerHTML = `
            <div class="room-item" style="opacity: 0.6; pointer-events: none;">
                <div class="room-icon">
                    <i class="fas fa-hashtag"></i>
                </div>
                <div class="room-details">
                    <div class="room-name">No public rooms</div>
                    <div class="room-description">Create a new room to start chatting</div>
                </div>
            </div>
        `;
    }
    
    if (privateRooms.length === 0) {
        privateRoomList.innerHTML = `
            <div class="room-item" style="opacity: 0.6; pointer-events: none;">
                <div class="room-icon">
                    <i class="fas fa-lock"></i>
                </div>
                <div class="room-details">
                    <div class="room-name">No private sessions</div>
                    <div class="room-description">Join using Room ID or create a private room</div>
                </div>
            </div>
        `;
    }
}

function createRoomElement(room) {
    const roomElement = document.createElement('div');
    roomElement.className = 'room-item';
    roomElement.onclick = () => joinRoom(room.id, room.name, room);
    
    const iconClass = room.type === 'private' ? 'fa-lock' : 'fa-hashtag';
    
    // Only show Room ID to the room creator for private rooms
    let roomIdDisplay = '';
    if (room.type === 'private' && room.room_id && room.owner_id === currentUser.id) {
        roomIdDisplay = `<div class="room-id-small">ID: ${room.room_id}</div>`;
    }
    
    roomElement.innerHTML = `
        <div class="room-icon">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="room-details">
            <div class="room-name">${room.name}</div>
            <div class="room-description">${room.member_count} members</div>
            ${roomIdDisplay}
        </div>
    `;
    
    return roomElement;
}

function joinRoom(roomId, roomName, roomData = null) {
    // Update UI
    document.querySelectorAll('.room-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Leave current room if any
    if (currentRoom && currentRoom !== roomId) {
        socket.emit('leave_room', { room_id: currentRoom });
    }
    
    // Join new room
    currentRoom = roomId;
    currentRoomData = roomData;
    currentRoomName.textContent = roomName;
    
    // Update room header with room ID if it's a private room and user is the owner
    if (roomData && roomData.type === 'private' && roomData.room_id && roomData.owner_id === currentUser.id) {
        roomIdDisplay.style.display = 'block';
        roomIdValue.textContent = roomData.room_id;
    } else {
        roomIdDisplay.style.display = 'none';
    }
    
    // Clear messages container
    messagesContainer.innerHTML = '';
    
    // Join room via socket
    socket.emit('join_room', { room_id: roomId });
}

// Room ID functionality
async function joinRoomById() {
    const roomId = roomIdInput.value.trim().toUpperCase();
    
    if (!roomId) {
        showToast('Please enter a Room ID', 'error');
        return;
    }
    
    if (roomId.length !== 8) {
        showToast('Room ID must be exactly 8 characters long', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/rooms/join-by-id', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ room_id: roomId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            roomIdInput.value = ''; // Clear input
            loadRooms(); // Refresh room list
            
            // Automatically join the room
            setTimeout(() => {
                joinRoom(data.room.id, data.room.name, data.room);
            }, 500);
        } else {
            showToast(data.error || 'Failed to join room', 'error');
        }
    } catch (error) {
        console.error('Error joining room by ID:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

// Copy room ID functionality
function copyRoomId() {
    if (currentRoomData && currentRoomData.room_id && currentRoomData.owner_id === currentUser.id) {
        navigator.clipboard.writeText(currentRoomData.room_id).then(() => {
            showToast('Room ID copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = currentRoomData.room_id;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('Room ID copied to clipboard!', 'success');
        });
    } else {
        showToast('Only the room creator can copy the Room ID', 'error');
    }
}

function copyCreatedRoomId() {
    const roomId = document.getElementById('createdRoomId').textContent;
    if (roomId) {
        navigator.clipboard.writeText(roomId).then(() => {
            showToast('Room ID copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = roomId;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('Room ID copied to clipboard!', 'success');
        });
    }
}

// Modal functions for room creation success
function showRoomCreatedModal(roomId) {
    document.getElementById('createdRoomId').textContent = roomId;
    document.getElementById('roomCreatedModal').classList.add('active');
}

function closeRoomCreatedModal() {
    document.getElementById('roomCreatedModal').classList.remove('active');
}

async function loadRoomMessages(roomId) {
    try {
        const response = await fetch(`/api/rooms/${roomId}/messages`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayMessages(data.messages);
        } else {
            showToast('Failed to load messages', 'error');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        showToast('Network error loading messages', 'error');
    }
}

function displayMessages(messages) {
    messagesContainer.innerHTML = '';
    
    messages.forEach(message => {
        addMessage(message, false);
    });
    
    // Scroll to bottom
    scrollToBottom();
}

// Message functions
function sendMessage() {
    const content = messageInput.value.trim();
    
    if (!content || !currentRoom) {
        return;
    }
    
    // Send message via socket
    socket.emit('send_message', {
        room_id: currentRoom,
        content: content
    });
    
    // Clear input
    messageInput.value = '';
    
    // Stop typing indicator
    stopTyping();
}

function addMessage(messageData, animate = true) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${messageData.sender && messageData.sender.id === currentUser.id ? 'own' : ''}`;
    
    const timestamp = new Date(messageData.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${messageData.sender ? messageData.sender.display_name : 'System'}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-text">${escapeHtml(messageData.content)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // Auto scroll to bottom
    scrollToBottom();
}

function addSystemMessage(content) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message system';
    messageElement.innerHTML = `
        <div class="message-content" style="background: #f1f2f6; color: #666; text-align: center; font-style: italic;">
            <div class="message-text">${escapeHtml(content)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Typing functions
function handleTyping() {
    if (!currentRoom) return;
    
    if (!isTyping) {
        isTyping = true;
        socket.emit('typing', { room_id: currentRoom });
    }
    
    // Clear existing timer
    clearTimeout(typingTimer);
    
    // Set new timer
    typingTimer = setTimeout(() => {
        stopTyping();
    }, 1000);
}

function stopTyping() {
    if (isTyping && currentRoom) {
        isTyping = false;
        socket.emit('stop_typing', { room_id: currentRoom });
    }
    
    clearTimeout(typingTimer);
}

function showTypingIndicator(userName) {
    typingText.textContent = `${userName} is typing...`;
    typingIndicator.style.display = 'flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// Room creation functions
function showCreateRoomModal() {
    document.getElementById('createRoomModal').classList.add('active');
}

function closeCreateRoomModal() {
    document.getElementById('createRoomModal').classList.remove('active');
    document.getElementById('createRoomForm').reset();
}

async function handleCreateRoom(e) {
    e.preventDefault();
    
    const name = document.getElementById('roomName').value.trim();
    const description = document.getElementById('roomDescription').value.trim();
    const type = document.getElementById('roomType').value;
    
    if (!name) {
        showToast('Room name is required', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ name, description, type })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeCreateRoomModal();
            
            if (type === 'private' && data.room.room_id) {
                // Show success modal with room ID for private rooms
                showRoomCreatedModal(data.room.room_id);
            } else {
                showToast('Room created successfully!', 'success');
            }
            
            loadRooms(); // Refresh room list
        } else {
            showToast(data.error || 'Failed to create room', 'error');
        }
    } catch (error) {
        console.error('Error creating room:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateUserStatus(userId, isOnline) {
    // Update user status in online users list
    // This can be expanded based on requirements
    console.log(`User ${userId} is now ${isOnline ? 'online' : 'offline'}`);
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// Handle connection issues
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
    if (authToken && !socket.connected) {
        initializeSocket();
    }
});

window.addEventListener('offline', function() {
    showToast('Connection lost', 'warning');
});