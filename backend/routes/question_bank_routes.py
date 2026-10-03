"""Question Bank — fixed folder hierarchy (Feb 2026 refactor).

Replaces the earlier dynamic topic/subtopic model with a seeded tree of
PYQ (JEE Mains / JEE Advanced / NEET / Olympiads) and Non-PYQ folders.
Every teacher can read + write the bank; the gate on specific emails has
been lifted so Test Creation can source questions for all teachers.

Per-question upload cap: 15 MB total across every image attached to a
single question (question image + option A/B/C/D images). Enforced on
every write path.
"""
import json
import logging
import mimetypes
import uuid
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from config.database import get_pool, get_supabase_admin
from middleware.auth import get_current_teacher
from services.pg_utils import json_safe

router = APIRouter(prefix="/teacher", tags=["question-bank"])
logger = logging.getLogger(__name__)

BUCKET = "question-bank-images"
MAX_TOTAL_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB per question (all images combined)
MAX_SOLUTION_VIDEO_BYTES = 25 * 1024 * 1024  # separate cap for solution video
ALLOWED_DIFFICULTY = {"Easy", "Moderate", "Difficult"}


def teacher_has_question_bank(user: dict) -> bool:
    """Open to every authenticated teacher + admin now that CreateTest sources
    questions from the bank for all teachers. Kept as a function so other
    modules (auth_routes, otp_routes) that import this symbol still work."""
    role = (user or {}).get("role")
    return role in ("teacher", "admin")


async def get_qbank_teacher(request: Request):
    """All authenticated teachers (+ admins) can use the Question Bank."""
    return await get_current_teacher(request)


# ---- Storage bucket helper --------------------------------------------------
def _ensure_bucket():
    supabase = get_supabase_admin()
    try:
        supabase.storage.create_bucket(BUCKET, options={"public": True})
    except Exception as e:
        msg = str(e).lower()
        if "already" not in msg and "duplicate" not in msg:
            logger.debug(f"create_bucket({BUCKET}) ignored: {e}")


async def _read_image(file: UploadFile) -> bytes:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    return await file.read()


def _upload_bytes(data: bytes, content_type: str, user_id: str, kind: str = "img") -> str:
    _ensure_bucket()
    ext = mimetypes.guess_extension(content_type) or ".png"
    if ext.lower() == ".jpeg":
        ext = ".jpg"
    key = f"{user_id}/{kind}/{uuid.uuid4().hex}{ext}"
    supabase = get_supabase_admin()
    supabase.storage.from_(BUCKET).upload(
        key, data, {"content-type": content_type, "upsert": "true"}
    )
    return supabase.storage.from_(BUCKET).get_public_url(key)


async def _upload_media(file: UploadFile, user_id: str) -> tuple[str, str]:
    """Upload a solution image or video. Returns (public_url, 'image'|'video')."""
    ct = file.content_type or ""
    if ct.startswith("image/"):
        kind = "image"; limit = MAX_TOTAL_IMAGE_BYTES
    elif ct.startswith("video/"):
        kind = "video"; limit = MAX_SOLUTION_VIDEO_BYTES
    else:
        raise HTTPException(status_code=400, detail="Solution media must be an image or a video")
    data = await file.read()
    if len(data) > limit:
        raise HTTPException(
            status_code=400,
            detail=f"Solution {kind} exceeds {limit // (1024 * 1024)} MB limit",
        )
    return _upload_bytes(data, ct, user_id, kind="solution"), kind


# =============================================================================
# FOLDERS (fixed hierarchy — PYQ + Non-PYQ)
# =============================================================================
@router.get("/qb/folders")
async def list_folders(user=Depends(get_qbank_teacher)):
    """Return the full folder tree with question counts per leaf."""
    pool = get_pool()
    async with pool.acquire() as conn:
        folders = await conn.fetch(
            "SELECT * FROM qb_folders ORDER BY level ASC, sort_order ASC, name ASC"
        )
        counts = await conn.fetch(
            "SELECT folder_id, count(*) AS cnt FROM question_bank "
            "WHERE folder_id IS NOT NULL GROUP BY folder_id"
        )
    count_map = {str(r["folder_id"]): r["cnt"] for r in counts}

    nodes: Dict[str, Dict[str, Any]] = {}
    for f in folders:
        d = json_safe(f)
        d["children"] = []
        d["question_count"] = int(count_map.get(d["id"], 0)) if d["is_leaf"] else 0
        nodes[d["id"]] = d

    roots: List[Dict[str, Any]] = []
    for d in nodes.values():
        parent = d.get("parent_id")
        if parent and str(parent) in nodes:
            nodes[str(parent)]["children"].append(d)
        else:
            roots.append(d)

    # Roll descendant question counts up to non-leaf parents (for display badges)
    def _roll(node):
        if node["is_leaf"]:
            return node["question_count"]
        total = 0
        for c in node["children"]:
            total += _roll(c)
        node["question_count"] = total
        return total

    for r in roots:
        _roll(r)
    roots.sort(key=lambda n: (n["sort_order"], n["name"]))
    return {"success": True, "folders": roots}


