"""
Email service for sending admission confirmation emails using Resend
"""
import os
import asyncio
import logging
import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

def get_admission_confirmation_email(student_name: str, admission_id: str, email: str, course: str) -> str:
    """Generate HTML content for admission confirmation email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border-radius: 10px 10px 0 0;">
            <tr>
                <td style="padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">NexUacademy</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Your Gateway to IIT</p>
                </td>
            </tr>
        </table>
        
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
            <tr>
                <td>
                    <h2 style="color: #1f2937; margin: 0 0 20px 0;">Welcome, {student_name}! 🎉</h2>
                    
                    <p style="margin: 0 0 15px 0;">
                        Congratulations! Your admission application has been successfully submitted to NexUacademy.
                    </p>
                    
                    <table width="100%" cellpadding="15" cellspacing="0" style="background: white; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb;">
                        <tr>
                            <td style="border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #6b7280;">Admission ID</strong><br>
                                <span style="font-size: 20px; font-weight: bold; color: #1e3a5f;">{admission_id}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="border-bottom: 1px solid #e5e7eb;">
                                <strong style="color: #6b7280;">Course Applied</strong><br>
                                <span style="font-size: 16px; color: #1f2937;">{course}</span>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <strong style="color: #6b7280;">Email</strong><br>
                                <span style="font-size: 16px; color: #1f2937;">{email}</span>
                            </td>
                        </tr>
                    </table>
                    
                    <p style="margin: 20px 0 15px 0;">
                        <strong>What's Next?</strong>
                    </p>
                    <ul style="margin: 0 0 20px 0; padding-left: 20px;">
                        <li style="margin-bottom: 8px;">Your account has been automatically created</li>
                        <li style="margin-bottom: 8px;">Login with your email and the password you set during registration</li>
                        <li style="margin-bottom: 8px;">Start practicing with our comprehensive PYQ database</li>
                        <li style="margin-bottom: 8px;">Track your progress on your personalized dashboard</li>
                    </ul>
                    
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="text-align: center; padding: 20px 0;">
                                <a href="#" style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                                    Start Learning Now
                                </a>
                            </td>
                        </tr>
                    </table>
                    
                    <p style="color: #6b7280; font-size: 14px; margin: 20px 0 0 0; text-align: center;">
                        Please save your Admission ID for future reference.<br>
                        If you have any questions, contact us at support@nexuacademy.com
                    </p>
                </td>
            </tr>
        </table>
        
        <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
                    © 2025 NexUacademy. All rights reserved.<br>
                    This is an automated email. Please do not reply.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

async def send_admission_confirmation_email(
    student_name: str,
    email: str,
    admission_id: str,
    course: str
) -> dict:
    """Send admission confirmation email to student"""
    
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not configured - skipping email send")
        return {"status": "skipped", "message": "Email service not configured"}
    
    html_content = get_admission_confirmation_email(
        student_name=student_name,
        admission_id=admission_id,
        email=email,
        course=course
    )
    
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": f"Welcome to NexUacademy! Your Admission ID: {admission_id}",
        "html": html_content
    }
    
    try:
        # Run sync SDK in thread to keep FastAPI non-blocking
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent successfully to {email}: {result.get('id', 'unknown')}")
        return {
            "status": "success",
            "message": f"Confirmation email sent to {email}",
            "email_id": result.get("id")
        }
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }
