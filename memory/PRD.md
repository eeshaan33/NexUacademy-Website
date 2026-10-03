# NexUacademy — Product Requirements & Status

## Original Problem Statement
Complete JEE/NEET platform with Teacher Dashboard, Student Site, Admin Panel, and highly advanced NTA-pattern tests. Supports admissions, live classes (Zoom), tests, payments (Razorpay), emails (Resend) and Supabase auth. 3-tier (Admin / Teacher / Student) with Nitin Saini as the lead teacher.

## Tech Stack
- Backend: Python / FastAPI
- Frontend: React (CRA + Craco) + Tailwind + Shadcn UI
- Database/Auth: Supabase (Postgres + Auth)
- Payments: Razorpay
- Live Classes: Zoom Meeting SDK
- Emails/OTP: Resend
- Deployment: Emergent

## Core Modules (all shipped)
- Admissions flow + fee payment
- Live classes with host/join + raised hands + attendance
- Tests (JEE Main & JEE Advanced patterns) with server-authoritative scoring, time-integrity guard, autosave
- Student dashboard: assigned tests, classes, analytics, bookmarks, profile
- Teacher dashboard: classes, tests, Question Bank (fixed hierarchy, Feb 2026)
- Admin panel: users, contacts export, applications, payments
- Email OTP on signup (Resend) + Admin Contacts CSV export

---

## Phase 17 (Feb 2026) — Fixed Question Bank Hierarchy + Test Analysis Dashboard

### What's new
- **Question Bank refactor** — moved from dynamic topics/subtopics to a **seeded fixed hierarchy** (`qb_folders` table). Legacy folders are pruned on each migration run. New structure:
  ```
  PYQ
    JEE
      JEE Mains        {Physics, Chemistry, Maths}
      JEE Advanced     {Physics, Chemistry, Maths}
    NEET               {Physics, Chemistry, Biology}
    Olympiads          {NSEP, NSEC, NSEB, NSEA, NSEJS}
  Non-PYQ              {Physics, Chemistry, Maths, Biology}
  ```
- **15 MB total image cap per question** (question + all option images), enforced on frontend (live progress bar + rejection) and backend (`MAX_TOTAL_IMAGE_BYTES`).
- **Difficulty values** restricted to `Easy` / `Moderate` / `Difficult`.
- **Create Test is bank-only** — manual-question path removed. Teachers must pick questions from the Question Bank folder tree, filtered by batch exclusion (already-assigned questions hidden).
- **Comprehensive Test Analysis Dashboard** at `/test-analysis/:attemptId` (route added in `App.js`) with 9 ordered sections:
  1. Score & Summary Bar
  2. Attempt & Accuracy Rate
  3. Rank & Percentile (with vs-previous deltas)
  4. Subject & Topic Breakdown (Strong > 80% / Moderate 50-80% / Weak < 50%)
  5. Question Type & Difficulty Analysis
  6. Time Management (Time Traps > 150s flagged, per-subject timing)
  7. Self-Reported Error Tagging (7 predefined tags + Careless % metric)
  8. Previous Test Comparison (score / accuracy / negative / attempt-rate deltas)
  9. Personalized Action Points (Top 3 Issues + Next-Test Goals)
- **Shared `QBFolderTree` component** (`/app/frontend/src/components/QBFolderTree.js`) — iterative-flatten tree to avoid babel plugin stack-overflow on recursive JSX.
- Opened Question Bank access to all teachers (previously allow-list of Nitin Saini only); legacy `teacher_has_question_bank()` kept as a shim.

### Key endpoints added
- `GET  /api/teacher/qb/folders` — nested folder tree with per-leaf question counts
- `POST /api/teacher/question-bank` — multipart create (15 MB total image guard)
- `GET  /api/teacher/question-bank?folder_id=...` — list questions in a leaf
- `GET  /api/teacher/question-bank/available?folder_ids=...&batch_codes=...` — bank picker with batch-exclusion
- `POST /api/teacher/question-bank/record-assignments` — track used questions per batch
- `GET  /api/student/tests/attempts/{attempt_id}/analysis` — full dashboard payload (null/zero safe)
- `POST /api/student/tests/attempts/{attempt_id}/error-tag` — set / clear self-reported error tag

### Key schema changes (migrations run on startup)
- `qb_folders` (self-referential tree, seeded with 25 fixed paths; prunes anything else)
- `question_bank.folder_id UUID` (new, FK to qb_folders)
- `question_bank.topic_id`, `question_bank.subtopic_id` now nullable (legacy only)
- Dropped old `question_bank_difficulty_check` constraint (now app-validated)
- `attempt_error_tags(attempt_id TEXT, question_number INT, error_tag TEXT, UNIQUE(attempt_id, qn))`

### Testing
- Iteration 29 report: 100% pass on 9 backend assertions + full frontend walkthrough (fixed folder tree, 15 MB UI budget, Difficulty select, bank-only CreateTest, Test Analysis page handles bad attempt id).

---

## Pending / Backlog

### P1
- **SMS OTP Verification** — expand email-only OTP on signup to also offer SMS (Twilio or similar — needs user confirmation of provider).

### P2
- **Question Bank Bulk Upload** — CSV + zipped images batch upload per leaf folder.
- **Duplicate Text Check (Question Bank)** — warn if a similar question text already exists in the bank before saving.
- **Referral Rewards** — admitted-student referral code → fee discount for the referrer.
- **Receipt Audit Log** — `receipt_email_status` column + admin view.
- **Dismiss All Banners** — single-click dismiss when multiple live classes go live.
- **Seed a submitted student attempt** so the Test Analysis dashboard renders populated UI in CI.
- **Delete / Edit question** UI inside Browse page (API already supports deletion with batch-assignment guard).

### P0 (production blocker — waiting on user)
- Add `RESEND_API_KEY` and `SENDER_EMAIL` to the live `nexuacademy.com` deployment and redeploy so OTP works in prod. (Preview is unaffected — fully working.)

---

## Credentials (also in /app/memory/test_credentials.md)
- Teacher: `nitinsaini.iitkgp@gmail.com` / `nitin@123`
- Admin: `admin@nexuacademy.com` / `admin@2026`
- Student (preseeded roster): first_name lowercase + batch year (e.g. `arjun2027`)
