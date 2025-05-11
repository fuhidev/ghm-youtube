# modules/scheduler.py
# Đặt lịch thực thi tác vụ
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

scheduler = BackgroundScheduler()

def schedule_task(func, run_time, *args, **kwargs):
    scheduler.add_job(func, 'date', run_date=run_time, args=args, kwargs=kwargs)
    if not scheduler.running:
        scheduler.start()
