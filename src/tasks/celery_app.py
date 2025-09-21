"""
Celery application for background tasks
"""
import os
from celery import Celery
from celery.schedules import crontab

# Create Celery instance
celery_app = Celery(
    "weekly_intel",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["src.tasks.weekly_tasks"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "generate-weekly-report": {
        "task": "src.tasks.weekly_tasks.generate_weekly_report",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Every Monday at 9 AM
        "args": (["AI", "machine learning", "startup", "fintech"],),
    },
    "cleanup-old-articles": {
        "task": "src.tasks.weekly_tasks.cleanup_old_articles",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
        "args": (30,),  # Keep articles for 30 days
    },
}