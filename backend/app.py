from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from database.db import init_db, seed_default_user, seed_demo_data
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """配置文件日志：输出到 data/logs/app.log，自动轮转（10MB×3个文件）"""
    log_file = os.path.join(Config.LOG_DIR, 'app.log')
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config['SECRET_KEY'] = Config.JWT_SECRET

    # 公开接口（必须在所有其他路由之前注册，避免被 catch-all 拦截）
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    # CORS: 生产环境应通过环境变量 CORS_ORIGINS 指定允许的域名
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # 反向代理适配（绿联 NAS 等通过域名反代访问场景）
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    setup_logging(app)
    app.logger.info('个人数据管家启动中...')

    init_db()
    seed_default_user()
    seed_demo_data()

    from routes.auth import auth_bp
    from routes.category import category_bp
    from routes.record import record_bp
    from routes.reminder import reminder_bp
    from routes.import_data import import_bp
    from routes.settings import settings_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(category_bp, url_prefix='/api/categories')
    app.register_blueprint(record_bp, url_prefix='/api/records')
    app.register_blueprint(reminder_bp, url_prefix='/api/reminders')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # Serve frontend static files in production
    _base = os.path.dirname(os.path.abspath(__file__))
    # 兼容两种部署方式：本地开发（backend/ 子目录）和 Docker（直接同级目录）
    frontend_dist = os.path.join(_base, '..', 'frontend', 'dist')
    if not os.path.isdir(frontend_dist):
        frontend_dist = os.path.join(_base, 'frontend', 'dist')
    if os.path.exists(frontend_dist):
        @app.route('/')
        def serve_index():
            return send_from_directory(frontend_dist, 'index.html')

        @app.route('/assets/<path:path>')
        def serve_assets(path):
            return send_from_directory(frontend_dist, f'assets/{path}')

        # 反向代理调试：记录实际收到的请求
        @app.route('/<path:path>')
        def serve_frontend(path):
            # API 请求全部放过，交给蓝图处理
            if path.startswith('api/'):
                from werkzeug.exceptions import NotFound
                raise NotFound()
            # 打到这说明是反向代理请求——记录实际路径
            from flask import request as _req
            app.logger.info(f'前端路由 path={path!r} full_url={_req.url!r} base_url={_req.base_url!r} script_name={_req.script_root!r}')
            file_path = os.path.join(frontend_dist, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')
    
    from scheduler.scheduler import start_scheduler
    start_scheduler(app)

    app.logger.info('启动完成')
    return app

if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=Config.PORT, debug=debug)
