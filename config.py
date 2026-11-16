import os
from datetime import timedelta

class Config:
    """Application Configuration Settings"""
    # General Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cryptix-super-secret-key-phase1-dev')

    # MySQL Database Settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'cryptix_db')

    # JWT Authentication Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-cryptix-auth-secret-key-2026')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 8
    JWT_COOKIE_NAME = 'cryptix_token'
    JWT_COOKIE_SECURE = False  # Set to True when running under HTTPS
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'

    # Admin Seed Credentials
    ADMIN_DEFAULT_NAME = 'System Administrator'
    ADMIN_DEFAULT_EMAIL = 'admin@cryptix.com'
    ADMIN_DEFAULT_PASSWORD = 'AdminPassword123!'
