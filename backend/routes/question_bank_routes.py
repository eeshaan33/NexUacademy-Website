"""Question Bank + smart test-question exclusion (per-batch memory).

Gated to teachers explicitly listed in QUESTION_BANK_TEACHERS below (currently
just Nitin Saini). Add more emails to open the feature up.
"""
import json
import logging
import mimetypes
import uuid
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from config.database import get_pool, get_supabase_admin
from middleware.auth import get_current_teacher
from services.pg_utils import json_safe

router = APIRouter(prefix="/teacher", tags=["question-bank"])
logger = logging.getLogger(__name__)

# ---- Feature flag: which teacher emails see the Question Bank ---------------
QUESTION_BANK_TEACHERS = {"nitin@nexuacademy.com"}

BUCKET = "question-bank-images"


def teacher_has_question_bank(user: dict) -> bool:
    """Enabled for admins + explicit allow-list teachers."""
    if user.get("role") == "admin":
        return True
    email = (user.get("email") or "").strip().lower()
    return email in QUESTION_BANK_TEACHERS


async def get_qbank_teacher(request: Request):
    user = await get_current_teacher(request)
    if not teacher_has_question_bank(user):
        raise HTTPException(status_code=403, detail="Question Bank access not enabled for this account")
    return user


# ---- Storage bucket helper --------------------------------------------------
def _ensure_bucket():
    supabase = get_supabase_admin()
    try:
        supabase.storage.create_bucket(BUCKET, options={"public": True})
    except Exception as e:
        msg = str(e).lower()
        if "already" not in msg and "duplicate" not in msg:
            logger.debug(f"create_bucket({BUCKET}) ignored: {e}")


async def _upload_image(file: UploadFile, user_id: str) -> str:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image exceeds 5 MB limit")
    _ensure_bucket()
    ext = mimetypes.guess_extension(file.content_type) or ".png"
    if ext.lower() == ".jpeg":
        ext = ".jpg"
    key = f"{user_id}/{uuid.uuid4().hex}{ext}"
    supabase = get_supabase_admin()
    supabase.storage.from_(BUCKET).upload(
        key, data, {"content-type": file.content_type, "upsert": "true"}
    )
    return supabase.storage.from_(BUCKET).get_public_url(key)


# =============================================================================
# TOPICS
# =============================================================================
class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    subject: Optional[str] = None


