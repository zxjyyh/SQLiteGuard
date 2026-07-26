from flask import Blueprint, request, g
from database.db import get_db
from utils.response import success, fail, paginated
from utils.auth import login_required
from services.reminder_svc import run_reminder_check

reminder_bp = Blueprint('reminder', __name__)

@reminder_bp.route('/logs', methods=['GET'])
@login_required
def list_logs():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    category_id = request.args.get('categoryId', type=int)
    offset = (page - 1) * page_size

    conn = get_db()
    where = ""
    params = []
    if category_id:
        where = "WHERE rl.category_id = ?"
        params = [category_id]

    total = conn.execute(f"SELECT COUNT(*) FROM reminder_logs rl {where}", params).fetchone()[0]
    rows = conn.execute(
        f"""SELECT rl.*, c.name as category_name, r.remind_type, r.note
            FROM reminder_logs rl
            LEFT JOIN categories c ON rl.category_id = c.id
            LEFT JOIN reminders r ON rl.reminder_id = r.id
            {where}
            ORDER BY rl.sent_at DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()
    conn.close()
    return paginated([dict(r) for r in rows], total, page, page_size)

@reminder_bp.route('/test', methods=['POST'])
@login_required
def trigger_check():
    """手动触发提醒检查"""
    try:
        run_reminder_check()
        return success(message='提醒检查已执行')
    except Exception as e:
        return fail(f'执行失败: {str(e)}')

@reminder_bp.route('/stats', methods=['GET'])
@login_required
def reminder_stats():
    """获取所有提醒统计"""
    conn = get_db()
    now = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 已过期（next_remind_at < now)
    expired = conn.execute(
        "SELECT COUNT(*) FROM reminders WHERE is_active = 1 AND next_remind_at < ?", (now,)
    ).fetchone()[0]
    # 全部活跃提醒
    total_active = conn.execute("SELECT COUNT(*) FROM reminders WHERE is_active = 1").fetchone()[0]
    conn.close()
    return success({'expired': expired, 'totalActive': total_active})

@reminder_bp.route('/pending', methods=['GET'])
@login_required
def pending_reminders():
    """获取所有待提醒事项，按下次提醒时间排序"""
    conn = get_db()
    now = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rows = conn.execute(
        """SELECT r.id, r.record_id, r.category_id, r.remind_type, r.next_remind_at,
                  r.interval_days, r.current_count, r.total_count, r.note, r.is_active,
                  c.name as category_name, c.table_name
           FROM reminders r
           LEFT JOIN categories c ON r.category_id = c.id
           WHERE r.is_active = 1
           ORDER BY r.next_remind_at ASC"""
    ).fetchall()

    pending = []
    for row in rows:
        item = dict(row)
        try:
            record = conn.execute(
                f"SELECT * FROM {item['table_name']} WHERE id = ?", (item['record_id'],)
            ).fetchone()
            if record:
                first_key = conn.execute(
                    "SELECT field_key FROM category_fields WHERE category_id = ? ORDER BY sort_order LIMIT 1",
                    (item['category_id'],)
                ).fetchone()['field_key']
                item['record_title'] = dict(record).get(first_key, '-')
        except:
            item['record_title'] = '-'
        pending.append(item)

    conn.close()
    return success(pending)
