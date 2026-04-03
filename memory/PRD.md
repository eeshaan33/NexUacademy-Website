# NexUacademy - Product Requirements Document

## Original Problem Statement
Build a comprehensive JEE/NEET coaching platform with a Teacher Dashboard, Student Website, browser-based Push Notification system, and a professional marketing landing page. The platform serves students (learners), teachers (content creators, admin-managed), and admin (teacher account management).

## Tech Stack
- **Frontend:** React 18 + Tailwind CSS + shadcn/ui + Framer Motion + react-katex
- **Backend:** Python/FastAPI
- **Database:** MongoDB Atlas (DB: `nexuacademy`)
- **Auth:** Cookie-based sessions (httpOnly), Emergent-managed Google OAuth
- **Notifications:** Web Push (pywebpush), APScheduler for reminders
- **Storage:** Emergent Object Storage (for question/option images)
- **Math Rendering:** KaTeX (react-katex) for LaTeX formulas

## User Personas
1. **Students** - Register, take tests (JEE Main/Advanced UI), view classes, track performance
2. **Teachers** - Create tests/classes with batch assignment, view analytics (accounts created by admin only)
3. **Admin** - Create teacher accounts, view contact inquiries (login: admin@nexuacademy.com / nexuacademy123)

## Core Architecture
```
/app
├── backend/ (FastAPI, port 8001)
│   ├── routes/ (auth, admin, teacher_*, student_*, batch, notification, push, upload)
│   ├── middleware/auth.py (session-based auth, role guards)
│   ├── services/ (push, reminders, storage_service)
│   └── config/ (database, batches)
└── frontend/ (React, port 3000)
    ├── pages/
    │   ├── LandingPage.js (marketing page at /landing)
    │   ├── Login.js, Signup.js, AdminPanel.js, Dashboard.js
    │   ├── teacher/ (TeacherDashboard, ManageClasses, CreateTest, StudentAnalytics)
    │   └── student/ (StudentClasses, AssignedTests, TakeTest, JEEMainInterface, JEEAdvancedInterface, TestResults)
    ├── components/ (Layout, TeacherLayout, AuthCallback, NotificationBell, ProtectedRoute)
    └── utils/ (api.js, pageTitle.js)
```

## What's Been Implemented

### Phase 1 - Core Platform (Completed)
- [x] Full Teacher Dashboard (classes CRUD, test creation, student analytics)
- [x] Student features (view classes, take tests, view results)
- [x] Push notification system + test reminders
- [x] Batch management (5 predefined batches)
- [x] Teacher notes visible only on incorrect/unattempted questions

### Phase 2 - Auth & Access (Completed)
- [x] Role-based auto-redirect: Admin -> /admin, Teachers -> /teacher, Students -> /dashboard
- [x] Admin login via main login page
- [x] Admin Panel: Create teacher accounts + view contact inquiries
- [x] Google OAuth with role-based redirect
- [x] Signup restricted to students only

### Phase 3 - Landing Page & Contact (Completed)
- [x] Full marketing landing page at /landing with Framer Motion animations
- [x] Founder section, testimonials, courses, contact form
- [x] Contact form saves to DB, viewable in admin panel

### Phase 4 - NTA Pattern Test Interfaces (Completed - Apr 2026)
- [x] **JEE Main Interface** - Orange-themed NTA UI with:
  - Subject tabs, question palette, timer, candidate info
  - MCQ Single/Multiple, Numerical Integer/Decimal question types
  - Action buttons: SAVE & NEXT, SAVE & MARK FOR REVIEW, CLEAR RESPONSE, MARK FOR REVIEW & NEXT
  - Auto-save every 30 seconds, auto-submit on time expiry
  - Custom submit confirmation modal (no double window.confirm)
- [x] **JEE Advanced Interface** - Blue/Indigo-themed UI with:
  - Section-wise tabs (Physics - Sec A, Chemistry - Sec B, etc.)
  - Question Navigator grouped by subject
  - MCQ Multiple with "One or More Correct" badge
  - All JEE Main features plus section navigation
- [x] **SmartTestRouter** - Automatically routes students to correct interface based on test_pattern
- [x] **KaTeX Math Rendering** - In questions, options, and results page
- [x] **Emergent Object Storage** - Image uploads for questions and options
- [x] **Test Results Page** - Fixed to handle new option format {text, imageUrl}, KaTeX rendering, Numerical answer display
- [x] **Pattern Badges** - Orange/Blue badges on AssignedTests and teacher test list
- [x] **Teacher Test Creator** - Pattern selection (JEE Main / JEE Advanced), question types, image upload, batch assignment
- [x] **Batch Filtering** - Tests and classes correctly filtered by student's batch

## Test Credentials
- Student: student@test.com / password123 (batch: JEE Mains 2027)
- Teacher: teacher@test.com / password123
- Admin: admin@nexuacademy.com / nexuacademy123

## Key API Endpoints
- `POST /api/auth/login` - User login (returns role for redirect)
- `POST /api/auth/register` - Student registration only
- `POST /api/admin/create-teacher` - Create teacher (admin auth required)
- `POST /api/teacher/tests/create` - Create test with pattern selection
- `POST /api/teacher/tests/{id}/add-question` - Add question to test
- `PUT /api/teacher/tests/{id}/publish` - Publish test and notify students
- `GET /api/student/tests/assigned` - Batch-filtered assigned tests
- `POST /api/student/tests/{id}/start` - Start test (returns test_pattern)
- `PUT /api/student/tests/attempts/{id}/autosave` - Auto-save progress
- `POST /api/student/tests/attempts/{id}/submit` - Submit test
- `GET /api/student/tests/results/{id}` - Get enriched results
- `GET /api/student/classes/my-classes` - Batch-filtered classes
- `POST /api/upload/image` - Upload image to Emergent Object Storage
- `GET /api/batches/` - List predefined batches

## Prioritized Backlog

### P1
- Class Reminder System (24h, 1h, 15min email/push notifications)
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
