# NexUacademy - Product Requirements Document

## Original Problem Statement
Build a comprehensive JEE/NEET coaching platform with a Teacher Dashboard, Student Website, browser-based Push Notification system, and a professional marketing landing page. The platform serves students (learners), teachers (content creators, admin-managed), and admin (teacher account management).

## Tech Stack
- **Frontend:** React 18 + Tailwind CSS + shadcn/ui + Framer Motion
- **Backend:** Python/FastAPI
- **Database:** MongoDB Atlas (DB: `nexuacademy`)
- **Auth:** Cookie-based sessions (httpOnly), Emergent-managed Google OAuth
- **Notifications:** Web Push (pywebpush), APScheduler for reminders

## User Personas
1. **Students** - Register, take tests, view classes, track performance
2. **Teachers** - Create tests/classes, view analytics (accounts created by admin only)
3. **Admin** - Create teacher accounts, view contact inquiries (login: admin@nexuacademy.com / nexuacademy123)

## Core Architecture
```
/app
├── backend/ (FastAPI, port 8001)
│   ├── routes/ (auth, admin, teacher_*, student_*, batch, notification, push)
│   ├── middleware/auth.py (session-based auth, role guards)
│   ├── services/ (push, reminders)
│   └── config/ (database, batches)
└── frontend/ (React, port 3000)
    ├── pages/
    │   ├── LandingPage.js (marketing page at /landing)
    │   ├── Login.js, Signup.js, AdminPanel.js, Dashboard.js
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

### Phase 2 - Auth & Access (Completed - Mar 2026)
- [x] Role-based auto-redirect: Admin -> /admin, Teachers -> /teacher, Students -> /dashboard
- [x] Admin login via main login page (admin@nexuacademy.com / nexuacademy123)
- [x] Admin Panel: Create teacher accounts + view contact inquiries
- [x] All page titles updated to "NexUacademy"
- [x] Signup restricted to students only
- [x] Google OAuth with role-based redirect

### Phase 3 - Landing Page & Contact (Completed - Mar 2026)
- [x] Full marketing landing page at /landing
  - Hero section with founder photo + CTA buttons
  - About section (6 feature cards)
  - Courses section (4 course cards: JEE Mains, JEE Advanced, NEET, Olympiad)
  - Founder section with Nitin Saini's photos + bio
  - Founder detail modal with 5 tabs (Journey, Education, Achievements, Skills, Philosophy)
  - Testimonials carousel
  - CTA section with stats counters
  - Contact form (stores to DB)
  - Footer with social links + contact info
- [x] Contact form: Saves inquiries to MongoDB, viewable in admin panel
- [x] Admin panel "Inquiries" tab: View + mark as responded
- [x] Scroll-to-top button, smooth scrolling, animations
- [x] "Visit Platform" button -> /login
- [x] Root URL / redirects to /landing for unauthenticated users

## Test Credentials
- Student: student@test.com / password123
- Teacher: teacher@test.com / password123
- Admin: admin@nexuacademy.com / nexuacademy123

## Key API Endpoints
- `POST /api/auth/login` - User login (returns role for redirect)
- `POST /api/auth/register` - Student registration only
- `POST /api/admin/create-teacher` - Create teacher (admin auth required)
- `GET /api/admin/teachers` - List teachers (admin auth required)
- `POST /api/admin/contact` - Submit contact form (public)
- `GET /api/admin/contacts` - List contact inquiries (admin auth required)
- `PUT /api/admin/contacts/{id}/status` - Mark inquiry responded (admin auth required)
- `GET /api/batches` - List predefined batches

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
