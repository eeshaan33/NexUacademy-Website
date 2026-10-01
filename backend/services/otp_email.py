"""Send OTP codes via Resend (best-effort, non-blocking)."""
import logging
import os

import resend

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, code: str, purpose: str = "verification") -> bool:
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    sender = (os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev").strip()
    if not api_key or not to_email:
        logger.info("Resend not configured or missing recipient; skipping OTP email")
        return False
    # Expiry depends on purpose — the generic email_verify flow uses 5 min, auth flows use 10 min.
    expiry_minutes = 5 if purpose == "email_verify" else 10
    subject = {
        "signup": "NexUacademy — Verify your email",
        "login": "NexUacademy — New device login code",
        "email_verify": "Your NexUacademy Verification Code",
    }.get(purpose, "NexUacademy — Your verification code")
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
      <p style="color:#94a3b8; font-size: 12px; text-align:center;">© NexUacademy · Auto-generated, please don't reply.</p>
    </div>
    """
    try:
        resend.api_key = api_key
        resend.Emails.send({
            "from": sender,
            "to": to_email,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.warning(f"Resend OTP email failed for {to_email}: {e}")
        return False
