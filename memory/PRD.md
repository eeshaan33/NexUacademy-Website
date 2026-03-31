# NexUacademy - Product Requirements Document

## Original Problem Statement
Build a comprehensive JEE/NEET coaching platform with a Teacher Dashboard, Student Website, and browser-based Push Notification system. The platform serves both teachers (content creators) and students (learners) through a shared backend with role-based access.

## Tech Stack
- **Frontend:** React 18 + Tailwind CSS + shadcn/ui
- **Backend:** Python/FastAPI
- **Database:** MongoDB Atlas (DB: `nexuacademy`)
- **Auth:** Cookie-based sessions (httpOnly), Emergent-managed Google OAuth
- **Notifications:** Web Push (pywebpush), APScheduler for reminders

## User Personas
1. **Students** - Register, take tests, view classes, track performance
2. **Teachers** - Create tests/classes, view analytics (accounts created by admin only)
3. **Admin** - Create teacher accounts (hardcoded credentials)

## Core Architecture
```
/app
├── backend/ (FastAPI, port 8001)
│   ├── routes/ (auth, admin, teacher_*, student_*, batch, notification, push)
│   ├── middleware/auth.py (session-based auth, role guards)
│   ├── services/ (push, reminders)
│   └── config/ (database, batches)
└── frontend/ (React, port 3000)
    ├── pages/ (Login, Signup, AdminPanel, Dashboard)
    │   ├── teacher/ (TeacherDashboard, ManageClasses, CreateTest, StudentAnalytics)
    │   └── student/ (StudentClasses, AssignedTests, TakeTest, TestResults)
    ├── components/ (Layout, TeacherLayout, AuthCallback, NotificationBell)
    └── utils/ (api.js, pageTitle.js)
```

## What's Been Implemented

### Phase 1 - Core Platform (Completed)
- [x] Full Teacher Dashboard (classes CRUD, test creation, student analytics)
- [x] Student features (view classes, take tests, view results)
- [x] Push notification system + test reminders
- [x] Batch management (5 predefined batches)
- [x] Teacher notes visible only on incorrect/unattempted questions

### Phase 2 - Auth & Access (Completed - Feb 2026)
- [x] **Role-based auto-redirect**: Teachers → /teacher, Students → /dashboard
- [x] **Admin Panel** (/admin): Separate auth, create teacher accounts
  - Admin credentials: username=admin, password=nexuacademy123
- [x] **All page titles** updated to "NexUacademy"
- [x] **Signup restricted** to students only (teacher accounts admin-created)
- [x] **Google OAuth** with role-based redirect (Emergent-managed)

## Test Credentials
- Student: student@test.com / password123
- Teacher: teacher@test.com / password123
- Admin: username=admin / nexuacademy123

## Key API Endpoints
- `POST /api/admin/login` - Admin authentication
- `POST /api/admin/create-teacher` - Create teacher (admin only)
- `GET /api/admin/teachers` - List teachers (admin only)
- `POST /api/auth/login` - User login (returns role for redirect)
- `POST /api/auth/register` - Student registration only
- `POST /api/auth/google/session` - Google OAuth callback
- `GET /api/batches` - List predefined batches
- `POST /api/teacher/classes/create` - Create class
- `POST /api/teacher/tests/create` - Create test
- `GET /api/student/tests/assigned` - Student's assigned tests

## Prioritized Backlog

### P0 (Next Up)
- Class Reminder System (similar to test reminders)

### P1
- Detailed Student Analytics UI (graphs, heatmaps using recharts)
- Teacher: Detailed test results per student + CSV export

### P2
- Phase 2 Batch Management (teachers create custom batches)
- Student-facing "My Analytics" page
- Bookmarks feature
- Custom Test Builder (rebuild "My Tests")
- Leaderboards
- Study Plans
- Video Lecture sections

### Refactoring
- Create Pydantic models for Test, Class, TestAttempt, Notification
- Consider frontend state management (Zustand) for growing complexity