# =============================================================================
# QUESTION BANK — CRUD scoped to a leaf folder
# =============================================================================
def _parse_json_field(raw: Optional[str], default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


async def _assert_leaf_folder(folder_id: str) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM qb_folders WHERE id = $1", folder_id)
    if not row:
        raise HTTPException(status_code=400, detail="Folder not found")
    if not row["is_leaf"]:
        raise HTTPException(status_code=400, detail="Questions can only be added to a leaf folder")
    return dict(row)


@router.post("/question-bank")
async def create_question(
    request: Request,
    folder_id: str = Form(...),
    question_text: Optional[str] = Form(""),
    question_type: str = Form("MCQ_Single"),
    options_text: Optional[str] = Form(None),
    correct_answers: Optional[str] = Form(None),
    numerical_answer: Optional[str] = Form(None),
    answer_range: Optional[str] = Form(None),
    difficulty: str = Form("Moderate"),
    marks: int = Form(4),
    negative_marks: int = Form(-1),
    teacher_note: Optional[str] = Form(""),
    solution_youtube_url: Optional[str] = Form(""),
    question_image: Optional[UploadFile] = File(None),
    option_a_image: Optional[UploadFile] = File(None),
    option_b_image: Optional[UploadFile] = File(None),
    option_c_image: Optional[UploadFile] = File(None),
    option_d_image: Optional[UploadFile] = File(None),
    solution_media: Optional[UploadFile] = File(None),
):
    user = await get_qbank_teacher(request)
    folder = await _assert_leaf_folder(folder_id)

    if question_type not in ("MCQ_Single", "MCQ_Multiple", "Numerical_Integer", "Numerical_Decimal"):
        raise HTTPException(status_code=400, detail="Invalid question_type")
    if difficulty not in ALLOWED_DIFFICULTY:
        raise HTTPException(
            status_code=400,
            detail=f"Difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}",
        )

    # Read all images up-front and enforce the 15 MB TOTAL cap
    image_slots: List[tuple[str, UploadFile]] = []
    if question_image is not None and question_image.filename:
        image_slots.append(("Q", question_image))
    for label, upload in (
        ("A", option_a_image), ("B", option_b_image),
        ("C", option_c_image), ("D", option_d_image),
    ):
        if upload is not None and upload.filename:
            image_slots.append((label, upload))

    image_bytes: Dict[str, tuple[bytes, str]] = {}
    total_bytes = 0
    for label, upload in image_slots:
        data = await _read_image(upload)
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_IMAGE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Total image size exceeds 15 MB (reached {total_bytes // (1024 * 1024)} MB "
                    f"while processing image {label}). Compress or remove images and retry."
                ),
            )
        image_bytes[label] = (data, upload.content_type)

    # Upload now that validation passed
    q_image_url = None
    if "Q" in image_bytes:
        data, ct = image_bytes["Q"]
        q_image_url = _upload_bytes(data, ct, user["user_id"], kind="question")

    opt_texts = _parse_json_field(options_text, {}) or {}
    correct = _parse_json_field(correct_answers, []) or []

    options_out: Dict[str, Dict[str, Any]] = {}
    if question_type.startswith("MCQ"):
        for opt in ("A", "B", "C", "D"):
            img_url = ""
            if opt in image_bytes:
                data, ct = image_bytes[opt]
                img_url = _upload_bytes(data, ct, user["user_id"], kind="option")
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

    # Solution media (image OR video) + YouTube
    solution_media_url = None
    solution_media_type = None
    if solution_media is not None and solution_media.filename:
        solution_media_url, solution_media_type = await _upload_media(solution_media, user["user_id"])
    yt = (solution_youtube_url or "").strip() or None

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO question_bank
              (folder_id, question_text, question_image_url, question_type,
               options, correct_answers, numerical_answer, answer_range, difficulty,
               marks, negative_marks, teacher_note, solution_youtube_url,
               solution_media_url, solution_media_type, created_by)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8::jsonb,$9,$10,$11,$12,$13,$14,$15,$16)
            RETURNING *
            """,
            folder_id,
            (question_text or "").strip(), q_image_url, question_type,
            json.dumps(options_out) if options_out else json.dumps({}),
            correct, num_ans,
            json.dumps(ans_range) if ans_range else None,
            difficulty, marks, negative_marks,
            (teacher_note or "").strip(), yt,
            solution_media_url, solution_media_type,
            user["user_id"],
        )
    return {"success": True, "question": json_safe(row), "folder_path": folder["path"]}


@router.get("/question-bank")
async def list_questions(
    folder_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    user=Depends(get_qbank_teacher),
):
    pool = get_pool()
    clauses, args = [], []
    if folder_id:
        args.append(folder_id); clauses.append(f"folder_id = ${len(args)}")
    if difficulty:
        args.append(difficulty); clauses.append(f"difficulty = ${len(args)}")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM question_bank {where} ORDER BY created_at DESC LIMIT 500", *args
        )
    return {"success": True, "questions": [json_safe(r) for r in rows]}


@router.get("/question-bank/available")
async def available_for_batches(
    request: Request,
    folder_ids: List[str] = Query(default_factory=list),
    batch_codes: List[str] = Query(default_factory=list),
):
    """Return questions from the selected leaf folders that are still fresh
    (not yet assigned) for at least one requested batch, plus per-batch flags."""
    user = await get_qbank_teacher(request)
    if not folder_ids or not batch_codes:
        return {"success": True, "questions": [], "total_before_exclusion": 0}

    batches = [b.strip().upper() for b in batch_codes if b.strip()]
    pool = get_pool()
    async with pool.acquire() as conn:
        matched = await conn.fetch(
            """SELECT * FROM question_bank
                WHERE folder_id = ANY($1::uuid[])
                ORDER BY created_at DESC""",
            folder_ids,
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
            continue
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
# ASSIGNMENT LEDGER — called by CreateTest after test creation
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
