"""
Authentication utilities for JWT token management
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from database import UserModel
import logging

logger = logging.getLogger(__name__)

# Secret key for JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, password_hash):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id, email, role):
    """Generate a JWT token for a user."""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token):
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'status': 'error', 'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'status': 'error', 'error': 'Token is missing'}), 401
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            return jsonify({'status': 'error', 'error': 'Invalid or expired token'}), 401
        
        # Get user from database
        user = UserModel.find_by_id(payload['user_id'])
        if not user:
            return jsonify({'status': 'error', 'error': 'User not found'}), 401
        
        # Add user to request context
        request.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        
        if user['role'] != 'admin':
            return jsonify({'status': 'error', 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated


def candidate_required(f):
    """Decorator to require candidate role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        
        if user['role'] != 'candidate':
            return jsonify({'status': 'error', 'error': 'Candidate access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

