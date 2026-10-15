"""Razorpay payments: create order → checkout on frontend → verify signature → webhook.

- POST /api/payments/create-order       (auth) — creates a Razorpay order + DB row
- POST /api/payments/verify             (auth) — verifies signature and marks paid
- GET  /api/payments/my                 (auth) — student's own payment history
- POST /api/payments/webhook            (public, HMAC verified) — Razorpay push
"""
import hmac
import hashlib
import json
import logging
import os
from typing import Optional

import razorpay
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import short_id
from services.receipt_service import send_payment_receipt_email, pretty_paid_at

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)


def _client() -> razorpay.Client:
    key = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key or not secret:
        raise HTTPException(status_code=500, detail="Razorpay is not configured")
    return razorpay.Client(auth=(key, secret))


class CreateOrderRequest(BaseModel):
    plan: str = Field("admission_fee", max_length=50)
    amount: Optional[int] = None  # ignored except for admission_fee back-compat


# Server-side price catalog + tier granted on verify. Client-supplied amounts
# are ignored except for admission_fee (which uses FEE_AMOUNT_INR env for
# backwards compatibility with older tests).
PLAN_CATALOG = {
    "admission_fee":            {"amount_rupees": 30000, "grants_tier": "live_batch"},
    "lectures_upgrade":         {"amount_rupees": 1500,  "grants_tier": "lectures_only"},
    "lectures_tests_upgrade":   {"amount_rupees": 2500,  "grants_tier": "full_recorded"},
}


