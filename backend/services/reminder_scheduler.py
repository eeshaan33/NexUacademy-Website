"""
Unified reminder scheduler for tests AND classes.
Sends reminders 24h, 1h, and 15 minutes before each scheduled event.
Delivers via: In-app notification + Push (Web Push) + Email (Resend).
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone, timedelta

import resend
from config.database import get_database
from services.push_service import send_push_notification

logger = logging.getLogger(__name__)

# Initialise Resend once (safe if key missing – we just skip email)
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

REMINDER_INTERVALS = [
    {"minutes": 24 * 60, "label": "24 hours", "key": "24h"},
    {"minutes": 60,       "label": "1 hour",   "key": "1h"},
    {"minutes": 15,       "label": "15 minutes", "key": "15m"},
]


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            # Normalise trailing Z
            v = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(v)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _render_event_email(student_name: str, event: dict, kind: str, label: str) -> tuple[str, str]:
    """Return (subject, html) for a test or class reminder."""
    title = event.get("test_name") or event.get("title") or "Your event"
    subject_line = {
        "24h": f"Tomorrow: {title}",
        "1h":  f"Starting in 1 hour: {title}",
        "15m": f"Starting in 15 minutes: {title}",
    }.get(event["__interval_key"], f"Reminder: {title}")

    scheduled = _parse_dt(event.get("scheduled_date_time"))
    date_str = scheduled.strftime("%A, %b %d, %Y") if scheduled else "Soon"
    time_str = scheduled.strftime("%I:%M %p UTC") if scheduled else ""

    cta_label = "Start Test" if kind == "test" else "Join Class"
    cta_link = event.get("meeting_link") or os.environ.get("APP_BASE_URL", "#")
    kind_label = "TEST" if kind == "test" else "LIVE CLASS"
    accent = "#f97316" if kind == "test" else "#4f46e5"

    extra_rows = ""
    if kind == "test":
        extra_rows = f"""
          <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>DURATION</td>
              <td style='padding:6px 0;font-weight:600;'>{event.get('duration', 60)} min</td></tr>
          <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>QUESTIONS</td>
              <td style='padding:6px 0;font-weight:600;'>{event.get('total_questions', 0)}</td></tr>
        """
    else:
        extra_rows = f"""
          <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>SUBJECT</td>
              <td style='padding:6px 0;font-weight:600;'>{event.get('subject', 'General')}</td></tr>
          <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>TEACHER</td>
              <td style='padding:6px 0;font-weight:600;'>{event.get('teacher_name', '—')}</td></tr>
        """

    html = f"""
    <!DOCTYPE html><html><body style='font-family:Arial,sans-serif;background:#f5f7fb;padding:24px;'>
      <div style='max-width:560px;margin:auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(15,23,42,.06);'>
        <div style='background:linear-gradient(135deg,#1e3a5f,#2d5a87);color:#fff;padding:28px;'>
          <div style='font-size:12px;letter-spacing:3px;opacity:.85;'>NEXUACADEMY — {kind_label} REMINDER</div>
          <h1 style='margin:8px 0 0;font-size:24px;'>Starts in {label}</h1>
        </div>
        <div style='padding:28px;'>
          <p style='margin:0 0 16px;color:#334155;'>Hi <strong>{student_name}</strong>, don't forget about your upcoming {kind}:</p>
          <div style='border-left:4px solid {accent};background:#f8fafc;padding:16px 18px;border-radius:8px;'>
            <div style='font-size:18px;font-weight:700;color:#0f172a;margin-bottom:8px;'>{title}</div>
            <table style='width:100%;border-collapse:collapse;'>
              <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>DATE</td>
                  <td style='padding:6px 0;font-weight:600;'>{date_str}</td></tr>
              <tr><td style='padding:6px 0;color:#64748b;font-size:12px;'>TIME</td>
                  <td style='padding:6px 0;font-weight:600;'>{time_str}</td></tr>
              {extra_rows}
            </table>
          </div>
          <div style='text-align:center;margin:24px 0;'>
            <a href='{cta_link}' style='display:inline-block;background:{accent};color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;'>{cta_label}</a>
          </div>
          <p style='color:#64748b;font-size:13px;margin:16px 0 0;'>Tip: join 5 minutes early to ensure your connection is working.</p>
        </div>
        <div style='background:#f8fafc;padding:16px;text-align:center;color:#94a3b8;font-size:12px;'>© NexUacademy · Automated reminder</div>
      </div>
    </body></html>
    """
    return subject_line, html


async def _send_email(to_email: str, subject: str, html: str) -> bool:
    if not resend.api_key or not to_email:
        return False
    try:
        await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return False


async def _dispatch_reminders_for_event(event: dict, kind: str, interval: dict):
    """Dispatch reminder notifications (in-app, push, email) for one event."""
    db = get_database()
    now = datetime.now(timezone.utc)

    event_id = event.get("test_id") if kind == "test" else event.get("class_id")
    reminder_key = f"reminder_{kind}_{interval['key']}_{event_id}"

    already = await db.sent_reminders.find_one({"key": reminder_key})
    if already:
        return

    batches = event.get("assigned_batches", [])
    if not batches:
        return

    students = await db.users.find({
        "role": "student",
        "batch_id": {"$in": batches},
    }, {"_id": 0, "password": 0}).to_list(length=None)

    event["__interval_key"] = interval["key"]
    event_title = event.get("test_name") if kind == "test" else event.get("title", "class")
    url = "/assigned-tests" if kind == "test" else "/classes"

    push_count = 0
    email_count = 0

    for student in students:
        # In-app notification
        await db.notifications.insert_one({
            "user_id": student["user_id"],
            "type": kind,
            "title": f"{ 'Test' if kind=='test' else 'Class' } in {interval['label']}",
            "message": f"{event_title} starts in {interval['label']}.",
            "data": {("test_id" if kind == "test" else "class_id"): event_id},
            "is_read": False,
            "created_at": now.isoformat(),
        })

        # Push notification
        sub = student.get("push_subscription")
        if sub and student.get("notifications_enabled"):
            ok = await send_push_notification(sub, {
                "title": f"{ 'Test' if kind=='test' else 'Class' } in {interval['label']}",
                "body": f"{event_title} starts soon.",
                "data": {"url": url, "type": kind},
            })
            if ok:
                push_count += 1

        # Email reminder
        subj, html = _render_event_email(student.get("name", "Student"), event, kind, interval["label"])
        if await _send_email(student.get("email"), subj, html):
            email_count += 1

    await db.sent_reminders.insert_one({
        "key": reminder_key,
        "event_kind": kind,
        "event_id": event_id,
        "interval_key": interval["key"],
        "sent_at": now.isoformat(),
        "students_notified": len(students),
        "push_sent": push_count,
        "email_sent": email_count,
    })

    logger.info(
        f"Reminder ({interval['label']}, {kind}): {event_title} -> "
        f"{len(students)} in-app, {push_count} push, {email_count} email"
    )


async def check_and_send_reminders():
    """Scan scheduled tests AND classes for upcoming reminders."""
    db = get_database()
    now = datetime.now(timezone.utc)

    # Look ahead window ±2 minutes around each interval mark
    for interval in REMINDER_INTERVALS:
        window_start = now + timedelta(minutes=interval["minutes"] - 2)
        window_end = now + timedelta(minutes=interval["minutes"] + 2)

        # ---------- TESTS ----------
        tests = await db.teacher_tests.find({
            "status": {"$in": ["scheduled", "published"]},
        }, {"_id": 0}).to_list(length=None)
        for t in tests:
            dt = _parse_dt(t.get("scheduled_date_time"))
            if dt and window_start <= dt <= window_end:
                await _dispatch_reminders_for_event(t, "test", interval)

        # ---------- CLASSES ----------
        classes = await db.classes.find({
            "status": {"$ne": "cancelled"},
        }, {"_id": 0}).to_list(length=None)
        for c in classes:
            dt = _parse_dt(c.get("scheduled_date_time"))
            if dt and window_start <= dt <= window_end:
                await _dispatch_reminders_for_event(c, "class", interval)


async def reminder_loop():
    """Background loop - runs every 60 seconds."""
    logger.info("Unified reminder scheduler started (tests + classes, 24h/1h/15m)")
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            logger.error(f"Reminder check error: {e}", exc_info=True)
        await asyncio.sleep(60)
