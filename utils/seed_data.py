"""
Database seeder script for creating sample data
Run this script to populate the database with sample users and rooms
"""

from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/chat_app')
client = MongoClient(mongo_uri)
db = client.chat_app

# Collections
users_collection = db.users
rooms_collection = db.chat_rooms
messages_collection = db.messages

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def create_sample_users():
    """Create sample users"""
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'admin',
            'email': 'admin@chatapp.com',
            'password_hash': hash_password('admin123'),
            'display_name': 'Administrator',
            'avatar_url': '',
            'is_online': False,
            'last_seen': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password_hash': hash_password('password123'),
            'display_name': 'John Doe',
            'avatar_url': '',
            'is_online': False,
            'last_seen': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'password_hash': hash_password('password123'),
            'display_name': 'Jane Smith',
            'avatar_url': '',
            'is_online': False,
            'last_seen': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password_hash': hash_password('password123'),
            'display_name': 'Bob Wilson',
            'avatar_url': '',
            'is_online': False,
            'last_seen': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    for user in sample_users:
        # Check if user already exists
        if not users_collection.find_one({'username': user['username']}):
            result = users_collection.insert_one(user)
            print(f"Created user: {user['username']} (ID: {result.inserted_id})")
        else:
            print(f"User {user['username']} already exists, skipping...")

def create_sample_rooms():
    """Create sample chat rooms"""
    print("Creating sample rooms...")
    
    # Get admin user for room ownership
    admin_user = users_collection.find_one({'username': 'admin'})
    if not admin_user:
        print("Admin user not found. Please create users first.")
        return
    
    sample_rooms = [
        {
            'name': 'General',
            'description': 'General discussion room for everyone',
            'type': 'public',
            'owner_id': admin_user['_id'],
            'members': [{
                'user_id': admin_user['_id'],
                'joined_at': datetime.utcnow(),
                'role': 'admin'
            }],
            'max_members': None,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Technology',
            'description': 'Discuss the latest in technology and programming',
            'type': 'public',
            'owner_id': admin_user['_id'],
            'members': [{
                'user_id': admin_user['_id'],
                'joined_at': datetime.utcnow(),
                'role': 'admin'
            }],
            'max_members': None,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Random',
            'description': 'Random conversations and off-topic discussions',
            'type': 'public',
            'owner_id': admin_user['_id'],
            'members': [{
                'user_id': admin_user['_id'],
                'joined_at': datetime.utcnow(),
                'role': 'admin'
            }],
            'max_members': None,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'name': 'Team Private',
            'description': 'Private room for team discussions',
            'type': 'private',
            'owner_id': admin_user['_id'],
            'members': [{
                'user_id': admin_user['_id'],
                'joined_at': datetime.utcnow(),
                'role': 'admin'
            }],
            'max_members': 10,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    for room in sample_rooms:
        # Check if room already exists
        if not rooms_collection.find_one({'name': room['name']}):
            result = rooms_collection.insert_one(room)
            print(f"Created room: {room['name']} (ID: {result.inserted_id})")
        else:
            print(f"Room {room['name']} already exists, skipping...")

def create_sample_messages():
    """Create some sample messages"""
    print("Creating sample messages...")
    
    # Get general room and users
    general_room = rooms_collection.find_one({'name': 'General'})
    admin_user = users_collection.find_one({'username': 'admin'})
    john_user = users_collection.find_one({'username': 'john_doe'})
    
    if not all([general_room, admin_user, john_user]):
        print("Required room or users not found. Please create rooms and users first.")
        return
    
    sample_messages = [
        {
            'room_id': general_room['_id'],
            'sender_id': admin_user['_id'],
            'content': 'Welcome to the chat application! Feel free to start conversations here.',
            'message_type': 'text',
            'edited': False,
            'deleted': False,
            'timestamp': datetime.utcnow()
        },
        {
            'room_id': general_room['_id'],
            'sender_id': john_user['_id'],
            'content': 'Hello everyone! Great to be here. This chat app looks amazing!',
            'message_type': 'text',
            'edited': False,
            'deleted': False,
            'timestamp': datetime.utcnow()
        },
        {
            'room_id': general_room['_id'],
            'sender_id': admin_user['_id'],
            'content': 'Thanks! The app supports real-time messaging, multiple rooms, and user authentication.',
            'message_type': 'text',
            'edited': False,
            'deleted': False,
            'timestamp': datetime.utcnow()
        }
    ]
    
    for message in sample_messages:
        result = messages_collection.insert_one(message)
        print(f"Created message: {message['content'][:50]}... (ID: {result.inserted_id})")

def create_indexes():
    """Create database indexes for better performance"""
    print("Creating database indexes...")
    
    try:
        # Users collection indexes
        users_collection.create_index('username', unique=True)
        users_collection.create_index('email', unique=True)
        users_collection.create_index('is_online')
        print("Created users collection indexes")
        
        # Rooms collection indexes
        rooms_collection.create_index('name')
        rooms_collection.create_index('type')
        rooms_collection.create_index('owner_id')
        rooms_collection.create_index('members.user_id')
        print("Created rooms collection indexes")
        
        # Messages collection indexes
        messages_collection.create_index('room_id')
        messages_collection.create_index('sender_id')
        messages_collection.create_index('timestamp')
        messages_collection.create_index([('room_id', 1), ('timestamp', -1)])
        print("Created messages collection indexes")
        
    except Exception as e:
        print(f"Error creating indexes: {e}")

def clear_all_data():
    """Clear all existing data (use with caution!)"""
    print("Clearing all existing data...")
    
    confirmation = input("Are you sure you want to delete all data? Type 'yes' to confirm: ")
    if confirmation.lower() == 'yes':
        users_collection.delete_many({})
        rooms_collection.delete_many({})
        messages_collection.delete_many({})
        print("All data cleared successfully!")
    else:
        print("Data clearing cancelled.")

def main():
    """Main function to run the seeder"""
    print("=== Chat Application Database Seeder ===")
    print("1. Create sample users")
    print("2. Create sample rooms")
    print("3. Create sample messages")
    print("4. Create database indexes")
    print("5. Seed all data (users + rooms + messages + indexes)")
    print("6. Clear all data (DANGER!)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == '1':
        create_sample_users()
    elif choice == '2':
        create_sample_rooms()
    elif choice == '3':
        create_sample_messages()
    elif choice == '4':
        create_indexes()
    elif choice == '5':
        create_sample_users()
        create_sample_rooms()
        create_sample_messages()
        create_indexes()
        print("\n✅ All sample data created successfully!")
        print("\nSample login credentials:")
        print("Username: admin, Password: admin123")
        print("Username: john_doe, Password: password123")
        print("Username: jane_smith, Password: password123")
        print("Username: bob_wilson, Password: password123")
    elif choice == '6':
        clear_all_data()
    elif choice == '0':
        print("Goodbye!")
        return
    else:
        print("Invalid choice. Please try again.")
    
    # Ask if user wants to continue
    if choice != '0':
        continue_choice = input("\nDo you want to perform another action? (y/n): ").strip().lower()
        if continue_choice == 'y':
            main()

if __name__ == '__main__':
    main()