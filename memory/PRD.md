# NexUacademy - Product Requirements Document

## Original Problem Statement
Build a comprehensive JEE/NEET coaching platform with a Teacher Dashboard, Student Website, browser-based Push Notification system, professional marketing landing page, and NTA-pattern JEE Main & Advanced test interfaces. The platform serves students, teachers (admin-managed), and admin.

## Tech Stack
- **Frontend:** React 18 + Tailwind CSS + shadcn/ui + Framer Motion + react-katex + recharts
- **Backend:** Python/FastAPI
- **Database:** MongoDB Atlas (DB: `nexuacademy`)
- **Auth:** Cookie-based sessions, Emergent-managed Google OAuth
- **Notifications:** Web Push (pywebpush) + Email (Resend) + APScheduler
- **Storage:** Emergent Object Storage
- **Math Rendering:** KaTeX

## User Personas
1. **Students** - Register, take tests (JEE Main/Advanced UI), view classes, track performance
2. **Teachers** - Create tests/classes with batch assignment, view detailed analytics & per-test results (accounts created by admin only)
3. **Admin** - Create teacher accounts, view contact inquiries

## Core Architecture
```
/app
├── backend/ (FastAPI, port 8001)
│   ├── routes/ (auth, admin, teacher_*, student_*, batch, notification, push, upload, student_analytics)
│   ├── middleware/auth.py (cookie + bearer; role guards)
│   ├── services/ (push_service, reminder_scheduler [unified], class_reminders, email_service, storage_service)
│   └── config/ (database, batches, syllabus)
└── frontend/ (React, port 3000)
    ├── pages/
    │   ├── LandingPage.js, Login.js, Signup.js, AdminPanel.js, Dashboard.js
    │   ├── BookmarksPage.js
    │   ├── teacher/ (TeacherDashboard, ManageClasses, CreateTest, StudentAnalytics, TestResultsDetail)
    │   └── student/ (StudentClasses, AssignedTests, TakeTest, JEEMainInterface, JEEAdvancedInterface, TestResults, AnalyticsDashboard)
    ├── components/ (Layout, TeacherLayout, AuthCallback, NotificationBell, ProtectedRoute, BatchManagerDialog)
    └── utils/ (api.js, pageTitle.js)
```

## What's Been Implemented

### Phase 1 - Core Platform (Completed)
- [x] Teacher Dashboard (classes CRUD, test creation, student analytics)
- [x] Student features (view classes, take tests, view results)
- [x] Push notification system
- [x] Batch management (5 predefined batches)
- [x] Teacher notes visible on incorrect/unattempted

### Phase 2 - Auth & Access (Completed)
- [x] Role-based auto-redirect & Admin Panel with Logout
- [x] Google OAuth + role-based redirect
- [x] Signup restricted to students only

### Phase 3 - Landing Page & Contact (Completed)
- [x] Marketing landing page with Framer Motion animations, founder, testimonials, contact form

### Phase 4 - NTA-Pattern Test Interfaces (Completed)
- [x] JEE Main (orange) & JEE Advanced (blue) interfaces with KaTeX + object storage images
- [x] SmartTestRouter
- [x] Test Results page handling `{text, imageUrl}` options + KaTeX
- [x] Pattern badges on AssignedTests & teacher test list

### Phase 5 - Engagement & Insights (Completed - Feb 2026)
- [x] **Unified Reminder Scheduler** — 24h / 1h / 15m reminders for BOTH tests & classes, delivered via in-app + Web Push + Email (Resend). Idempotent via `sent_reminders` collection.
- [x] **Student Analytics Dashboard** — Overview stats + 30-day activity chart + Chapter×Subject heatmap + Batch Leaderboard + Insights (best/worst test, weak chapters).
- [x] **Teacher Test Results Detail** — Ranked per-student attempts table with search, per-question difficulty chart, aggregate stats (avg score/accuracy, highest, lowest), and one-click **CSV export**.
- [x] **Custom Batch Management** — Teachers can create/delete their own batches via `BatchManagerDialog`; predefined batches remain. Merge-view in `/batches/`.
- [x] **Real Bookmarks Page** — Search + remove your saved questions; empty state links back to PYQ.

## Test Credentials
- Student: student@test.com / password123 (batch: JEE Mains 2027)
- Teacher: teacher@test.com / password123
- Admin: admin@nexuacademy.com / nexuacademy123

## Key API Endpoints
### Analytics (Student)
- `GET /api/student/analytics/overview` - stats + best/worst test + batch_rank
- `GET /api/student/analytics/heatmap` - subject/chapter accuracy
- `GET /api/student/analytics/activity` - 30 buckets (solved, correct)
- `GET /api/student/analytics/leaderboard` - top 25 of batch

### Teacher Results
- `GET /api/teacher/tests/{id}/results` - enriched attempts, stats, question_stats
- `GET /api/teacher/tests/{id}/results.csv` - CSV download (teacher-only)

### Batches
- `GET /api/batches/` - predefined + custom (merged)
- `POST /api/batches/` - teacher creates custom batch (name, year)
- `DELETE /api/batches/{id}` - teacher deletes own batch (predefined blocked)

### Existing
- `/api/auth/*`, `/api/admin/*`, `/api/teacher/{classes,tests,students}/*`, `/api/student/{classes,tests}/*`, `/api/upload/image`, `/api/push/*`, `/api/bookmarks/*`

## Prioritized Backlog

### P1
- Pydantic models refactor across all write endpoints (test create, class create, question add)
- Student PYQ bookmarking flow (button on PYQ questions + from TestResults)

### P2
- Phase 2 "Manage Students" UI (admin assign batch in bulk)
- Custom Test Builder rebuild (currently placeholder)
- Video Lectures section
- Study Plans (AI-powered recommendations via EMERGENT_LLM_KEY)
- Profile editing

### Refactoring
- Consolidate two reminder services (`class_reminders.py` can be deleted; `reminder_scheduler.py` now covers both)
- Break up `server.py` startup logic into `startup/` module (minor)
