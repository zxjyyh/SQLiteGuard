from apscheduler.schedulers.background import BackgroundScheduler
from services.reminder_svc import run_reminder_check
import atexit

scheduler = BackgroundScheduler()

def start_scheduler(app):
    """启动定时任务：每小时检查一次提醒"""
    scheduler.add_job(
        func=run_reminder_check,
        trigger='interval',
        hours=1,
        id='reminder_check',
        name='检查提醒任务',
        replace_existing=True
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
