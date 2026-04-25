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

### Phase 6 - Bookmarks, Pydantic & Custom Tests (Completed - Feb 2026)
- [x] **PYQ Bookmark Toggle** — Bookmark/BookmarkCheck icon on PYQ question viewer; uses `/api/bookmarks/ids` for fast toggle state.
- [x] **TestResults Bookmark Toggle** — Per-question bookmark on `/test-results/:attemptId` (for both correct & incorrect). Stores snapshot so bookmarks stay renderable.
- [x] **Unified Bookmarks Backend** — `{source, question_id | (test_id+question_number), snapshot}` model. Endpoints: `POST /bookmarks/`, `DELETE /bookmarks/by-question`, `GET /bookmarks/ids`, `GET /bookmarks/`, `DELETE /bookmarks/{id}`.
- [x] **Pydantic Request Validation** — New `models/requests.py` with `TestCreateRequest`, `QuestionAddRequest`, `TestUpdateRequest`, `ClassCreateRequest`. Invalid payloads now return 422 with field-level errors.
- [x] **Custom Test Builder** — `/my-tests` full flow: Home (history) → Wizard (Step 1: exam/difficulty/years/duration, Step 2: chapter picker with per-chapter count) → Generate → Ready screen → `/my-tests/take/:testId` test taker with timer + palette → Submit → results screen.

### Phase 7 - Admin Dashboard & Resume Flow (Completed - Feb 2026)
- [x] **Resume-in-progress Custom Test** — Server-side `test_sessions` collection tracks each active attempt with auto-expiry. Taker calls `start-session` on mount → resumes if active, creates fresh if not. Auto-save (1.5s debounce) via `save-progress`. `/my-tests` home surfaces a yellow "Resume Your Tests" card with remaining time.
- [x] **Admin 'Seed PYQ Bank'** — New `AdminPanel → PYQ Bank` tab with: total-questions stat + subject bar chart, Quick Seed Sample Pack (15-question rotating pool, 5-200 count), Bulk CSV Import (paste / download template / shows per-row errors), and a gated "Delete ALL" danger-zone button.
- [x] **Pydantic Refactor** extended to `custom_test_routes`, `question_routes`, `analytics_routes`, `admin_dashboard_routes`, `student_suggestion_routes`. New shared schemas: `QuestionAttemptRequest`, `PageViewRequest`, `CustomTestCreateRequest`, `CustomTestSubmissionRequest`, `SaveProgressRequest`, `BulkImportRequest`, `SuggestionCreateRequest`, `SuggestionUpdateRequest`.
- [x] **Admin Analytics Dashboard** — Route `/admin` (tab: Analytics). Page-view tracking via `PageViewTracker` component (silent POST to `/analytics/pageview` on every SPA route change). Charts: Most Visited Pages (bar), Daily Traffic (line), Device Breakdown (donut), Batch Distribution (bar). Stat cards (visits, uniques, users, new suggestions). Time-range filter (7/30/90/365). CSV export. Student suggestions moderation panel with status/priority filters + detail dialog (status, priority, admin notes, delete).
- [x] **Student Suggestion Box** — Global floating button (students only) → modal with Type/Subject/Message → submits to `/student/suggestions/`. Upvote toggle endpoint available.