@router.post("/create-order")
async def create_order(payload: CreateOrderRequest, user=Depends(get_current_user)):
    plan_info = PLAN_CATALOG.get(payload.plan)
    if plan_info is None:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {payload.plan}")

    if payload.plan == "admission_fee":
        # Back-compat: honour FEE_AMOUNT_INR env override, else client-supplied
        amount_rupees = payload.amount or int(os.environ.get("FEE_AMOUNT_INR", plan_info["amount_rupees"]))
    else:
        amount_rupees = plan_info["amount_rupees"]

    if amount_rupees <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    amount_paise = amount_rupees * 100

    payment_id = short_id("pay")
    receipt = f"NEXU-{payment_id[-10:]}"

    try:
        order = _client().order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
            "notes": {"user_id": str(user["user_id"]), "email": user["email"],
                      "plan": payload.plan},
        })
    except Exception as e:
        logger.exception("Razorpay order.create failed")
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)[:200]}")

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO payments (payment_id, user_id, razorpay_order_id, amount, currency,
                                  plan, status, receipt, notes)
            VALUES ($1,$2,$3,$4,'INR',$5,'created',$6,$7::jsonb)
            """,
            payment_id, user["user_id"], order["id"], amount_paise,
            payload.plan, receipt, json.dumps({"created_from": "web"}),
        )

    return {
        "success": True,
        "order_id": order["id"],
        "amount": amount_paise,
        "amount_rupees": amount_rupees,
        "currency": "INR",
        "receipt": receipt,
        "key_id": os.environ["RAZORPAY_KEY_ID"],
        "prefill": {"name": user.get("name"), "email": user.get("email"),
                    "contact": user.get("phone_number") or ""},
        "plan": payload.plan,
    }


class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/verify")
async def verify_payment(payload: VerifyRequest, background: BackgroundTasks, user=Depends(get_current_user)):
    secret = os.environ.get("RAZORPAY_KEY_SECRET", "").encode()
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE payments SET status='failed', failed_at=NOW() WHERE razorpay_order_id=$1",
                payload.razorpay_order_id,
            )
        raise HTTPException(status_code=400, detail="Signature verification failed")

    pool = get_pool()
    async with pool.acquire() as conn:
        # Ownership guard: this order must belong to this user
        row = await conn.fetchrow(
            "SELECT user_id FROM payments WHERE razorpay_order_id = $1",
            payload.razorpay_order_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if str(row["user_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="This order does not belong to you")

        await conn.execute(
            """UPDATE payments
               SET razorpay_payment_id = $2, razorpay_signature = $3,
                   status = 'paid', paid_at = NOW()
               WHERE razorpay_order_id = $1""",
            payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature,
        )
        pay_plan = await conn.fetchval(
            "SELECT plan FROM payments WHERE razorpay_order_id = $1",
            payload.razorpay_order_id,
        )
        grants_tier = (PLAN_CATALOG.get(pay_plan or "") or {}).get("grants_tier")
        # For tier upgrades we always promote (they paid). For admission we
        # only set live_batch. Downgrade never happens automatically.
        await conn.execute(
            """UPDATE profiles SET payment_status = 'paid',
                   payment_completed_at = NOW(),
                   access_tier = CASE
                       WHEN $2::text IS NULL THEN access_tier
                       WHEN $2::text = 'live_batch' THEN 'live_batch'
                       WHEN access_tier = 'live_batch' THEN 'live_batch'
                       WHEN $2::text = 'full_recorded' THEN 'full_recorded'
                       WHEN $2::text = 'lectures_only' AND access_tier <> 'full_recorded' THEN 'lectures_only'
                       ELSE access_tier
                   END
               WHERE id = $1""",
            user["user_id"], grants_tier,
        )
        # Also mark student_applications paid if this order belongs to one
        await conn.execute(
            """UPDATE student_applications SET payment_status = 'paid',
                   razorpay_order_id = $2
               WHERE user_id = $1 AND payment_status <> 'paid'""",
            user["user_id"], payload.razorpay_order_id,
        )
        pay_row = await conn.fetchrow(
            """SELECT p.payment_id, p.receipt, p.amount, p.plan, p.paid_at,
                      p.razorpay_payment_id, p.razorpay_order_id,
                      pr.name, pr.email, pr.phone_number, pr.batch_id
               FROM payments p LEFT JOIN profiles pr ON pr.id = p.user_id
               WHERE p.razorpay_order_id = $1""",
            payload.razorpay_order_id,
        )
    # Fire receipt email in the background so /verify returns immediately.
    if pay_row and pay_row["email"]:
        background.add_task(
            send_payment_receipt_email,
            to_email=pay_row["email"],
            to_name=pay_row["name"] or "Student",
            receipt_data={
                "receipt_no": pay_row["receipt"],
                "payment_id": pay_row["razorpay_payment_id"],
                "order_id": pay_row["razorpay_order_id"],
                "paid_at_pretty": pretty_paid_at(pay_row["paid_at"]),
                "amount_paise": pay_row["amount"],
                "plan": pay_row["plan"],
                "student_name": pay_row["name"],
                "student_email": pay_row["email"],
                "student_phone": pay_row["phone_number"],
                "batch_code": pay_row["batch_id"],
            },
        )
    return {"success": True, "status": "paid"}


@router.get("/my")
async def my_payments(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM payments WHERE user_id = $1 ORDER BY created_at DESC",
            user["user_id"],
        )
    def _dt(v): return v.isoformat() if hasattr(v, "isoformat") else v
    return {"success": True, "payments": [
        {k: _dt(v) for k, v in dict(r).items()} for r in rows
    ]}


@router.post("/webhook")
async def webhook(request: Request):
    """Razorpay pushes payment.captured / payment.failed / order.paid events here."""
    signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip()
    raw_body = await request.body()

    if webhook_secret:
        expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    etype = event.get("event", "")
    entity = (event.get("payload") or {}).get("payment", {}).get("entity") or \
             (event.get("payload") or {}).get("order", {}).get("entity") or {}
    order_id = entity.get("order_id") or entity.get("id")
    payment_id_rp = entity.get("id")

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT payment_id, user_id FROM payments WHERE razorpay_order_id = $1", order_id)
        if not row:
            logger.info(f"Webhook received for unknown order_id: {order_id}")
            return {"received": True, "matched": False}

        if etype in ("payment.captured", "order.paid"):
            already_paid = await conn.fetchval(
                "SELECT status = 'paid' FROM payments WHERE razorpay_order_id = $1",
                order_id,
            )
            await conn.execute(
                """UPDATE payments SET status='paid', paid_at=NOW(), razorpay_payment_id=$2
                   WHERE razorpay_order_id=$1""",
                order_id, payment_id_rp,
            )
            await conn.execute(
                """UPDATE profiles SET payment_status='paid', payment_completed_at=NOW(),
                       access_tier = CASE
                           WHEN (SELECT plan FROM payments WHERE razorpay_order_id=$2) = 'admission_fee' THEN 'live_batch'
                           WHEN access_tier = 'live_batch' THEN 'live_batch'
                           WHEN (SELECT plan FROM payments WHERE razorpay_order_id=$2) = 'lectures_tests_upgrade' THEN 'full_recorded'
                           WHEN (SELECT plan FROM payments WHERE razorpay_order_id=$2) = 'lectures_upgrade' AND access_tier <> 'full_recorded' THEN 'lectures_only'
                           ELSE access_tier
                       END
                   WHERE id=$1""",
                row["user_id"], order_id,
            )
            await conn.execute(
                """UPDATE student_applications SET payment_status='paid', razorpay_order_id=$2
                   WHERE user_id=$1 AND payment_status <> 'paid'""",
                row["user_id"], order_id,
            )
            # Only email once per payment (skip if verify endpoint already sent)
            if not already_paid:
                pay_row = await conn.fetchrow(
                    """SELECT p.receipt, p.amount, p.plan, p.paid_at,
                              p.razorpay_payment_id, p.razorpay_order_id,
                              pr.name, pr.email, pr.phone_number, pr.batch_id
                       FROM payments p LEFT JOIN profiles pr ON pr.id = p.user_id
                       WHERE p.razorpay_order_id = $1""",
                    order_id,
                )
                if pay_row and pay_row["email"]:
                    try:
                        send_payment_receipt_email(
                            to_email=pay_row["email"],
                            to_name=pay_row["name"] or "Student",
                            receipt_data={
                                "receipt_no": pay_row["receipt"],
                                "payment_id": pay_row["razorpay_payment_id"],
                                "order_id": pay_row["razorpay_order_id"],
                                "paid_at_pretty": pretty_paid_at(pay_row["paid_at"]),
                                "amount_paise": pay_row["amount"],
                                "plan": pay_row["plan"],
                                "student_name": pay_row["name"],
                                "student_email": pay_row["email"],
                                "student_phone": pay_row["phone_number"],
                                "batch_code": pay_row["batch_id"],
                            },
                        )
                    except Exception as e:
                        logger.warning(f"Webhook receipt email failed: {e}")
        elif etype == "payment.failed":
            await conn.execute(
                "UPDATE payments SET status='failed', failed_at=NOW() WHERE razorpay_order_id=$1",
                order_id,
            )
    logger.info(f"Webhook processed: {etype} order={order_id}")
    return {"received": True, "matched": True, "event": etype}
