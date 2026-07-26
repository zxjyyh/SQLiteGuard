import sqlite3
import os

def get_db_path():
    from config import Config
    db_path = Config.DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT 'Folder',
            has_reminder INTEGER DEFAULT 0,
            table_name TEXT UNIQUE NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS category_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            field_key TEXT NOT NULL,
            field_label TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            record_id INTEGER NOT NULL,
            remind_type TEXT NOT NULL,
            remind_at TEXT,
            interval_days INTEGER,
            total_count INTEGER,
            current_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            next_remind_at TEXT,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reminder_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            record_id INTEGER NOT NULL,
            sent_at TEXT DEFAULT (datetime('now','localtime')),
            status TEXT DEFAULT 'sent',
            error_msg TEXT DEFAULT '',
            FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS smtp_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            host TEXT DEFAULT '',
            port INTEGER DEFAULT 587,
            username TEXT DEFAULT '',
            password TEXT DEFAULT '',
            from_addr TEXT DEFAULT '',
            recipient_email TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
    ''')

    # 站点配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_config (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO site_config (key, value) VALUES ('site_title', '个人数据管家')")

    # 迁移：为旧版 smtp_config 补充 recipient_email 列
    try:
        cursor.execute("ALTER TABLE smtp_config ADD COLUMN recipient_email TEXT DEFAULT ''")
    except:
        pass

    conn.commit()
    conn.close()

def seed_default_user():
    import bcrypt
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        pwd = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ('admin', pwd.decode('utf-8'))
        )
        conn.commit()
    conn.close()

def seed_demo_data():
    """初始化示例管理项和字段（仅在数据库为空时执行）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    _create_demo_category(conn, '账号信息', '管理各类网站和应用的账号密码', 'Lock', True, [
        ('f_platform', '平台名称'), ('f_url', '网址'), ('f_account', '账号'),
        ('f_password', '密码'), ('f_note', '备注')
    ])
    _create_demo_category(conn, '备忘录', '日常备忘事项和待办', 'Memo', True, [
        ('f_title', '标题'), ('f_content', '内容')
    ])
    _create_demo_category(conn, '网址收藏', '常用网站和书签收藏', 'Link', False, [
        ('f_name', '网站名称'), ('f_url', '网址'), ('f_desc', '描述'), ('f_tag', '标签')
    ])
    _create_demo_category(conn, '联系人', '常用联系人和通讯录', 'User', False, [
        ('f_name', '姓名'), ('f_phone', '电话'), ('f_email', '邮箱'), ('f_company', '公司'), ('f_note', '备注')
    ])
    conn.commit()
    conn.close()

def _create_demo_category(conn, name, desc, icon, has_reminder, fields):
    import hashlib
    hash_suffix = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
    table_name = f"cat_{hash_suffix}"
    cursor = conn.execute(
        "INSERT INTO categories (name, description, icon, has_reminder, table_name) VALUES (?, ?, ?, ?, ?)",
        (name, desc, icon, 1 if has_reminder else 0, table_name)
    )
    cat_id = cursor.lastrowid
    col_defs = []
    for i, (key, label) in enumerate(fields):
        conn.execute(
            "INSERT INTO category_fields (category_id, field_key, field_label, sort_order) VALUES (?, ?, ?, ?)",
            (cat_id, key, label, i)
        )
        col_defs.append(f"{key} TEXT DEFAULT ''")
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {', '.join(col_defs)},
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """
    conn.execute(create_sql)
