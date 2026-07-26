import datetime
from database.db import get_db
from services.email_svc import send_email

def run_reminder_check():
    """检查所有活跃提醒，发送到期提醒"""
    conn = get_db()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取所有需要提醒的记录（next_remind_at <= now 且 is_active = 1）
    reminders = conn.execute(
        """SELECT r.*, c.name as category_name, c.table_name
           FROM reminders r
           JOIN categories c ON r.category_id = c.id
           WHERE r.is_active = 1 AND r.next_remind_at <= ?""",
        (now,)
    ).fetchall()

    for reminder in reminders:
        reminder = dict(reminder)
        try:
            # 获取记录详情
            record = conn.execute(
                f"SELECT * FROM {reminder['table_name']} WHERE id = ?",
                (reminder['record_id'],)
            ).fetchone()

            if not record:
                # 记录已被删除，清理提醒
                conn.execute("DELETE FROM reminders WHERE id = ?", (reminder['id'],))
                continue

            record = dict(record)
            # 构建提醒内容
            record_name = record.get(list(record.keys())[1] if len(record.keys()) > 1 else 'id', str(reminder['record_id']))
            subject = f"【数据管理提醒】{reminder['category_name']} - {record_name}"
            body = f"管理项：{reminder['category_name']}\n"
            body += f"记录：{record_name}\n"
            if reminder.get('note'):
                body += f"备注：{reminder['note']}\n"
            body += f"\n---\n此提醒由数据管理系统自动发送"

            # 发送邮件
            email_sent, _ = send_email(subject, body)
            status = 'sent' if email_sent else 'failed'

        except Exception as e:
            status = 'failed'
            error_msg = str(e)
        else:
            error_msg = ''

        # 记录日志
        conn.execute(
            """INSERT INTO reminder_logs (reminder_id, category_id, record_id, status, error_msg)
               VALUES (?, ?, ?, ?, ?)""",
            (reminder['id'], reminder['category_id'], reminder['record_id'], status, error_msg)
        )

        # 更新提醒状态
        if reminder['remind_type'] == 'once':
            # 一次性提醒：停用
            conn.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder['id'],))
        elif reminder['remind_type'] == 'multi':
            # 多次提醒：增加计数，计算下次提醒时间
            new_count = reminder['current_count'] + 1
            if new_count >= reminder['total_count']:
                conn.execute("UPDATE reminders SET is_active = 0, current_count = ? WHERE id = ?",
                           (new_count, reminder['id']))
            else:
                next_time = (datetime.datetime.now() + datetime.timedelta(days=reminder['interval_days'])).strftime('%Y-%m-%d %H:%M:%S')
                conn.execute(
                    "UPDATE reminders SET current_count = ?, next_remind_at = ? WHERE id = ?",
                    (new_count, next_time, reminder['id'])
                )
        elif reminder['remind_type'] == 'recurring':
            # 循环提醒：计算下次提醒时间
            next_time = (datetime.datetime.now() + datetime.timedelta(days=reminder['interval_days'])).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE reminders SET next_remind_at = ? WHERE id = ?", (next_time, reminder['id']))

    conn.commit()
    conn.close()
