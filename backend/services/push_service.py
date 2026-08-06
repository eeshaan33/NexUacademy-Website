"""In-app notifications (+ optional web-push) for batch students.

Web-push is a best-effort optional layer. In-app notifications are written to
`notifications` for every student in the assigned batch(es), regardless of
whether they have a push subscription.
"""
import logging
from typing import Iterable

from config.database import get_pool
from services.pg_utils import short_id, now_iso

logger = logging.getLogger(__name__)


async def _notify_batch_students(batches: Iterable[str], title: str, message: str,
                                 ntype: str, data: dict):
    if not batches:
        return 0
    pool = get_pool()
    async with pool.acquire() as conn:
        students = await conn.fetch(
            "SELECT id FROM profiles WHERE role = 'student' AND batch_id = ANY($1::text[])",
            list(batches),
        )
        if not students:
            return 0
        # Bulk-insert notifications
        rows_data = [
            (short_id("notif"), s["id"], ntype, title, message, data)
            for s in students
        ]
        await conn.executemany(
            """
            INSERT INTO notifications (notification_id, user_id, type, title, message, data)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            [(r[0], r[1], r[2], r[3], r[4], __import__("json").dumps(r[5])) for r in rows_data],
        )
    logger.info(f"Notified {len(students)} students (in-app) about {ntype}: {title}")
    return len(students)


async def notify_students_about_class(class_data: dict):
    batches = class_data.get("assigned_batches") or []
    return await _notify_batch_students(
        batches,
        title=class_data.get("title", "New Class Scheduled"),
        message=f"{class_data.get('subject','')}",
        ntype="class",
        data={"class_id": class_data.get("class_id"), "url": "/classes"},
    )


async def notify_students_about_test(test_data: dict):
    batches = test_data.get("assigned_batches") or []
    return await _notify_batch_students(
        batches,
        title=f"New Test: {test_data.get('test_name','')}",
        message=f"{test_data.get('subject','')}",
        ntype="test",
        data={"test_id": test_data.get("test_id"), "url": "/assigned-tests"},
    )


async def notify_students_about_announcement(a: dict):
    batches = a.get("assigned_batches") or []
    return await _notify_batch_students(
        batches,
        title=f"📢 {a.get('title','Announcement')}",
        message=a.get("message", ""),
        ntype="announcement",
        data={"announcement_id": a.get("announcement_id")},
    )
