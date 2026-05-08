"""
apps/access/scheduler.py

Background scheduler for access control periodic tasks.
CNST-004: APScheduler only — no Celery.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def expire_exceptional_permissions() -> int:
    """
    Marks ExceptionalPermissions as 'expired' when their valid_until
    date has passed and their status is still 'approved'.

    Runs every hour via AccessScheduler.

    Returns:
        int: number of permissions updated to 'expired'.
    """
    from django.utils import timezone
    from apps.access.models import ExceptionalPermission

    now = timezone.now()
    updated = ExceptionalPermission.objects.filter(
        status='approved',
        valid_until__lt=now,
    ).update(status='expired')

    if updated:
        logger.info(
            "AccessScheduler: %d ExceptionalPermission(s) marked as expired.", updated)

    return updated


class AccessScheduler:
    """
    Background scheduler for the access app.

    Manages:
    - expire_exceptional_permissions: runs every hour.
    """

    scheduler = None

    @classmethod
    def start(cls) -> None:
        """
        Start the scheduler. Idempotent — does nothing if already running.
        Skips management commands to avoid duplicate scheduler instances.
        """
        import sys
        command = ' '.join(sys.argv)
        skip_commands = (
            'makemigrations', 'migrate', 'sqlmigrate',
            'showmigrations', 'check', 'spectacular', 'shell',
            'collectstatic', 'test',
        )
        if any(cmd in command for cmd in skip_commands):
            logger.info(
                "AccessScheduler: NOT started (management command: %s)", command)
            return

        if cls.scheduler is not None:
            logger.info("AccessScheduler: already running.")
            return

        logger.info("AccessScheduler: starting...")

        cls.scheduler = BackgroundScheduler()
        cls.scheduler.add_job(
            expire_exceptional_permissions,
            trigger=IntervalTrigger(hours=1),
            id='expire_exceptional_permissions',
            name='Expire approved ExceptionalPermissions',
            replace_existing=True,
        )
        cls.scheduler.start()

        logger.info("AccessScheduler: started successfully.")

    @classmethod
    def stop(cls) -> None:
        """
        Stop the scheduler gracefully.
        """
        if cls.scheduler:
            logger.info("AccessScheduler: stopping...")
            cls.scheduler.shutdown()
            cls.scheduler = None
            logger.info("AccessScheduler: stopped.")
