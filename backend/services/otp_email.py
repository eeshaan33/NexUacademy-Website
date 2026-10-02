"""Send OTP codes via Resend (best-effort, non-blocking)."""
import logging
import os

import resend

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, code: str, purpose: str = "verification") -> dict:
    """Send a branded OTP email via Resend.

    Returns a dict so the caller can decide how to handle failures:
      - {"ok": True,  "id": <resend_id>}
      - {"ok": False, "error": <message>, "status_code": <int|None>, "name": <resend_err_name|None>}
    """
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    sender = (os.environ.get("SENDER_EMAIL") or "").strip() or "NexUacademy <info@nexuacademy.com>"
    reply_to = (os.environ.get("REPLY_TO_EMAIL") or "info@nexuacademy.com").strip()
    if not api_key:
        return {"ok": False, "error": "RESEND_API_KEY not configured on the server", "status_code": None, "name": "missing_api_key"}
    if not to_email:
        return {"ok": False, "error": "Missing recipient", "status_code": None, "name": "missing_to"}

    # Expiry depends on purpose — the generic email_verify flow uses 5 min, auth flows use 10 min.
    expiry_minutes = 5 if purpose == "email_verify" else 10
    subject = {
        "signup": f"NexUacademy — Your verification code {code}",
        "login": f"NexUacademy — New device login code {code}",
        "email_verify": f"Your NexUacademy verification code: {code}",
    }.get(purpose, f"NexUacademy — Your verification code {code}")
    heading = {
        "signup": "Welcome to NexUacademy! 👋",
        "login": "New device sign-in",
        "email_verify": "Verify your email",
    }.get(purpose, "Your verification code")
    body_line = {
        "signup": "Use the code below to finish setting up your account.",
        "login": "We noticed a sign-in from a new device. Confirm it's you with the code below.",
        "email_verify": "Use this one-time code to verify your email address.",
    }.get(purpose, "Use this one-time code to continue.")

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; max-width: 480px; margin: auto; padding: 32px 24px; color: #0f172a;">
      <div style="text-align:center; margin-bottom: 24px;">
        <div style="display:inline-block; background:#1B3A52; color:#fff; font-size: 22px; font-weight: 700; padding: 10px 20px; border-radius: 10px;">NexUacademy</div>
      </div>
      <h2 style="font-size: 22px; margin: 0 0 8px 0;">{heading}</h2>
      <p style="color:#475569; font-size: 15px; line-height: 1.5;">{body_line}</p>
      <div style="background:#f1f5f9; border: 2px dashed #1B3A52; border-radius: 12px; padding: 20px; margin: 24px 0; text-align:center;">
        <div style="font-size: 12px; color:#64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">Verification Code</div>
        <div style="font-size: 34px; font-weight: 700; letter-spacing: 0.4em; color:#1B3A52;">{code}</div>
      </div>
      <p style="color:#64748b; font-size: 13px;">This code expires in <b>{expiry_minutes} minutes</b>. If you didn't request it, you can safely ignore this email.</p>
      <hr style="border:none; border-top:1px solid #e2e8f0; margin: 24px 0;" />
      <p style="color:#94a3b8; font-size: 12px; text-align:center;">© NexUacademy · Auto-generated, please don't reply.<br/>Questions? Email <a href="mailto:{reply_to}" style="color:#1B3A52;">{reply_to}</a>.</p>
    </div>
    """
    # Plain-text version is critical for deliverability — Gmail flags HTML-only
    # messages as spam/promotions, especially from fresh domains.
    text = (
        f"NexUacademy — {heading}\n\n"
        f"{body_line}\n\n"
        f"Your verification code is: {code}\n\n"
        f"This code expires in {expiry_minutes} minutes. If you didn't request it, you can "
        "safely ignore this email.\n\n"
        f"— NexUacademy ({reply_to})"
    )

    try:
        resend.api_key = api_key
        res = resend.Emails.send({
            "from": sender,
            "to": to_email,
            "reply_to": reply_to,
            "subject": subject,
            "html": html,
            "text": text,
            # Standards-compliant headers that materially improve inbox placement
            "headers": {
                "List-Unsubscribe": f"<mailto:{reply_to}?subject=unsubscribe>",
                "X-Entity-Ref-ID": "nexuacademy-otp",
            },
            "tags": [{"name": "category", "value": f"otp_{purpose}"}],
        })
        if isinstance(res, dict) and res.get("id"):
            return {"ok": True, "id": res["id"]}
        if isinstance(res, dict) and res.get("error"):
            err = res["error"]
            return {"ok": False, "error": err.get("message", str(err)),
                    "status_code": err.get("statusCode"), "name": err.get("name")}
        logger.warning(f"Resend returned unexpected shape: {res!r}")
        return {"ok": False, "error": f"Unexpected Resend response: {res!r}", "status_code": None, "name": "unexpected"}
    except Exception as e:
        status = getattr(e, "status_code", None) or getattr(e, "code", None)
        name = getattr(e, "name", None) or type(e).__name__
        msg = getattr(e, "message", None) or str(e)
        logger.warning(
            f"Resend OTP email failed for {to_email}: name={name} status={status} message={msg}"
        )
        return {"ok": False, "error": msg, "status_code": status, "name": name}


def get_resend_email_status(email_id: str) -> dict:
    """Fetch the delivery status of a previously-sent email directly from Resend.

    Returns the raw Resend payload including `last_event` which can be one of:
      queued | scheduled | sent | delivered | delivery_delayed | bounced |
      complained | failed | opened | clicked.
    """
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        return {"ok": False, "error": "RESEND_API_KEY not configured"}
    import httpx
    try:
        with httpx.Client(timeout=10) as c:
            r = c.get(f"https://api.resend.com/emails/{email_id}",
                      headers={"Authorization": f"Bearer {api_key}"})
        if r.status_code != 200:
            return {"ok": False, "error": r.text, "status_code": r.status_code}
        body = r.json()
        return {"ok": True, "last_event": body.get("last_event"),
                "to": body.get("to"), "from": body.get("from"),
                "subject": body.get("subject"),
                "created_at": body.get("created_at")}
    except Exception as e:
        return {"ok": False, "error": str(e)}
