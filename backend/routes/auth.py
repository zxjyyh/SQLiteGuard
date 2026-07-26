import bcrypt
import jwt
import datetime
import random
import string
from flask import Blueprint, request, g
from database.db import get_db
from config import Config
from utils.response import success, fail
from utils.auth import login_required
from services.email_svc import send_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return fail('用户名或密码错误')

    token = jwt.encode({
        'user_id': user['id'],
        'username': user['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.JWT_SECRET, algorithm='HS256')

    return success({'token': token, 'username': user['username']})

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    return success({'username': g.username, 'userId': g.user_id})

@auth_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    data = request.get_json()
    old_pwd = data.get('oldPassword', '')
    new_pwd = data.get('newPassword', '')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()

    if not bcrypt.checkpw(old_pwd.encode('utf-8'), user['password_hash'].encode('utf-8')):
        conn.close()
        return fail('原密码错误')

    new_hash = bcrypt.hashpw(new_pwd.encode('utf-8'), bcrypt.gensalt())
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash.decode('utf-8'), g.user_id))
    conn.commit()
    conn.close()

    return success(message='密码修改成功')

@auth_bp.route('/username', methods=['PUT'])
@login_required
def change_username():
    data = request.get_json()
    new_username = data.get('username', '').strip()
    if not new_username:
        return fail('用户名不能为空')
    if len(new_username) > 50:
        return fail('用户名过长')

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, g.user_id)).fetchone()
    if existing:
        conn.close()
        return fail('用户名已被占用')

    conn.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, g.user_id))
    conn.commit()
    conn.close()

    # 生成新token
    token = jwt.encode({
        'user_id': g.user_id,
        'username': new_username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.JWT_SECRET, algorithm='HS256')

    return success({'token': token, 'username': new_username}, '用户名修改成功')

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """忘记密码：发送随机临时密码到配置的邮箱"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    if not username:
        return fail('请输入用户名')

    conn = get_db()
    smtp = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
    if not smtp or not smtp['host'] or not smtp['username']:
        conn.close()
        return fail('邮件服务未配置，请先联系管理员在系统设置中配置SMTP')

    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return fail('用户名不存在')

    # 生成8位随机密码
    chars = string.ascii_letters + string.digits
    temp_pwd = ''.join(random.choices(chars, k=8))

    # 只重置该用户密码
    new_hash = bcrypt.hashpw(temp_pwd.encode('utf-8'), bcrypt.gensalt())
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash.decode('utf-8'), username))
    conn.commit()
    conn.close()

    # 发送邮件
    ok, error = send_email(
        '【个人数据管家】密码找回',
        f'您好 {username}，\n\n您的个人数据管家临时密码为：{temp_pwd}\n\n请使用此密码登录后尽快修改密码。\n\n---\n此邮件由系统自动发送'
    )
    if ok:
        return success(message='临时密码已发送，请检查收件箱')
    else:
        return fail(f'邮件发送失败: {error}')

@auth_bp.route('/smtp-info', methods=['GET'])
def get_smtp_info():
    """获取邮件配置信息（公开：返回是否已配置和邮箱掩码，不泄漏完整邮箱）"""
    conn = get_db()
    smtp = conn.execute("SELECT username, host, recipient_email FROM smtp_config WHERE id = 1").fetchone()
    conn.close()
    configured = bool(smtp and smtp['host'] and smtp['username'])
    email_hint = ''
    if configured:
        raw = smtp['recipient_email'] or smtp['username']
        at_idx = raw.find('@')
        email_hint = raw[:2] + '***' + raw[at_idx:] if at_idx > 0 else raw[:2] + '***'
    return success({
        'configured': configured,
        'email': email_hint
    })
