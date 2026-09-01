"""Branded PDF admission-fee receipt + Resend email delivery."""
import io
import logging
import os
from datetime import datetime, timezone

import resend
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)

BRAND = "#E6A817"  # NexUacademy amber
INK = "#0F172A"    # slate-900
MUTED = "#64748B"  # slate-500

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=22,
                    textColor=colors.HexColor(INK), spaceAfter=4,
                    fontName="Helvetica-Bold")
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                    textColor=colors.HexColor(BRAND), spaceAfter=6,
                    fontName="Helvetica-Bold")
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10,
                      textColor=colors.HexColor(INK), leading=14)
SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor(MUTED), leading=11)


def build_receipt_pdf(data: dict) -> bytes:
    """Render a PDF receipt to bytes.

    `data` keys: receipt_no, payment_id, order_id, paid_at (iso), amount_paise,
    plan, student_name, student_email, student_phone, batch_code.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=f"NexUacademy Receipt {data.get('receipt_no','')}")

    story = []
    # Brand strip
    strip = Table([[""]], colWidths=[170 * mm], rowHeights=[3 * mm])
    strip.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(BRAND))]))
    story.append(strip)
    story.append(Spacer(1, 8))

    story.append(Paragraph("NexUacademy", H1))
    story.append(Paragraph("JEE / NEET Excellence · nexuacademy.com", SMALL))
    story.append(Spacer(1, 14))

    story.append(Paragraph("PAYMENT RECEIPT", H2))
    meta = [
        ["Receipt No.", data.get("receipt_no", "—")],
        ["Payment ID", data.get("payment_id", "—")],
        ["Order ID",   data.get("order_id", "—")],
        ["Paid on",    data.get("paid_at_pretty", "—")],
        ["Status",     "PAID"],
    ]
    t = Table(meta, colWidths=[35 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor(INK)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Billed to", H2))
    bill = [
        ["Name",  data.get("student_name") or "—"],
        ["Email", data.get("student_email") or "—"],
        ["Phone", data.get("student_phone") or "—"],
        ["Batch", data.get("batch_code") or "—"],
    ]
    t2 = Table(bill, colWidths=[35 * mm, 120 * mm])
    t2.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(MUTED)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Order summary", H2))
    amount_paise = int(data.get("amount_paise") or 0)
    amount_rupees = amount_paise / 100
    plan_label = "Admission Fee" if data.get("plan") == "admission_fee" else (data.get("plan") or "Fee")
    rows = [
        ["Description", "Amount"],
        [plan_label, f"₹ {amount_rupees:,.2f}"],
        ["Total (INR)", f"₹ {amount_rupees:,.2f}"],
    ]
    t3 = Table(rows, colWidths=[110 * mm, 45 * mm])
    t3.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 11),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FEF3C7")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
    ]))
    story.append(t3)
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "This is a computer-generated receipt. No signature required. "
        "For queries, write to <font color='#E6A817'>support@nexuacademy.com</font>.",
        SMALL,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Thank you for choosing NexUacademy. Wishing you the very best for JEE / NEET 2027.", BODY))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def send_payment_receipt_email(*, to_email: str, to_name: str, receipt_data: dict) -> bool:
    """Send the branded PDF receipt via Resend. Returns True on success.

    Fails silently (logs a warning) so payment verification never breaks
    even if Resend is misconfigured — the payment itself is already recorded.
    """
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    sender = (os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev").strip()
    if not api_key or not to_email:
        logger.info("Resend not configured or missing recipient; skipping receipt email")
        return False

    try:
        pdf_bytes = build_receipt_pdf(receipt_data)
        resend.api_key = api_key
        amount_rupees = int(receipt_data.get("amount_paise") or 0) / 100
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#0F172A">
          <div style="background:#E6A817;height:6px;border-radius:6px 6px 0 0"></div>
          <div style="padding:24px;background:#fff;border:1px solid #E5E7EB;border-top:none;border-radius:0 0 8px 8px">
            <h1 style="margin:0 0 6px;color:#0F172A;font-size:22px">Payment received ✅</h1>
            <p style="color:#64748B;margin:0 0 18px">Hi {to_name}, your admission fee has been received. Your receipt is attached below.</p>
            <table style="width:100%;font-size:14px;line-height:1.6">
              <tr><td style="color:#64748B;width:40%">Amount</td><td><b>₹ {amount_rupees:,.2f}</b></td></tr>
              <tr><td style="color:#64748B">Receipt No.</td><td>{receipt_data.get('receipt_no','—')}</td></tr>
              <tr><td style="color:#64748B">Payment ID</td><td>{receipt_data.get('payment_id','—')}</td></tr>
              <tr><td style="color:#64748B">Paid on</td><td>{receipt_data.get('paid_at_pretty','—')}</td></tr>
            </table>
            <p style="color:#64748B;margin-top:24px;font-size:12px">This is a computer-generated email. Reach us anytime at support@nexuacademy.com.</p>
          </div>
        </div>
        """
        resend.Emails.send({
            "from": f"NexUacademy <{sender}>",
            "to": [to_email],
            "subject": f"Your NexUacademy admission-fee receipt ({receipt_data.get('receipt_no','')})",
            "html": html,
            "attachments": [{
                "filename": f"NexUacademy-Receipt-{receipt_data.get('receipt_no','')}.pdf",
                "content": list(pdf_bytes),
            }],
        })
        return True
    except Exception as e:
        logger.warning(f"Resend receipt email failed: {e}")
        return False


def pretty_paid_at(iso_or_dt) -> str:
    if not iso_or_dt:
        iso_or_dt = datetime.now(timezone.utc)
    if isinstance(iso_or_dt, str):
        try:
            dt = datetime.fromisoformat(iso_or_dt.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = iso_or_dt
    return dt.strftime("%d %b %Y, %I:%M %p")