### Phase 8 - CSV Validation, PYQ Browser, Content (Completed - Feb 2026)
- [x] **Rich CSV validation** — Bulk import now detects duplicates within a CSV batch AND vs existing DB rows (keyed by exam_type + subject + question_text). Normalises `question_image_url` (http(s) kept, bare filenames prefixed `/uploads/`, garbage dropped). Returns `inserted / duplicates_skipped / errors` with per-row details.
- [x] **Admin 'Browse PYQ Bank'** — New searchable/filterable table (exam, subject, chapter, year, difficulty, fuzzy text search), paginated with preview dialog (shows correct answer highlighted) and inline delete. Live-syncs to students (delete reflects immediately in `/api/questions/`).
- [x] **Landing content refresh** — Replaced fake testimonials with REAL student data (Harshit AIR 916 IIT Guwahati, Tanishq Saxena AIR 341 IIT Kharagpur, Samyak Rai INCHO Qualifier IIT Hyderabad). Added `VideoTestimonials` (3 YouTube Shorts with modal player), `RealResults` (achievement cards + summary stats), `YouTubeSection` (channel embed + Subscribe CTA). Added YouTube icon to social links footer.
- [x] **Sample Questions page** — New public `/sample-questions` route with 2 real JEE Advanced 2023 Chemistry questions (Dry Ice Sublimation, Raoult's Law) + locked-solution "Sign up for free" CTA.

### Phase 9 - Single-Question Creator & Dynamic Samples (Completed - Feb 2026)
- [x] **Admin Single-Question Creator** — In `AdminPanel → PYQ Bank` tab, new form to create one question at a time with all fields (exam, subject, chapter, year, difficulty, question text, 4 options, correct answer, explanation). Supports image upload via Emergent Object Storage (`/api/upload/image`) with preview. Includes an `is_sample` toggle to mark the question as a public sample.
- [x] **Dynamic Sample Questions API** — `/sample-questions` page now fetches questions from `GET /api/questions/samples` (returns all questions with `is_sample=True`). Public route, no auth needed. Falls back to static content if no sample questions exist.
- [x] **`is_sample` field on questions** — Added boolean property on `questions` collection; admin-controllable via both single-question creator and (future) bulk CSV flag.

### Phase 10 - Deployment Readiness (Completed - Feb 2026)
- [x] **N+1 Query Elimination** — `analytics_routes.get_subject_wise_performance`, `get_chapter_wise_performance`, `get_weak_topics`, and `test_routes.submit_test` now bulk-fetch all referenced questions in a single `$in` query and use an in-memory `question_map` for O(1) lookups. Prevents timeouts on large attempt datasets in production.
- [x] **Deployment Health Check Passed** — All checks green: env files OK, no hardcoded URLs/secrets, CORS configured, supervisor valid, auth redirects use `window.location.origin`, queries optimized.

### Phase 11 - Batch ID System, Profile Page & Connection Fixes (Completed - Feb 2026)
- [x] **Centralized batch system with alphanumeric Batch IDs** — New `services/batch_service.py` + `batches` collection. Predefined batches auto-seeded with deterministic codes (`JEEM2027`, `JEEM2028`, `JEEM2029`, `JEEA2027`, `JEEA2028`). Custom batches get auto-generated 8-char alphanumeric codes (O/I/0/1 excluded for clarity) or admin-supplied codes.
- [x] **Admin "Batches" tab in `/admin`** — Create/list/delete batches with copy-to-clipboard codes (`AdminBatchesPane.js`).
- [x] **Admission form joins by Batch ID** — Step 2 now shows a Batch ID input + Verify button (calls `/api/batches/by-code/{code}`). Verified batch auto-fills the course; user document is created with `batch_id`, `batch_code`, and a unique `roll_number`.
- [x] **Unique student roll numbers** — Format `NXU-<YY><6 alphanumeric>` (e.g. `NXU-26P7PABT`). Generated at admission time; backfilled on existing students at startup.
- [x] **Connection fix: tests/classes now reach students** — Root cause was admission flow never wrote `user.batch_id`. Fixed in `submit_admission`. `services/migrations.py` runs at backend startup and idempotently backfills 19 existing students with `batch_id` (from `admissions.course_applying`) and roll numbers.
- [x] **Connection fix: teacher Students filter** — "All batches" worked but per-batch filter returned 0 because no users had `batch_id`. Migration fixed it; teacher filter now returns the right students per batch.
- [x] **Notification fix in `push_service`** — `notify_students_about_class` and `notify_students_about_test` now ALWAYS create in-app notifications for every student in the assigned batch (web push subscription is now optional, not required).
- [x] **Profile page (`/profile`)** — New `ProfilePage.js` shows student avatar, name/email/role, copyable roll number + batch code, full personal/contact/academic details fetched from `GET /api/admissions/me`. Wired into avatar dropdown.
- [x] **Resume widget on student dashboard** — When a student logs back in, the dashboard now surfaces yellow "Resume Your Test" cards for in-progress attempts and an "Upcoming Classes" card with quick links — no auto-submit.
- [x] **`get_current_teacher` allows admins** — Admin can now create batches without a separate role-bypass.
- [x] **Landing page consistency** — Hero pill, stat card, founder bio, mentor card, and timeline all updated to "8+ Years Teaching" (was "7+"). Founder Skills tab: Thermodynamics now 100%.

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

### Questions (Admin / Public)
- `GET /api/questions/samples` - Public. Returns questions flagged `is_sample=True` for the `/sample-questions` landing page.
- `POST /api/questions/single` - Admin-only. Creates a single question with optional image URL and `is_sample` flag.

### Batches (Phase 11)
- `GET /api/batches/` - Public. Returns predefined + custom batches with `code` field.
- `GET /api/batches/by-code/{code}` - Public. Verify a Batch ID (used by admission form). 404 on invalid.
- `POST /api/batches/` - Teacher/Admin. Create a batch; auto-generates code if not supplied.
- `DELETE /api/batches/{batch_id}` - Teacher/Admin. Predefined batches non-deletable; cascades `users.batch_id=null` for any students assigned.
- `GET /api/admissions/me` - Student-only. Returns full profile (user + admission + batch) for the Profile page.

## Prioritized Backlog

### P1
- Phase 2 "Manage Students" UI (admin bulk-assign batch)
- UI polish: mobile profile button, hamburger menu transparency, minor copy changes

### P2
- Video Lectures section
- Study Plans (AI-powered recommendations via EMERGENT_LLM_KEY)
- Profile editing + avatar upload
- Share/challenge features for Leaderboard gamification
- Extend `is_sample` flag into bulk CSV importer

### Refactoring
- Delete legacy `services/class_reminders.py` (superseded by unified `reminder_scheduler.py`)
- Consolidate `tests` vs `teacher_tests` collections (two code paths exist)
- Break up `server.py` startup into `startup/` module
