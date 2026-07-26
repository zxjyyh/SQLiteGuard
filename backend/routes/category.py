import re
import hashlib
from flask import Blueprint, request, g
from database.db import get_db
from utils.response import success, fail
from utils.auth import login_required

category_bp = Blueprint('category', __name__)

def safe_table_name(name):
    """将中文名称转换为安全的英文表名"""
    import hashlib
    # 简单处理：取中文名的hash作为表名后缀，前缀为cat_
    hash_suffix = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
    return f"cat_{hash_suffix}"

def safe_column_key(label):
    """将字段标签转换为安全的ASCII列名"""
    import unicodedata
    # 尝试提取ASCII字符 + 数字
    ascii_chars = []
    for c in label:
        if c.isascii() and (c.isalnum() or c == '_'):
            ascii_chars.append(c.lower())
        elif c == ' ':
            ascii_chars.append('_')
    result = ''.join(ascii_chars)
    if not result:
        # 纯中文等非ASCII标签，用拼音首字母或直接用f_前缀
        result = 'f_' + hashlib.md5(label.encode('utf-8')).hexdigest()[:6]
    if not result[0].isalpha():
        result = 'f_' + result
    return result[:30]

@category_bp.route('', methods=['GET'])
@login_required
def list_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, (SELECT COUNT(*) FROM category_fields WHERE category_id=c.id) as field_count FROM categories c ORDER BY c.sort_order"
    ).fetchall()
    conn.close()
    return success([dict(r) for r in rows])

@category_bp.route('', methods=['POST'])
@login_required
def create_category():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '')
    icon = data.get('icon', 'Folder')
    has_reminder = 1 if data.get('hasReminder', False) else 0
    fields = data.get('fields', [])  # [{label: "网站名称"}, {label: "账号"}, ...]

    if not name:
        return fail('管理项名称不能为空')
    if not fields:
        return fail('至少需要一个字段')

    table_name = safe_table_name(name)

    conn = get_db()
    # 检查名称是否重复
    existing = conn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
    if existing:
        conn.close()
        return fail('管理项名称已存在')

    try:
        # 插入分类记录
        cursor = conn.execute(
            "INSERT INTO categories (name, description, icon, has_reminder, table_name) VALUES (?, ?, ?, ?, ?)",
            (name, description, icon, has_reminder, table_name)
        )
        category_id = cursor.lastrowid

        # 插入字段定义
        columns_def = []
        for i, field in enumerate(fields):
            label = field.get('label', '').strip()
            if not label:
                continue
            field_key = safe_column_key(label)
            # 确保字段key唯一（同一个category内）
            base_key = field_key
            suffix = 1
            existing_keys = {f[0] for f in columns_def}
            while field_key in existing_keys:
                suffix += 1
                field_key = f"{base_key}_{suffix}"

            conn.execute(
                "INSERT INTO category_fields (category_id, field_key, field_label, sort_order) VALUES (?, ?, ?, ?)",
                (category_id, field_key, label, i)
            )
            columns_def.append((field_key,))

        # 动态创建业务表
        col_sql = ', '.join([f"{col[0]} TEXT DEFAULT ''" for col in columns_def])
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {col_sql},
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """
        conn.execute(create_sql)
        conn.commit()

        result = {
            'id': category_id,
            'name': name,
            'tableName': table_name,
            'fields': [{'id': None, 'fieldKey': col[0], 'fieldLabel': fields[i]['label']} for i, col in enumerate(columns_def)]
        }
        conn.close()
        return success(result, '创建成功')
    except Exception as e:
        conn.rollback()
        conn.close()
        return fail(f'创建失败: {str(e)}')

@category_bp.route('/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    try:
        # 删除动态表
        conn.execute(f"DROP TABLE IF EXISTS {cat['table_name']}")
        # 删除关联的提醒
        conn.execute("DELETE FROM reminder_logs WHERE category_id = ?", (category_id,))
        conn.execute("DELETE FROM reminders WHERE category_id = ?", (category_id,))
        # 删除分类（级联删除字段定义）
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()
        return success(message='删除成功')
    except Exception as e:
        conn.rollback()
        conn.close()
        return fail(f'删除失败: {str(e)}')

@category_bp.route('/<int:category_id>/fields', methods=['GET'])
@login_required
def get_fields(category_id):
    conn = get_db()
    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()
    conn.close()
    return success([dict(f) for f in fields])

@category_bp.route('/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """编辑管理项：修改名称/图标/描述/提醒开关/自定义字段。修改字段会重建表并丢失数据。"""
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '')
    icon = data.get('icon', 'Folder')
    has_reminder = 1 if data.get('hasReminder', False) else 0
    fields = data.get('fields', [])
    dropped = data.get('_fieldsChanged', False)  # 前端告知字段有变化

    if not name:
        return fail('管理项名称不能为空')

    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    existing = conn.execute("SELECT id FROM categories WHERE name = ? AND id != ?", (name, category_id)).fetchone()
    if existing:
        conn.close()
        return fail('管理项名称已存在')

    try:
        # 更新基本信息
        conn.execute(
            "UPDATE categories SET name=?, description=?, icon=?, has_reminder=? WHERE id=?",
            (name, description, icon, has_reminder, category_id)
        )

        if dropped:
            # 获取旧字段
            old_fields = conn.execute(
                "SELECT * FROM category_fields WHERE category_id=? ORDER BY sort_order",
                (category_id,)
            ).fetchall()
            old_table = cat['table_name']

            # 如果字段有变化：备份数据→删旧表→删旧字段→建新表→插新字段→回迁数据
            old_keys = [f['field_key'] for f in old_fields]
            new_fields_list = []
            for i, f in enumerate(fields):
                label = f.get('label', '').strip()
                if not label:
                    continue
                key = safe_column_key(label)
                base = key
                s = 1
                while key in [nf[0] for nf in new_fields_list]:
                    s += 1
                    key = f"{base}_{s}"
                new_fields_list.append((key, label, i))

            if not new_fields_list:
                conn.close()
                return fail('至少需要一个字段')

            # 备份现有数据
            old_rows = []
            try:
                old_rows = conn.execute(f"SELECT * FROM {old_table}").fetchall()
            except:
                pass

            # 删旧表
            conn.execute(f"DROP TABLE IF EXISTS {old_table}")
            # 删旧字段定义
            conn.execute("DELETE FROM category_fields WHERE category_id=?", (category_id,))
            # 插新字段
            for key, label, sort in new_fields_list:
                conn.execute(
                    "INSERT INTO category_fields (category_id, field_key, field_label, sort_order) VALUES (?,?,?,?)",
                    (category_id, key, label, sort)
                )
            # 建新表
            col_sqls = [f"{key} TEXT DEFAULT ''" for key, _, _ in new_fields_list]
            create_sql = f"""
                CREATE TABLE {old_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {', '.join(col_sqls)},
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """
            conn.execute(create_sql)

            # 回迁匹配字段的数据
            new_keys = [key for key, _, _ in new_fields_list]
            common_keys = set(old_keys) & set(new_keys)
            for row in old_rows:
                row_dict = dict(row)
                vals = {k: row_dict.get(k, '') for k in new_keys}
                cols = ', '.join(vals.keys())
                placeholders = ', '.join(['?'] * len(vals))
                conn.execute(f"INSERT INTO {old_table} ({cols}) VALUES ({placeholders})", list(vals.values()))

        conn.commit()
        conn.close()
        return success(message='修改成功')
    except Exception as e:
        conn.rollback()
        conn.close()
        return fail(f'修改失败: {str(e)}')
