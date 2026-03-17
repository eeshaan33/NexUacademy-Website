import asyncio
import logging
from datetime import datetime, timezone, timedelta
from config.database import get_database
from services.push_service import send_push_notification

logger = logging.getLogger(__name__)

REMINDER_INTERVALS = [
    {"minutes": 60, "label": "1 hour"},
    {"minutes": 15, "label": "15 minutes"},
]


async def check_and_send_reminders():
    """Check for upcoming tests and send reminders at 1hr and 15min before."""
    db = get_database()
    now = datetime.now(timezone.utc)

    for interval in REMINDER_INTERVALS:
        window_start = now + timedelta(minutes=interval["minutes"] - 1)
        window_end = now + timedelta(minutes=interval["minutes"] + 1)

        tests = await db.teacher_tests.find({
            "status": "scheduled",
            "scheduled_date_time": {
                "$gte": window_start.isoformat(),
                "$lte": window_end.isoformat(),
            },
        }).to_list(length=None)

        for test in tests:
            reminder_key = f"reminder_{interval['minutes']}_{test['test_id']}"

            already_sent = await db.sent_reminders.find_one({"key": reminder_key})
            if already_sent:
                continue

            batches = test.get("assigned_batches", [])
            students = await db.users.find({
                "role": "student",
                "batch_id": {"$in": batches},
            }).to_list(length=None)

            push_count = 0
            for student in students:
                # In-app notification
                await db.notifications.insert_one({
                    "user_id": student["user_id"],
                    "type": "test",
                    "title": f"Test in {interval['label']}!",
                    "message": f"{test['test_name']} starts in {interval['label']}. Get ready!",
                    "data": {"test_id": test["test_id"]},
                    "is_read": False,
                    "created_at": now.isoformat(),
                })

                # Push notification
                sub = student.get("push_subscription")
                if sub and student.get("notifications_enabled"):
                    ok = await send_push_notification(sub, {
                        "title": f"Test in {interval['label']}!",
                        "body": f"{test['test_name']} starts in {interval['label']}. Get ready!",
                        "data": {"url": "/assigned-tests", "type": "test"},
                    })
                    if ok:
                        push_count += 1

            # Mark reminder as sent
            await db.sent_reminders.insert_one({
                "key": reminder_key,
                "test_id": test["test_id"],
                "interval_minutes": interval["minutes"],
                "sent_at": now.isoformat(),
                "students_notified": len(students),
                "push_sent": push_count,
            })

            logger.info(
                f"Reminder ({interval['label']}): {test['test_name']} → "
                f"{len(students)} in-app, {push_count} push"
            )


async def reminder_loop():
    """Background loop that checks for reminders every 60 seconds."""
    logger.info("Test reminder scheduler started")
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            logger.error(f"Reminder check error: {e}")
        await asyncio.sleep(60)
