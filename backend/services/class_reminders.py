"""
Email Reminder Service for Live Classes
Sends automated reminders 24h, 1h, and 15 mins before class
"""
import asyncio
import os
import logging
import resend
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')

def get_class_reminder_email(student_name: str, class_details: dict, reminder_type: str) -> str:
    """Generate HTML email for class reminder"""
    
    scheduled_dt = class_details.get("scheduled_datetime")
    if isinstance(scheduled_dt, str):
        scheduled_dt = datetime.fromisoformat(scheduled_dt.replace('Z', '+00:00'))
    
    date_str = scheduled_dt.strftime("%A, %B %d, %Y")
    time_str = scheduled_dt.strftime("%I:%M %p")
    
    reminder_text = {
        "24h": "📅 Reminder: Your class is scheduled for tomorrow!",
        "1h": "⏰ Starting Soon: Your class begins in 1 hour!",
        "15m": "🚨 Starting Now: Your class begins in 15 minutes!"
    }.get(reminder_type, "Class Reminder")
    
    subject_colors = {
        "Physics": "#3B82F6",
        "Chemistry": "#10B981",
        "Mathematics": "#EF4444",
        "General": "#8B5CF6"
    }
    subject_color = subject_colors.get(class_details.get("subject", "General"), "#667eea")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 28px;">🎓 JEE Master</h1>
        <h2 style="margin: 15px 0 0 0; font-size: 18px; font-weight: normal;">{reminder_text}</h2>
      </div>
      
      <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="margin: 0 0 20px 0;">Hi <strong>{student_name}</strong>,</p>
        
        <p style="margin: 0 0 20px 0;">This is a friendly reminder about your upcoming class:</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {subject_color};">
          <div style="margin-bottom: 15px;">
            <span style="color: #6b7280; font-size: 12px;">CLASS TITLE</span><br>
            <span style="font-size: 20px; font-weight: bold; color: #1f2937;">{class_details.get("title", "Untitled Class")}</span>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
              <span style="color: #6b7280; font-size: 12px;">📚 SUBJECT</span><br>
              <span style="font-weight: bold;">{class_details.get("subject", "General")}</span>
            </div>
            <div>
              <span style="color: #6b7280; font-size: 12px;">👨‍🏫 TEACHER</span><br>
              <span style="font-weight: bold;">{class_details.get("teacher_name", "Teacher")}</span>
            </div>
            <div>
              <span style="color: #6b7280; font-size: 12px;">📅 DATE</span><br>
              <span style="font-weight: bold;">{date_str}</span>
            </div>
            <div>
              <span style="color: #6b7280; font-size: 12px;">🕐 TIME</span><br>
              <span style="font-weight: bold;">{time_str}</span>
            </div>
            <div>
              <span style="color: #6b7280; font-size: 12px;">⏱️ DURATION</span><br>
              <span style="font-weight: bold;">{class_details.get("duration", 60)} minutes</span>
            </div>
            <div>
              <span style="color: #6b7280; font-size: 12px;">📹 PLATFORM</span><br>
              <span style="font-weight: bold;">{class_details.get("meeting_platform", "Zoom")}</span>
            </div>
          </div>
          
          {f'<div style="margin-top: 15px;"><span style="color: #6b7280; font-size: 12px;">📝 DESCRIPTION</span><br><span>{class_details.get("description")}</span></div>' if class_details.get("description") else ''}
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="{class_details.get("meeting_link", "#")}" 
             style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
            🎥 Join Class Now
          </a>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin: 20px 0;">
          💡 <strong>Tip:</strong> Join the class 5 minutes early to check your audio and video settings.
        </p>
        
        <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px;">
          <p style="margin: 0; color: #0369a1; font-size: 14px;">
            📌 <strong>Meeting Link:</strong> 
            <a href="{class_details.get("meeting_link", "#")}" style="color: #0369a1;">{class_details.get("meeting_link", "Not available")}</a>
          </p>
        </div>
      </div>
      
      <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
        <p>JEE Master - Your Path to IIT Success</p>
        <p>If you have any questions, contact us at support@jeemaster.com</p>
      </div>
    </body>
    </html>
    """

async def send_class_reminder(class_id: str, reminder_type: str):
    """Send reminder email to all students"""
    
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not configured - skipping email send")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get class details
        class_details = await db.classes.find_one({"class_id": class_id})
        if not class_details:
            logger.error(f"Class not found: {class_id}")
            return
        
        # Get all students
        students = await db.users.find(
            {"role": "student"},
            {"email": 1, "name": 1}
        ).to_list(length=1000)
        
        sent_count = 0
        for student in students:
            if not student.get("email"):
                continue
            
            try:
                html_content = get_class_reminder_email(
                    student.get("name", "Student"),
                    class_details,
                    reminder_type
                )
                
                subject_prefix = {
                    "24h": "Tomorrow",
                    "1h": "In 1 Hour",
                    "15m": "Starting Soon"
                }.get(reminder_type, "Reminder")
                
                params = {
                    "from": SENDER_EMAIL,
                    "to": [student["email"]],
                    "subject": f"Class Reminder: {class_details.get('title')} - {subject_prefix}",
                    "html": html_content
                }
                
                await asyncio.to_thread(resend.Emails.send, params)
                sent_count += 1
                logger.info(f"Reminder sent to {student['email']} for class {class_details['title']}")
                
            except Exception as e:
                logger.error(f"Failed to send email to {student.get('email')}: {e}")
        
        # Mark reminder as sent
        reminder_field = {
            "24h": "reminders_sent.one_day_before",
            "1h": "reminders_sent.one_hour_before",
            "15m": "reminders_sent.fifteen_mins_before"
        }.get(reminder_type)
        
        if reminder_field:
            await db.classes.update_one(
                {"class_id": class_id},
                {"$set": {reminder_field: True}}
            )
        
        logger.info(f"Sent {sent_count} reminders for class {class_id} ({reminder_type})")
        
    finally:
        client.close()

async def check_and_send_reminders():
    """Check for classes needing reminders and send them"""
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        now = datetime.now(timezone.utc)
        
        # Find upcoming classes
        upcoming_classes = await db.classes.find({
            "status": {"$ne": "cancelled"},
            "scheduled_datetime": {"$gt": now}
        }).to_list(length=100)
        
        for cls in upcoming_classes:
            scheduled_dt = cls.get("scheduled_datetime")
            if scheduled_dt.tzinfo is None:
                scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
            
            time_until = (scheduled_dt - now).total_seconds()
            hours_until = time_until / 3600
            mins_until = time_until / 60
            
            reminders = cls.get("reminders_sent", {})
            
            # 24 hours before
            if 23 <= hours_until <= 24 and not reminders.get("one_day_before"):
                await send_class_reminder(cls["class_id"], "24h")
            
            # 1 hour before
            if 0.75 <= hours_until <= 1 and not reminders.get("one_hour_before"):
                await send_class_reminder(cls["class_id"], "1h")
            
            # 15 minutes before
            if 10 <= mins_until <= 15 and not reminders.get("fifteen_mins_before"):
                await send_class_reminder(cls["class_id"], "15m")
        
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
    finally:
        client.close()

async def start_reminder_scheduler():
    """Start the reminder scheduler (runs every 5 minutes)"""
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            logger.error(f"Reminder scheduler error: {e}")
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    asyncio.run(check_and_send_reminders())
