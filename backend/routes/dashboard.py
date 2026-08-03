from flask import Blueprint, g
from database.db import get_db
from utils.response import success
from utils.auth import login_required
import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()

    stats = []
    for cat in categories:
        cat = dict(cat)
        try:
            total = conn.execute(f"SELECT COUNT(*) FROM {cat['table_name']}").fetchone()[0]
        except:
            total = 0

        # 活跃提醒数
        active_reminders = conn.execute(
            "SELECT COUNT(*) FROM reminders WHERE category_id = ? AND is_active = 1",
            (cat['id'],)
        ).fetchone()[0]

        stats.append({
            'id': cat['id'],
            'name': cat['name'],
            'icon': cat['icon'],
            'total': total,
            'activeReminders': active_reminders
        })

    # 全局提醒统计
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    pending_count = conn.execute(
        "SELECT COUNT(*) FROM reminders WHERE is_active = 1 AND next_remind_at > ?",
        (now,)
    ).fetchone()[0]
    # 已到期待处理的提醒（铃铛角标用）
    overdue_count = conn.execute(
        "SELECT COUNT(*) FROM reminders WHERE is_active = 1 AND next_remind_at <= ?",
        (now,)
    ).fetchone()[0]

    conn.close()
    return success({
        'categories': stats,
        'pendingCount': pending_count,
        'overdueCount': overdue_count
    })
