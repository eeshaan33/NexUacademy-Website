# NexUacademy - JEE Preparation Platform PRD

## Original Problem Statement
Build a complete JEE preparation web application named "NexUacademy" with:
- Teacher Dashboard for managing classes, tests, and student analytics
- Student Website for attending classes, taking tests, and viewing PYQs
- Browser Push Notifications for real-time updates
- All data in MongoDB Atlas

## Tech Stack
- **Backend:** Python/FastAPI + Motor (async MongoDB driver)
- **Frontend:** React 19 + Tailwind CSS + shadcn/ui
- **Database:** MongoDB Atlas (cloud)
- **Auth:** Session-based (httpOnly cookies) + Google OAuth (Emergent Auth)
- **Push:** Web Push API + VAPID keys + pywebpush

## Core Architecture
```
/app
├── backend/
│   ├── server.py                    # FastAPI main server
│   ├── .env                         # MongoDB Atlas, VAPID keys, JWT
│   ├── config/
│   │   ├── database.py              # MongoDB connection
│   │   ├── batches.py               # Predefined batches
│   │   └── syllabus.py              # JEE syllabus data
│   ├── middleware/auth.py           # Session auth + role middleware
│   ├── routes/
│   │   ├── auth_routes.py           # Login, register, Google OAuth
│   │   ├── teacher_class_routes.py  # Teacher class CRUD
│   │   ├── teacher_test_routes.py   # Teacher test CRUD + questions
│   │   ├── teacher_student_routes.py# Teacher student analytics
│   │   ├── student_class_routes.py  # Student class view + attendance
│   │   ├── student_test_routes.py   # Student test taking + results
│   │   ├── notification_routes.py   # In-app notifications
│   │   ├── push_routes.py           # Push subscription
│   │   ├── batch_routes.py          # Predefined batches API
│   │   ├── question_routes.py       # PYQ questions
│   │   └── ... (other existing routes)
│   └── services/
│       ├── push_service.py          # VAPID push notifications
│       └── email_service.py
├── frontend/
│   ├── src/
│   │   ├── App.js                   # All routes (teacher + student)
│   │   ├── components/
│   │   │   ├── Layout.js            # Student layout + notification bell
│   │   │   ├── TeacherLayout.js     # Teacher sidebar layout
│   │   │   ├── NotificationBell.js  # Notification dropdown
│   │   │   └── ui/                  # shadcn components
│   │   ├── pages/
│   │   │   ├── teacher/
│   │   │   │   ├── TeacherDashboard.js   # Stats + quick actions
│   │   │   │   ├── ManageClasses.js      # Schedule/edit/delete classes
│   │   │   │   ├── CreateTest.js         # Multi-step test creation
│   │   │   │   └── StudentAnalytics.js   # Student performance
│   │   │   ├── student/
│   │   │   │   ├── StudentClasses.js     # View assigned classes
│   │   │   │   ├── AssignedTests.js      # View assigned tests
│   │   │   │   ├── TakeTest.js           # Test-taking interface
│   │   │   │   └── TestResults.js        # Results with teacher notes
│   │   │   └── ... (existing pages)
│   │   └── context/AuthContext.js
│   └── public/service-worker.js     # Push notification handler
```

## What's Been Implemented

### Phase 1 - Completed (March 17, 2026)
**Teacher Dashboard + Student Features + Push Notifications**
- Complete teacher dashboard with stats cards, class management, test creation, student analytics
- Multi-step test creation form with question-by-question entry and teacher notes
- Teacher notes hidden during test, shown ONLY after submission for incorrect/unattempted answers
- Student class viewing with auto-refresh every 30 seconds  
- Student test-taking interface with timer, question palette, flagging
- Test results page with detailed question-wise review
- In-app notification bell with unread count (both layouts)
- VAPID push notification infrastructure
- Service worker for browser push notifications
- Predefined batch system (6 JEE batches: 2027/2028/2029 Morning/Evening)
- Updated signup page with batch selector dropdown
- Teacher login redirects to teacher dashboard
- Role-based access control (teacher/student middleware)

### Previously Completed
- Database migration to MongoDB Atlas (13k+ questions)
- Full rebranding to "NexUacademy" with custom logo
- PYQ Section with subject/chapter filtering
- JWT + Google OAuth authentication
- Admission form with course selection
- Student dashboard with stats

## Predefined Batches
- JEE-2027-Morning, JEE-2027-Evening
- JEE-2028-Morning, JEE-2028-Evening
- JEE-2029-Morning, JEE-2029-Evening

## Key Database Collections
- **users**: user_id, email, name, role, batch_id, push_subscription, notifications_enabled
- **classes**: class_id, title, subject, teacher_id, meeting_link, scheduled_date_time, assigned_batches, attendance
- **teacher_tests**: test_id, test_name, questions (with teacher_note), assigned_batches, status
- **test_attempts**: attempt_id, test_id, student_id, answers, total_score, status
- **notifications**: user_id, type, title, message, is_read
- **questions**: 13k+ PYQ questions

## Test Credentials
- Teacher: teacher@test.com / password123
- Student: student@test.com / password123 (batch: JEE-2027-Morning)

## Testing Status
- Backend: 19/19 tests passed (100%)
- Frontend: All UI tests passed (100%)
- E2E flow verified: Teacher creates test -> Student takes test -> Results with teacher notes

## P0/P1/P2 Backlog

### P0 (Critical)
- Data quality from PDF parsing (missing images, malformed text in PYQ)

### P1 (Important)
- Chapter/Topic sorting in PYQ section
- Google Sheets sync for live classes
- Analytics page (student self-analytics)

### P2 (Nice to have)
- Bookmarks page implementation
- Custom test builder (My Tests - currently placeholder)
- Teacher-created batches (beyond predefined)
- Leaderboards
- Study plans / AI recommendations
- Video lectures integration
- Download results as CSV for teachers
