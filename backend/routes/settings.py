import os
from flask import Blueprint, request, g
from database.db import get_db
from utils.response import success, fail
from utils.auth import login_required
from services.email_svc import send_email

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/site-title', methods=['GET'])
def public_site_title():
    """公开站点标题（无需登录）"""
    conn = get_db()
    row = conn.execute("SELECT value FROM site_config WHERE key='site_title'").fetchone()
    conn.close()
    return success({'title': row['value'] if row else '个人数据管家'})

@settings_bp.route('/smtp', methods=['GET'])
@login_required
def get_smtp():
    conn = get_db()
    row = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
    conn.close()
    if row:
        data = dict(row)
        if data.get('password'):
            data['password'] = '******'
        return success(data)
    return success({
        'host': '', 'port': 587, 'username': '', 'password': '',
        'from_addr': '', 'recipient_email': ''
    })

@settings_bp.route('/smtp', methods=['PUT'])
@login_required
def update_smtp():
    data = request.get_json()
    host = data.get('host', '')
    port = data.get('port', 587)
    username = data.get('username', '')
    password = data.get('password', '')
    from_addr = data.get('from_addr', username)
    recipient_email = data.get('recipient_email', username)

    conn = get_db()
    existing = conn.execute("SELECT id FROM smtp_config WHERE id = 1").fetchone()
    if existing:
        if password == '******':
            conn.execute(
                """UPDATE smtp_config SET host=?, port=?, username=?, from_addr=?, recipient_email=?,
                   updated_at=datetime('now','localtime') WHERE id=1""",
                (host, port, username, from_addr, recipient_email)
            )
        else:
            conn.execute(
                """UPDATE smtp_config SET host=?, port=?, username=?, password=?, from_addr=?, recipient_email=?,
                   updated_at=datetime('now','localtime') WHERE id=1""",
                (host, port, username, password, from_addr, recipient_email)
            )
    else:
        conn.execute(
            "INSERT INTO smtp_config (id, host, port, username, password, from_addr, recipient_email) VALUES (1, ?, ?, ?, ?, ?, ?)",
            (host, port, username, password, from_addr, recipient_email)
        )
    conn.commit()
    conn.close()
    return success(message='保存成功')

@settings_bp.route('/smtp/test', methods=['POST'])
@login_required
def test_smtp():
    """发送测试邮件到收件邮箱"""
    ok, error = send_email(
        '【个人数据管家】测试邮件',
        '您好，\n\n这是一封来自个人数据管家的测试邮件。\n\n如果您收到此邮件，说明邮件服务配置正确，提醒和密码找回功能可以正常使用。\n\n---\n此邮件由系统自动发送'
    )
    if ok:
        return success(message='测试邮件已发送，请检查收件箱')
    else:
        return fail(f'发送失败: {error}')

@settings_bp.route('/site', methods=['GET'])
@login_required
def get_site_config():
    conn = get_db()
    rows = conn.execute("SELECT * FROM site_config").fetchall()
    conn.close()
    config = {r['key']: r['value'] for r in rows}
    return success(config)

@settings_bp.route('/site', methods=['PUT'])
@login_required
def update_site_config():
    data = request.get_json()
    site_title = data.get('site_title', '').strip()
    if not site_title:
        return fail('标题不能为空')
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO site_config (key, value) VALUES ('site_title', ?)", (site_title,))
    conn.commit()
    conn.close()
    return success(message='保存成功')
