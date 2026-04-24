"""Admin Dashboard — page analytics, user stats, suggestion moderation."""
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional

from config.database import get_database
from middleware.auth import get_current_user
from models.requests import SuggestionUpdateRequest

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


async def _require_admin(request: Request):
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/overview")
async def overview(request: Request, days: int = 30):
    await _require_admin(request)
    db = get_database()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_visits = await db.page_visits.count_documents({"timestamp": {"$gte": since}})

    # Page visits breakdown
    page_visits = await db.page_visits.aggregate([
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {
            "_id": "$page",
            "totalVisits": {"$sum": 1},
            "uniqueVisitors": {"$addToSet": "$visitor_id"},
        }},
        {"$project": {"totalVisits": 1, "uniqueVisitors": {"$size": "$uniqueVisitors"}}},
        {"$sort": {"totalVisits": -1}},
        {"$limit": 20},
    ]).to_list(length=None)

    # Daily trend
    daily_trends = await db.page_visits.aggregate([
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "visits": {"$sum": 1},
            "uniqueVisitors": {"$addToSet": "$visitor_id"},
        }},
        {"$project": {"visits": 1, "uniqueVisitors": {"$size": "$uniqueVisitors"}}},
        {"$sort": {"_id": 1}},
    ]).to_list(length=None)

    # Device breakdown
    device_breakdown = await db.page_visits.aggregate([
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {"_id": "$device", "count": {"$sum": 1}}},
    ]).to_list(length=None)

    # Top referrers
    top_referrers = await db.page_visits.aggregate([
        {"$match": {"timestamp": {"$gte": since}, "referrer": {"$ne": ""}}},
        {"$group": {"_id": "$referrer", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]).to_list(length=None)

    unique_visitors = await db.page_visits.aggregate([
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {"_id": "$visitor_id"}},
        {"$count": "total"},
    ]).to_list(length=1)

    return {
        "success": True,
        "period_days": days,
        "total_visits": total_visits,
        "unique_visitors": (unique_visitors[0]["total"] if unique_visitors else 0),
        "pageVisits": page_visits,
        "dailyTrends": daily_trends,
        "deviceBreakdown": device_breakdown,
        "topReferrers": top_referrers,
    }


@router.get("/users")
async def user_stats(request: Request):
    await _require_admin(request)
    db = get_database()

    total_users = await db.users.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_teachers = await db.users.count_documents({"role": "teacher"})
    total_admins = await db.users.count_documents({"role": "admin"})

    # Registrations over last 30 days
    since = datetime.now(timezone.utc) - timedelta(days=30)
    registration_trend = await db.users.aggregate([
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]).to_list(length=None)

    batch_distribution = await db.users.aggregate([
        {"$match": {"role": "student", "batch_id": {"$ne": None}}},
        {"$group": {"_id": "$batch_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(length=None)

    # Active users (logged in within last 7 days)
    active_since = datetime.now(timezone.utc) - timedelta(days=7)
    active_users = await db.users.count_documents({"last_login": {"$gte": active_since}})

    return {
        "success": True,
        "totalUsers": total_users,
        "totalStudents": total_students,
        "totalTeachers": total_teachers,
        "totalAdmins": total_admins,
        "activeUsers": active_users,
        "registrationTrend": registration_trend,
        "batchDistribution": batch_distribution,
    }


@router.get("/suggestions")
async def list_suggestions(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    await _require_admin(request)
    db = get_database()

    q = {}
    if status and status != "all":
        q["status"] = status
    if priority and priority != "all":
        q["priority"] = priority

    total = await db.student_suggestions.count_documents(q)
    skip = max(0, (page - 1) * limit)
    rows = await db.student_suggestions.find(q, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)

    # Counts by status & priority
    by_status = await db.student_suggestions.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ).to_list(length=None)
    by_priority = await db.student_suggestions.aggregate(
        [{"$group": {"_id": "$priority", "count": {"$sum": 1}}}]
    ).to_list(length=None)
    unread_count = await db.student_suggestions.count_documents({"is_read": False})

    return {
        "success": True,
        "suggestions": rows,
        "pagination": {"total": total, "page": page, "pages": (total + limit - 1) // limit},
        "unreadCount": unread_count,
        "statusCounts": by_status,
        "priorityCounts": by_priority,
    }


@router.put("/suggestions/{suggestion_id}")
async def update_suggestion(suggestion_id: str, payload: SuggestionUpdateRequest, request: Request):
    await _require_admin(request)
    db = get_database()

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    res = await db.student_suggestions.update_one({"suggestion_id": suggestion_id}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    updated = await db.student_suggestions.find_one({"suggestion_id": suggestion_id}, {"_id": 0})
    return {"success": True, "suggestion": updated}


@router.delete("/suggestions/{suggestion_id}")
async def delete_suggestion(suggestion_id: str, request: Request):
    await _require_admin(request)
    db = get_database()
    res = await db.student_suggestions.delete_one({"suggestion_id": suggestion_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"success": True}
