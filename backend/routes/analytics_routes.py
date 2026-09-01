"""Analytics — student and admin dashboards on Supabase Postgres."""
from fastapi import APIRouter, Depends
from config.database import get_pool
from middleware.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def student_dashboard(user=Depends(get_current_user)):
    """Student's overview: attempts, avg accuracy, live/upcoming classes, unread notifs."""
    if user.get("role") != "student":
        return {"success": True, "stats": {}}
    pool = get_pool()
    async with pool.acquire() as conn:
        attempts = await conn.fetchval(
            "SELECT count(*) FROM test_attempts WHERE student_id = $1 AND status = 'submitted'",
            user["user_id"],
        )
        in_prog = await conn.fetchval(
            "SELECT count(*) FROM test_attempts WHERE student_id = $1 AND status = 'in_progress'",
            user["user_id"],
        )
        avg_acc = await conn.fetchval(
            "SELECT COALESCE(round(avg(accuracy)::numeric, 1), 0) FROM test_attempts WHERE student_id = $1 AND status = 'submitted'",
            user["user_id"],
        )
        classes = 0
        upcoming = 0
        if user.get("batch_id"):
            classes = await conn.fetchval(
                "SELECT count(*) FROM classes WHERE $1 = ANY(assigned_batches)",
                user["batch_id"],
            )
            upcoming = await conn.fetchval(
                "SELECT count(*) FROM classes WHERE $1 = ANY(assigned_batches) AND scheduled_date_time > NOW()",
                user["batch_id"],
            )
        unread_notifs = await conn.fetchval(
            "SELECT count(*) FROM notifications WHERE user_id = $1 AND is_read = false",
            user["user_id"],
        )
    return {
        "success": True,
        "stats": {
            "tests_taken": attempts or 0,
            "tests_in_progress": in_prog or 0,
            "average_accuracy": float(avg_acc or 0),
            "total_classes": classes or 0,
            "upcoming_classes": upcoming or 0,
            "unread_notifications": unread_notifs or 0,
        },
    }


@router.get("/subject-wise")
async def student_subject_wise(user=Depends(get_current_user)):
    """Accuracy breakdown by test subject for the student."""
    if user.get("role") != "student":
        return {"success": True, "subjects": []}
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.subject, count(a.attempt_id) AS attempts,
                   COALESCE(round(avg(a.accuracy)::numeric, 1), 0) AS avg_accuracy,
                   COALESCE(sum(a.correct_answers), 0) AS correct,
                   COALESCE(sum(a.incorrect_answers), 0) AS incorrect
            FROM test_attempts a
            JOIN tests t ON t.test_id = a.test_id
            WHERE a.student_id = $1 AND a.status = 'submitted'
            GROUP BY t.subject
            ORDER BY t.subject
            """,
            user["user_id"],
        )
    return {"success": True, "subjects": [dict(r) for r in rows]}


@router.get("/admin/overview")
async def admin_overview(user=Depends(get_current_admin)):
    """Admin dashboard: totals, batch breakdown, recent activity, payments."""
    pool = get_pool()
    async with pool.acquire() as conn:
        total_students = await conn.fetchval("SELECT count(*) FROM profiles WHERE role = 'student'")
        total_teachers = await conn.fetchval("SELECT count(*) FROM profiles WHERE role = 'teacher'")
        total_classes = await conn.fetchval("SELECT count(*) FROM classes")
        total_tests = await conn.fetchval("SELECT count(*) FROM tests")
        total_announcements = await conn.fetchval("SELECT count(*) FROM announcements")
        paid_students = await conn.fetchval("SELECT count(*) FROM profiles WHERE role='student' AND payment_status='paid'")
        revenue = await conn.fetchval("SELECT COALESCE(sum(amount),0) FROM payments WHERE status='paid'")
        by_batch = await conn.fetch(
            """
            SELECT b.id, b.name, b.code, count(p.id) AS students
            FROM batches b
            LEFT JOIN profiles p ON p.batch_id = b.id AND p.role = 'student'
            GROUP BY b.id, b.name, b.code
            ORDER BY students DESC, b.name ASC
            """
        )
        recent_signups = await conn.fetch(
            """SELECT id, email, name, batch_id, created_at FROM profiles
               WHERE role='student' ORDER BY created_at DESC LIMIT 10"""
        )
        recent_payments = await conn.fetch(
            """SELECT payment_id, user_id, amount, status, paid_at, plan
               FROM payments ORDER BY created_at DESC LIMIT 10"""
        )
    def _dt(v): return v.isoformat() if hasattr(v, "isoformat") else v
    return {
        "success": True,
        "stats": {
            "total_students": total_students or 0,
            "total_teachers": total_teachers or 0,
            "total_classes": total_classes or 0,
            "total_tests": total_tests or 0,
            "total_announcements": total_announcements or 0,
            "paid_students": paid_students or 0,
            "revenue_paise": revenue or 0,
            "revenue_inr": (revenue or 0) // 100,
        },
        "batches": [dict(r) for r in by_batch],
        "recent_signups": [{k: _dt(v) for k, v in dict(r).items()} | {"id": str(r["id"])} for r in recent_signups],
        "recent_payments": [{k: _dt(v) for k, v in dict(r).items()} | {"user_id": str(r["user_id"]) if r["user_id"] else None} for r in recent_payments],
    }
