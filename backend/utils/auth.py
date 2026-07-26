import jwt
from functools import wraps
from flask import request, g
from config import Config
from database.db import get_db
from utils.response import fail

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return fail('未登录', -2)
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            g.user_id = payload['user_id']
            g.username = payload['username']
        except jwt.ExpiredSignatureError:
            return fail('登录已过期', -2)
        except jwt.InvalidTokenError:
            return fail('无效的令牌', -2)
        return f(*args, **kwargs)
    return decorated
