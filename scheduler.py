# scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from scheduler_jobs import hourly_pattern_job, daily_pattern_job

scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Colombo"))

def start_scheduler():
    # Hourly (Mon–Fri, 09:30–14:30)
    scheduler.add_job(
        hourly_pattern_job,
        CronTrigger(day_of_week="mon-fri", hour="9-14", minute="0,30")
    )

    # Daily (Mon–Fri at 14:30)
    scheduler.add_job(
        daily_pattern_job,
        CronTrigger(day_of_week="mon-fri", hour=14, minute=30)
    )

    scheduler.start()
