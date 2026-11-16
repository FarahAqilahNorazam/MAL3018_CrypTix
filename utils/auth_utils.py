import datetime
from functools import wraps
import bcrypt
import jwt
from flask import request, redirect, url_for, flash, g, make_response
from config import Config

def hash_password(plain_password: str) -> str:
    """
    Hashes plain-text password using BCrypt with automatic salting.
    """
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a BCrypt hash.
    """
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False


def generate_jwt_token(user: dict) -> str:
    """
    Generates a signed JSON Web Token (JWT) encoding user identity and role.
    Includes privacy-preserving masked_ic and tokenized mykad_hash. Raw IC is never included.
    """
    payload = {
        'user_id': user['user_id'],
        'email': user['email'],
        'name': user['name'],
        'role': user['role'],
        'masked_ic': user.get('masked_ic', ''),
        'mykad_hash': user.get('mykad_hash', ''),
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    return token if isinstance(token, str) else token.decode('utf-8')


def decode_jwt_token(token: str):
    """
    Decodes and validates a JWT token. Returns payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user_from_request():
    """
    Extracts the JWT token from HTTP-only cookie (or Authorization header),
    decodes it, and returns the user payload.
    """
    token = request.cookies.get(Config.JWT_COOKIE_NAME)
    if not token:
        # Fallback to Authorization Header if used via API
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]

    if not token:
        return None

    return decode_jwt_token(token)


def login_required(f):
    """
    Decorator: Ensures user has a valid authenticated JWT session.
    Sets g.current_user for the request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_request()
        if not user:
            flash('Your session has expired or is invalid. Please sign in.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator: Ensures authenticated user has the 'Admin' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_request()
        if not user:
            flash('Admin authentication required. Please sign in.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        if user.get('role') != 'Admin':
            flash('Access Denied: You do not have administrator permissions.', 'danger')
            return redirect(url_for('dashboard'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
