import os
import json
import logging
from pywebpush import webpush, WebPushException
from config.database import get_database

logger = logging.getLogger(__name__)

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_MAILTO = os.environ.get("VAPID_MAILTO", "mailto:admin@nexuacademy.com")


async def send_push_notification(subscription_info: dict, payload: dict) -> bool:
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_MAILTO},
        )
        return True
    except WebPushException as e:
        logger.error(f"Push notification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Push error: {e}")
        return False


async def notify_students_about_class(class_data: dict):
    db = get_database()
    batches = class_data.get("assigned_batches", [])
    if not batches:
        return 0
    # ALL students in batch get an in-app notification (regardless of push_subscription)
    students = await db.users.find({
        "role": "student",
        "batch_id": {"$in": batches},
    }).to_list(length=None)

    payload = {
        "title": "New Class Scheduled",
        "body": f"{class_data['title']} - {class_data['subject']}",
        "data": {"url": "/classes", "type": "class"},
    }

    push_count = 0
    for student in students:
        # Only send web-push to those that have a subscription
        sub = student.get("push_subscription")
        if sub and student.get("notifications_enabled", True):
            ok = await send_push_notification(sub, payload)
            if ok:
                push_count += 1
        await db.notifications.insert_one({
            "notification_id": f"notif_{__import__('uuid').uuid4().hex[:12]}",
            "user_id": student["user_id"],
            "type": "class",
            "title": "New Class Scheduled",
            "message": f"{class_data['title']} - {class_data['subject']}",
            "data": {"class_id": class_data.get("class_id")},
            "is_read": False,
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
    logger.info(f"Notified {push_count} students (push), {len(students)} in-app, about class {class_data.get('class_id')}")
    return len(students)


async def notify_students_about_test(test_data: dict):
    db = get_database()
    batches = test_data.get("assigned_batches", [])
    if not batches:
        return 0
    # ALL students in batch get an in-app notification
    students = await db.users.find({
        "role": "student",
        "batch_id": {"$in": batches},
    }).to_list(length=None)

    payload = {
        "title": "New Test Assigned",
        "body": f"{test_data['test_name']} - {test_data['subject']}",
        "data": {"url": "/assigned-tests", "type": "test"},
    }

    push_count = 0
    for student in students:
        sub = student.get("push_subscription")
        if sub and student.get("notifications_enabled", True):
            ok = await send_push_notification(sub, payload)
            if ok:
                push_count += 1
        await db.notifications.insert_one({
            "notification_id": f"notif_{__import__('uuid').uuid4().hex[:12]}",
            "user_id": student["user_id"],
            "type": "test",
            "title": "New Test Assigned",
            "message": f"{test_data['test_name']} - {test_data['subject']}",
            "data": {"test_id": test_data.get("test_id")},
            "is_read": False,
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
    logger.info(f"Notified {push_count} students (push), {len(students)} in-app, about test {test_data.get('test_id')}")
    return len(students)
