from functools import wraps
from flask import request, jsonify
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager or admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'message': 'Manager privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    """Decorator to require API key for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != 'traffic-simulation-api-key':
            return jsonify({'success': False, 'message': 'Valid API key required'}), 401
        return f(*args, **kwargs)
    return decorated_function
