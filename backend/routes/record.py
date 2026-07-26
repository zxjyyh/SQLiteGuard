import re
from flask import Blueprint, request, g
from database.db import get_db
from utils.response import success, fail, paginated
from utils.auth import login_required

record_bp = Blueprint('record', __name__)

SAFE_TABLE_RE = re.compile(r'^cat_[a-f0-9]{8}$')

def _validate_table(name):
    """验证表名是否符合 cat_xxxxxxxx 格式，防止SQL注入"""
    if not SAFE_TABLE_RE.match(name):
        return False
    return True

@record_bp.route('/<int:category_id>', methods=['GET'])
@login_required
def list_records(category_id):
    """获取某个管理项下的所有记录"""
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * page_size

    table_name = cat['table_name']
    if not _validate_table(table_name):
        conn.close()
        return fail('系统错误')
    field_keys = [f['field_key'] for f in fields]

    where_clause = ""
    params = []
    if keyword and field_keys:
        like_conditions = " OR ".join([f"{fk} LIKE ?" for fk in field_keys])
        where_clause = f"WHERE {like_conditions}"
        params = [f"%{keyword}%"] * len(field_keys)

    # 总数
    count_sql = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # 数据
    cols = ', '.join(field_keys) if field_keys else '*'
    data_sql = f"SELECT id, {cols}, created_at, updated_at FROM {table_name} {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    rows = conn.execute(data_sql, params + [page_size, offset]).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        # 检查是否有提醒
        reminder = conn.execute(
            "SELECT * FROM reminders WHERE category_id = ? AND record_id = ? AND is_active = 1",
            (category_id, item['id'])
        ).fetchone()
        item['_hasReminder'] = reminder is not None
        item['_reminder'] = dict(reminder) if reminder else None
        result.append(item)

    conn.close()
    return paginated(result, total, page, page_size)

@record_bp.route('/<int:category_id>', methods=['POST'])
@login_required
def create_record(category_id):
    """创建记录"""
    data = request.get_json()
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    table_name = cat['table_name']
    if not _validate_table(table_name):
        conn.close()
        return fail('系统错误')
    field_keys = [f['field_key'] for f in fields]

    # 构建INSERT
    values = {}
    for fk in field_keys:
        values[fk] = data.get(fk, '')

    cols = ', '.join(values.keys())
    placeholders = ', '.join(['?'] * len(values))
    sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

    cursor = conn.execute(sql, list(values.values()))
    record_id = cursor.lastrowid

    # 处理提醒设置
    reminder_data = data.get('_reminder')
    if reminder_data and reminder_data.get('enabled'):
        _save_reminder(conn, category_id, record_id, reminder_data)

    conn.commit()
    conn.close()
    return success({'id': record_id}, '创建成功')

@record_bp.route('/<int:category_id>/<int:record_id>', methods=['GET'])
@login_required
def get_record(category_id, record_id):
    """获取单条记录详情"""
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    table_name = cat['table_name']
    if not _validate_table(table_name):
        conn.close()
        return fail('系统错误')
    row = conn.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,)).fetchone()
    if not row:
        conn.close()
        return fail('记录不存在')

    result = dict(row)

    # 获取提醒信息
    reminder = conn.execute(
        "SELECT * FROM reminders WHERE category_id = ? AND record_id = ?",
        (category_id, record_id)
    ).fetchone()
    result['_reminder'] = dict(reminder) if reminder else None

    conn.close()
    return success(result)

@record_bp.route('/<int:category_id>/<int:record_id>', methods=['PUT'])
@login_required
def update_record(category_id, record_id):
    """更新记录"""
    data = request.get_json()
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    fields = conn.execute(
        "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order",
        (category_id,)
    ).fetchall()

    table_name = cat['table_name']
    if not _validate_table(table_name):
        conn.close()
        return fail('系统错误')
    field_keys = [f['field_key'] for f in fields]

    set_parts = []
    values = []
    for fk in field_keys:
        if fk in data:
            set_parts.append(f"{fk} = ?")
            values.append(data[fk])

    if not set_parts:
        conn.close()
        return fail('没有需要更新的字段')

    set_parts.append("updated_at = datetime('now','localtime')")
    sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE id = ?"
    values.append(record_id)
    conn.execute(sql, values)

    # 处理提醒设置
    reminder_data = data.get('_reminder')
    if reminder_data is not None:
        # 先删除旧提醒
        conn.execute("DELETE FROM reminders WHERE category_id = ? AND record_id = ?", (category_id, record_id))
        if reminder_data.get('enabled'):
            _save_reminder(conn, category_id, record_id, reminder_data)

    conn.commit()
    conn.close()
    return success(message='更新成功')

@record_bp.route('/<int:category_id>/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(category_id, record_id):
    """删除记录"""
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        conn.close()
        return fail('管理项不存在')

    # 删除提醒
    conn.execute("DELETE FROM reminder_logs WHERE category_id = ? AND record_id = ?", (category_id, record_id))
    conn.execute("DELETE FROM reminders WHERE category_id = ? AND record_id = ?", (category_id, record_id))
    # 删除记录
    conn.execute(f"DELETE FROM {cat['table_name']} WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return success(message='删除成功')

def _save_reminder(conn, category_id, record_id, reminder_data):
    """保存提醒规则"""
    remind_type = reminder_data.get('type', 'once')  # once / multi / recurring
    note = reminder_data.get('note', '')

    if remind_type == 'once':
        remind_at = reminder_data.get('remindAt', '')
        conn.execute(
            """INSERT INTO reminders (category_id, record_id, remind_type, remind_at, next_remind_at, note)
               VALUES (?, ?, 'once', ?, ?, ?)""",
            (category_id, record_id, remind_at, remind_at, note)
        )
    elif remind_type == 'multi':
        interval_days = int(reminder_data.get('intervalDays', 1))
        total_count = int(reminder_data.get('totalCount', 1))
        # 首次提醒时间是当前时间 + interval_days
        from datetime import datetime, timedelta
        first_remind = (datetime.now() + timedelta(days=interval_days)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            """INSERT INTO reminders (category_id, record_id, remind_type, interval_days, total_count,
               current_count, next_remind_at, note)
               VALUES (?, ?, 'multi', ?, ?, 0, ?, ?)""",
            (category_id, record_id, interval_days, total_count, first_remind, note)
        )
    elif remind_type == 'recurring':
        interval_days = int(reminder_data.get('intervalDays', 1))
        from datetime import datetime, timedelta
        first_remind = (datetime.now() + timedelta(days=interval_days)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            """INSERT INTO reminders (category_id, record_id, remind_type, interval_days, is_active,
               next_remind_at, note)
               VALUES (?, ?, 'recurring', ?, 1, ?, ?)""",
            (category_id, record_id, interval_days, first_remind, note)
        )