@router.get("/topics")
async def list_topics(subject: Optional[str] = None, user=Depends(get_qbank_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        if subject:
            rows = await conn.fetch(
                "SELECT * FROM topics WHERE lower(subject) = lower($1) ORDER BY name ASC",
                subject,
            )
        else:
            rows = await conn.fetch("SELECT * FROM topics ORDER BY name ASC")
    return {"success": True, "topics": [json_safe(r) for r in rows]}


@router.post("/topics")
async def create_topic(payload: TopicCreate, user=Depends(get_qbank_teacher)):
    name = payload.name.strip()
    subject = (payload.subject or "").strip() or None
    if not name:
        raise HTTPException(status_code=400, detail="Topic name is required")
    pool = get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM topics WHERE lower(name) = lower($1) LIMIT 1", name
        )
        if existing:
            return {"success": True, "topic": json_safe(existing), "created": False}
        row = await conn.fetchrow(
            """INSERT INTO topics (name, subject, created_by)
               VALUES ($1, $2, $3) RETURNING *""",
            name, subject, user["user_id"],
        )
    return {"success": True, "topic": json_safe(row), "created": True}


# =============================================================================
# SUBTOPICS
# =============================================================================
class SubtopicCreate(BaseModel):
    topic_id: str
    name: str = Field(..., min_length=1, max_length=120)


@router.get("/topics/{topic_id}/subtopics")
async def list_subtopics(topic_id: str, user=Depends(get_qbank_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM subtopics WHERE topic_id = $1 ORDER BY name ASC", topic_id
        )
    return {"success": True, "subtopics": [json_safe(r) for r in rows]}


@router.post("/subtopics")
async def create_subtopic(payload: SubtopicCreate, user=Depends(get_qbank_teacher)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Subtopic name is required")
    pool = get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT * FROM subtopics WHERE topic_id = $1 AND lower(name) = lower($2) LIMIT 1",
            payload.topic_id, name,
        )
        if existing:
            return {"success": True, "subtopic": json_safe(existing), "created": False}
        row = await conn.fetchrow(
            """INSERT INTO subtopics (topic_id, name, created_by)
               VALUES ($1, $2, $3) RETURNING *""",
            payload.topic_id, name, user["user_id"],
        )
    return {"success": True, "subtopic": json_safe(row), "created": True}


# =============================================================================
# QUESTION BANK
# =============================================================================
def _parse_json_field(raw: Optional[str], default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


@router.post("/question-bank")
async def create_question(
    request: Request,
    topic_id: str = Form(...),
    subtopic_id: str = Form(...),
    question_text: Optional[str] = Form(""),
    question_type: str = Form("MCQ_Single"),
    options_text: Optional[str] = Form(None),       # JSON: {"A":"..","B":"..","C":"..","D":".."}
    correct_answers: Optional[str] = Form(None),    # JSON: ["A","C"]
    numerical_answer: Optional[str] = Form(None),
    answer_range: Optional[str] = Form(None),       # JSON: {"min":..,"max":..}
    difficulty: Optional[str] = Form(None),
    marks: int = Form(4),
    negative_marks: int = Form(-1),
    teacher_note: Optional[str] = Form(""),
    question_image: Optional[UploadFile] = File(None),
    option_a_image: Optional[UploadFile] = File(None),
    option_b_image: Optional[UploadFile] = File(None),
    option_c_image: Optional[UploadFile] = File(None),
    option_d_image: Optional[UploadFile] = File(None),
):
    user = await get_qbank_teacher(request)
    if question_type not in ("MCQ_Single", "MCQ_Multiple", "Numerical_Integer", "Numerical_Decimal"):
        raise HTTPException(status_code=400, detail="Invalid question_type")

    # Uploads
    q_image_url = None
    if question_image is not None and question_image.filename:
        q_image_url = await _upload_image(question_image, user["user_id"])

    opt_texts = _parse_json_field(options_text, {}) or {}
    correct = _parse_json_field(correct_answers, []) or []

    options_out: Dict[str, Dict[str, Any]] = {}
    if question_type.startswith("MCQ"):
        for opt, upload in [("A", option_a_image), ("B", option_b_image),
                            ("C", option_c_image), ("D", option_d_image)]:
            img_url = None
            if upload is not None and upload.filename:
                img_url = await _upload_image(upload, user["user_id"])
            options_out[opt] = {
                "text": (opt_texts.get(opt) or "").strip(),
                "imageUrl": img_url or "",
            }
        if not correct:
            raise HTTPException(status_code=400, detail="Select at least one correct option")
        if question_type == "MCQ_Single" and len(correct) != 1:
            raise HTTPException(status_code=400, detail="MCQ_Single needs exactly one correct answer")

    num_ans = None
    ans_range = None
    if question_type.startswith("Numerical"):
        if numerical_answer in (None, ""):
            raise HTTPException(status_code=400, detail="Numerical answer is required")
        try:
            num_ans = float(numerical_answer)
        except ValueError:
            raise HTTPException(status_code=400, detail="numerical_answer must be a number")
        r = _parse_json_field(answer_range, None)
        if r and r.get("min") not in (None, "") and r.get("max") not in (None, ""):
            try:
                ans_range = {"min": float(r["min"]), "max": float(r["max"])}
            except ValueError:
                ans_range = None

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO question_bank
              (topic_id, subtopic_id, question_text, question_image_url, question_type,
               options, correct_answers, numerical_answer, answer_range, difficulty,
               marks, negative_marks, teacher_note, created_by)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9::jsonb,$10,$11,$12,$13,$14)
            RETURNING *
            """,
            topic_id, subtopic_id,
            (question_text or "").strip(), q_image_url, question_type,
            json.dumps(options_out) if options_out else json.dumps({}),
            correct, num_ans,
            json.dumps(ans_range) if ans_range else None,
            difficulty, marks, negative_marks,
            (teacher_note or "").strip(), user["user_id"],
        )
    return {"success": True, "question": json_safe(row)}


@router.get("/question-bank")
async def list_questions(
    topic_id: Optional[str] = None,
    subtopic_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    user=Depends(get_qbank_teacher),
):
    pool = get_pool()
    clauses, args = [], []
    if topic_id:
        args.append(topic_id); clauses.append(f"topic_id = ${len(args)}")
    if subtopic_id:
        args.append(subtopic_id); clauses.append(f"subtopic_id = ${len(args)}")
    if difficulty:
        args.append(difficulty); clauses.append(f"difficulty = ${len(args)}")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM question_bank {where} ORDER BY created_at DESC LIMIT 500", *args
        )
    return {"success": True, "questions": [json_safe(r) for r in rows]}


@router.get("/question-bank/tree")
async def question_bank_tree(user=Depends(get_qbank_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        topics = await conn.fetch("SELECT * FROM topics ORDER BY name ASC")
        subtopics = await conn.fetch("SELECT * FROM subtopics ORDER BY name ASC")
        counts = await conn.fetch(
            """SELECT topic_id, subtopic_id, count(*) AS cnt
                 FROM question_bank GROUP BY topic_id, subtopic_id"""
        )
    count_map: Dict[str, int] = {f"{r['topic_id']}::{r['subtopic_id']}": r["cnt"] for r in counts}

    subtopics_by_topic: Dict[str, List[Dict[str, Any]]] = {}
    topic_totals: Dict[str, int] = {}
    for s in subtopics:
        s = json_safe(s)
        key = f"{s['topic_id']}::{s['id']}"
        s["question_count"] = int(count_map.get(key, 0))
        subtopics_by_topic.setdefault(str(s["topic_id"]), []).append(s)
        topic_totals[str(s["topic_id"])] = topic_totals.get(str(s["topic_id"]), 0) + s["question_count"]

    tree = []
    for t in topics:
        t = json_safe(t)
        tid = str(t["id"])
        t["subtopics"] = subtopics_by_topic.get(tid, [])
        t["question_count"] = topic_totals.get(tid, 0)
        tree.append(t)
    return {"success": True, "tree": tree}


@router.get("/question-bank/available")
async def available_for_batches(
    request: Request,
    topic_ids: List[str] = Query(default_factory=list),
    subtopic_ids: List[str] = Query(default_factory=list),
    batch_codes: List[str] = Query(default_factory=list),
):
    """Return every question that matches topic+subtopic filters AND is fresh
    for at least one of the requested batches, plus per-batch fresh/used flags.
    """
    user = await get_qbank_teacher(request)
    if not topic_ids or not subtopic_ids or not batch_codes:
        return {"success": True, "questions": [], "total_before_exclusion": 0}

    batches = [b.strip().upper() for b in batch_codes if b.strip()]
    pool = get_pool()
    async with pool.acquire() as conn:
        matched = await conn.fetch(
            """SELECT * FROM question_bank
                WHERE topic_id = ANY($1::uuid[])
                  AND subtopic_id = ANY($2::uuid[])
                ORDER BY created_at DESC""",
            topic_ids, subtopic_ids,
        )
        used_rows = await conn.fetch(
            """SELECT question_id, batch_code FROM question_batch_assignments
                WHERE batch_code = ANY($1::text[])""",
            batches,
        )
    used_map: Dict[str, set] = {}
    for r in used_rows:
        used_map.setdefault(str(r["question_id"]), set()).add(r["batch_code"])

    results = []
    for row in matched:
        q = json_safe(row)
        qid = str(q["id"])
        used_for = sorted(used_map.get(qid, set()) & set(batches))
        fresh_for = [b for b in batches if b not in used_for]
        if not fresh_for:
            continue  # already used for every requested batch — hide
        q["fresh_for"] = fresh_for
        q["used_for"] = used_for
        results.append(q)
    return {
        "success": True,
        "questions": results,
        "total_before_exclusion": len(matched),
        "hidden_count": len(matched) - len(results),
        "batches": batches,
    }


@router.get("/question-bank/{question_id}")
async def get_question(question_id: str, user=Depends(get_qbank_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM question_bank WHERE id = $1", question_id)
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"success": True, "question": json_safe(row)}


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    question_image_url: Optional[str] = None
    options: Optional[Dict[str, Dict[str, Any]]] = None
    correct_answers: Optional[List[str]] = None
    numerical_answer: Optional[float] = None
    answer_range: Optional[Dict[str, float]] = None
    difficulty: Optional[str] = None
    marks: Optional[int] = None
    negative_marks: Optional[int] = None
    teacher_note: Optional[str] = None


@router.put("/question-bank/{question_id}")
async def update_question(question_id: str, payload: QuestionUpdate, user=Depends(get_qbank_teacher)):
    fields, args = [], []
    body = payload.dict(exclude_unset=True)
    for k, v in body.items():
        if k in ("options", "answer_range"):
            args.append(json.dumps(v) if v is not None else None)
            fields.append(f"{k} = ${len(args)}::jsonb")
        else:
            args.append(v)
            fields.append(f"{k} = ${len(args)}")
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    args.append(question_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"UPDATE question_bank SET {', '.join(fields)} WHERE id = ${len(args)} RETURNING *",
            *args,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"success": True, "question": json_safe(row)}


@router.delete("/question-bank/{question_id}")
async def delete_question(
    question_id: str,
    force: bool = False,
    user=Depends(get_qbank_teacher),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        used = await conn.fetchval(
            "SELECT count(*) FROM question_batch_assignments WHERE question_id = $1",
            question_id,
        )
        if used and not force:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"This question has been assigned to {used} batch(es). "
                    "Pass ?force=true to delete anyway — past test results may be affected."
                ),
            )
        await conn.execute(
            "DELETE FROM question_batch_assignments WHERE question_id = $1", question_id
        )
        await conn.execute("DELETE FROM question_bank WHERE id = $1", question_id)
    return {"success": True}


# =============================================================================
# ASSIGNMENT LEDGER — called by CreateTest.js after test creation to "remember"
# =============================================================================
class RecordAssignments(BaseModel):
    test_id: Optional[str] = None
    question_ids: List[str]
    batch_codes: List[str]


@router.post("/question-bank/record-assignments")
async def record_assignments(payload: RecordAssignments, user=Depends(get_qbank_teacher)):
    if not payload.question_ids or not payload.batch_codes:
        return {"success": True, "recorded": 0}
    batches = [b.strip().upper() for b in payload.batch_codes if b.strip()]
    pool = get_pool()
    recorded = 0
    async with pool.acquire() as conn:
        for qid in payload.question_ids:
            for bc in batches:
                res = await conn.execute(
                    """INSERT INTO question_batch_assignments (question_id, batch_code, test_id)
                       VALUES ($1, $2, $3)
                       ON CONFLICT (question_id, batch_code) DO NOTHING""",
                    qid, bc, payload.test_id,
                )
                if res and res.endswith(" 1"):
                    recorded += 1
    return {"success": True, "recorded": recorded}
