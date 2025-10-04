"""
Configuration file for the chat application
Contains all application settings and configurations
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # MongoDB settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/chat_app')
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-jwt-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    # Application settings
    MAX_MESSAGE_LENGTH = 1000
    MAX_ROOM_NAME_LENGTH = 50
    MAX_USERNAME_LENGTH = 30
    MAX_DISPLAY_NAME_LENGTH = 50
    
    # File upload settings (for future implementation)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Rate limiting settings
    RATE_LIMIT_MESSAGES_PER_MINUTE = 30
    RATE_LIMIT_ROOMS_PER_HOUR = 5
    
    # Database settings
    DB_CONNECTION_TIMEOUT = 5000  # milliseconds
    DB_MAX_POOL_SIZE = 50

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/chat_app_test'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}