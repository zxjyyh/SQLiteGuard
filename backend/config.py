import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 数据目录：所有持久化文件（数据库、日志等）都在此目录下
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    LOG_DIR = os.path.join(DATA_DIR, 'logs')

    # 数据库路径
    DB_PATH = os.getenv('DB_PATH', os.path.join(DATA_DIR, 'data.db'))

    # JWT
    # JWT: 缺失密钥时生成随机密钥（生产环境务必通过环境变量设置固定值）
    _jwt = os.getenv('JWT_SECRET', '')
    if not _jwt:
        import secrets
        _jwt = secrets.token_hex(32)
    JWT_SECRET = _jwt
    PORT = int(os.getenv('PORT', 5000))

    # SMTP（从数据库读取，env 仅作备用）
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    SMTP_FROM = os.getenv('SMTP_FROM', '')

# 确保必要目录存在
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.LOG_DIR, exist_ok=True)
