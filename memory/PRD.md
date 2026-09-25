# NexUacademy - Product Requirements & State (Phase 16)

## Overview
JEE/NEET learning platform with Teacher Dashboard, Student Portal, Admin Panel,
embedded Zoom live classes, batch-targeted content, Razorpay-powered admission
fees, tier-based access control, and analytics dashboards.

## Current Stack
- **Backend**: Python 3 / FastAPI + `asyncpg` + Supabase Postgres + Auth
- **Frontend**: React + Tailwind + shadcn + Supabase JWT (localStorage)
- **Storage**: Supabase Storage (`question-images` public bucket)
- **Auth**: Supabase Auth (email/password + Google OAuth)
- **Live video**: Zoom Meeting SDK (Web SDK, client view, embedded)
- **Zoom API**: Server-to-Server OAuth for meeting create/delete/participants
- **Payments**: Razorpay (test keys wired) — create-order → checkout → verify (HMAC-SHA256) → DB + webhook
- **Emails**: Resend + branded PDF receipts (reportlab)

## Phase 16 (Feb 2026) — Streamlined admission + Preseed claim + Tier system + Upgrade packs + Bugfix pass
- **3-field admission form** — `AdmissionForm.js` rewritten. Public form now
  takes only Full Name, Email, WhatsApp Number → auto-creates auth user with
  a generated password (`firstname_lower + last4(whatsapp)`) → sign in → redirect
  to `/fee-structure` for the ₹30,000 Razorpay flow.
- **First-Time Setup for enrolled students** — new `/first-time-setup` page.
  21 pre-enrolled students (19 NEX2027 + 2 NEX2028) live in
  `public.preseed_students`. Claim = first_name (case-insensitive) + fresh
  email + batch. Default password = `firstname_lower + batchYear` (e.g.,
  `arjun2027`). On success: `profiles.access_tier='live_batch'`, 
  `is_existing_student=true`, session tokens returned, password displayed once.
- **Tier column** — `profiles.access_tier` (`free`, `lectures_only`,
  `full_recorded`, `live_batch`). Server-side `PLAN_CATALOG` in
  `payment_routes.py` maps plan → price → granted tier. Client-supplied
  amounts are ignored for upgrade plans (only admission_fee honours env override).
- **₹1,500 Lectures Pack (Phase 16)** — plan=`lectures_upgrade` → tier `lectures_only`.
- **₹2,500 Lectures + Tests Pack (Phase 16)** — plan=`lectures_tests_upgrade` → tier `full_recorded`.
- **/upgrade page + navbar CTA (Phase 16)** — visible to students whose
  tier != `live_batch`. Hidden for admin/teacher and for already-full-tier users.
- **student@test.com moved from JEEM2027 → NEX2027** (seed_service).
- **Google OAuth redirect** — `/auth/google/url` now accepts `?redirect_to=`
  query param and the frontend passes `window.location.origin/auth/callback`
  explicitly (fixes callback landing on `localhost:3000` on prod).

### Bugfix pass iter23/iter24 (Feb 2026)
- **Class list 404** — Fixed. Frontend called `GET /teacher/classes/` and
  `GET /teacher/classes/stats` but backend only exposed `/my-classes` and
  `/stats/summary`. Added root aliases on both teacher and student class
  routers. Teacher can now see their scheduled classes; students in the
  correct batch see them too.
- **Tier refresh after paid admission** — Fixed. `FeeStructure.js` now
  awaits `checkAuth()` after `/payments/verify` succeeds so AuthContext
  refreshes `access_tier` from `free` → `live_batch` before the redirect.
- **JEEM2027 cleanup** — New idempotent migration `cleanup_batches()` in
  `services/migration_service.py` moved all 7 profiles from JEEM2027 → NEX2027.
  Now NEX2027 has 17 students, NEX2028 has 2, JEEM2027 has 0.
- **Removed dead file** — `src/pages/ClassesPage.js` was never mounted in
  the router but confused the testing agent — deleted.

## New DB tables (Phase 16, auto-created by migration_service on startup)
- `public.student_applications` — 3-field public applications ledger
- `public.preseed_students` — whitelist of enrolled students eligible for
  `/first-time-setup` (idempotent seed of 21 rows)
- `public.profiles.access_tier`, `is_existing_student`, `whatsapp_number` — new columns

## What's implemented (full list)
✅ Auth (login/signup/me/logout/Google OAuth URL)
✅ **3-field New Student Application → Razorpay ₹30,000 → live_batch tier** (Phase 16)
✅ **First-Time Setup for enrolled students (21 preseeded)** (Phase 16)
✅ **profiles.access_tier column + auto-grant live_batch on paid admission** (Phase 16)
✅ Batches (JEEM2027, NEX2027, NEX2028 seeded + admin CRUD)
✅ Classes (teacher/student, batch-filtered)
✅ Live Classes (Zoom SDK create + host/attendee join + raise-hand)
✅ Tests + Attempts (server-authoritative scoring, time-guard)
✅ Questions with option-images
✅ Announcements (batch-targeted + in-app notifications)
✅ Notifications
✅ Uploads → Supabase Storage
✅ Contacts (landing form)
✅ Payments (Razorpay) with branded PDF email receipts
✅ Analytics (student + admin)
✅ Profile page (roll number, batch, personal details)
✅ Route-level code splitting (React.lazy)

## Deferred / Not yet re-ported
- Free-tier paywall UI (₹1,500 / ₹2,500 upgrade packs) — user asked to
  defer for now; backend `access_tier` column already exists.
- PYQ browser & bulk CSV seeder
- Custom Test builder / Bookmarks
- Suggestion moderation
- Teacher CRUD in admin panel
- Page-view analytics middleware
- Test reminder scheduler

## Test Credentials
See `/app/memory/test_credentials.md`.

## Verified via Testing Agent
- iter14: 32/37 · iter15: 37/37 · iter16: 18/18 · iter17: 20/20 · iter18: 50/50
- iter20: 5/5 · iter21: 14/14 · iter22: 13/13 · iter23: 8/9 + partial FE
- iter24: 100% (classes bugfix regression)
- **iter25: 100% (9/9 backend + full frontend) — pre-deploy readiness pass**

## Phase 17 (Feb 2026) — YouTube latest video + pre-deploy hardening
- **`/api/youtube/latest`** — new endpoint in `routes/youtube_routes.py` that
  resolves the channel_id from `@NexUacademypvtltd` handle, hits the public
  RSS feed (`/feeds/videos.xml?channel_id=UC…`), extracts the newest video's
  ID + title, and caches 1 hour in-memory. No API key required.
- **YouTubeSection.js** — landing page now embeds the actual latest video
  (`prxtAAGvBcM` — "Aldehyde & Ketone ONE SHOT") with the fetched title as
  the heading; falls back to a static known-good embed if the API fails.
- **Pre-deploy Zoom E2E** — teacher schedule → student list → teacher start
  → LiveNowBanner shows on all pages within 30 s poll → student join with
  Zoom signature → teacher end → is_live reverts. Verified end-to-end.

## Phase 18 (Feb 2026) — Class-scheduling flow diagnostic
- User reported classes not appearing on Teacher/Student pages after schedule.
- Full DB + API + UI trace executed (iteration_26 test report):
  - Backend curl: teacher POST /api/teacher/classes/create inserts row with
    `assigned_batches=['NEX2027']`, class returned in GET /api/teacher/classes/.
  - Student GET /api/student/classes/my-classes matches by `$1 = ANY(assigned_batches)`
    where `$1 = auth user's batch_id (NEX2027)` → new class visible.
  - Playwright UI test: Teacher scheduled a class via /teacher/classes, card
    rendered immediately and after reload; student on /classes saw it in
    'Upcoming & Live' section. 100% pass, no code changes needed for the bug.
- Fixed silent error swallowing in ManageClasses.js and StudentClasses.js —
  now toast + console.error on load failure so this never presents as a
  false "class missing" symptom again.
- **RCA: not reproducible in preview.** The user's report almost certainly
  reflects the un-deployed production build (nexuacademy.com), which still
  runs pre-Phase-16 code. A redeploy will resolve the perceived bug.


## External to-do (not code)
1. Set `RAZORPAY_WEBHOOK_SECRET` in prod after configuring the webhook in
   Razorpay Dashboard (`payment.captured`, `payment.failed`, `order.paid`).
2. Enable Google OAuth provider in Supabase Dashboard (Client ID/Secret ready).
   Ensure Redirect URI `<PROD>/auth/callback` is whitelisted.
3. Redeploy to `nexuacademy.com` — login on prod was reported broken; the
   preview backend has always worked. A redeploy will pick up the new
   preseed migration + moved student batch + 3-field form.

## Backlog / Roadmap
- P1: Free-tier paywall UI (`₹1,500` unlocks all lectures, `₹2,500` unlocks
      lectures + all chapter tests) → wire to `access_tier`
- P1: Free lecture gating (one free lecture per Class 11 / Class 12) —
      needs `class_level` on classes table
- P1: Free chapter-test gating (one free test per chapter)
- P2: Receipt audit log (`receipt_email_status` column)
- P2: Referral rewards (discount code for admitted students)
- P2: Dismiss-all live-now banners
- P2: Shareable batch join links `/join/JEEM2027`
- P2: Bookmarks + Custom Test builder + Teacher-CRUD admin flow
- P2: Bulk-upload questions to bank (CSV + zipped images)
- P2: Duplicate-question warning on save

## Phase 20 (Feb 2026) — Solution enrichment + Email OTP + Central Contacts
- **Question Bank solution/hint upgrade** (`question_bank` table):
  - New columns: `solution_youtube_url` (paste `youtu.be/…?t=N` link with
    timestamp → student sees a red "Go to YouTube" button in the modal)
  - `solution_media_url` + `solution_media_type` ('image'|'video') — teacher
    can drag-and-drop an image (≤5 MB) or a short MP4/WebM (≤25 MB) that
    renders inline in the browse modal and in the student's solution view.
  - Uploader helper `_upload_media()` writes to the `question-bank-images`
    bucket under `<user_id>/solution/<uuid>`. Both image and video are
    stored in the same public bucket.
- **Email OTP verification** (Resend, shared with receipt_service):
  - New tables: `auth_otps` (email, code_hash sha256, purpose in
    signup/login, JSON payload, attempts, expires_at, verified_at) and
    `trusted_devices` (user_id + device_id unique).
  - `profiles` gains `phone`, `email_verified_at`, `phone_verified_at`.
  - Endpoints (`/api/auth/otp/…`):
    - `POST /start-signup`  → collect name/email/phone/password/batch,
      write OTP + payload, email code
    - `POST /verify-signup` → creates Supabase Auth user (bcrypt-hashed
      by Supabase), writes profile with `email_verified_at`, auto-trusts
      the signup device, returns tokens
    - `POST /verify-login`  → after new-device password login, verifies
      email code and trusts the device, returns tokens
    - `POST /resend-login`  → rate-limited resend button on the OTP screen
  - `POST /api/auth/login` now reads `X-Device-Id` header. Unknown device
    → returns `{requires_otp: true, email}` and fires an email. Missing
    header (legacy clients) → returns tokens (backward compat).
  - `services/otp_email.py` — branded HTML template with the 6-digit code.
  - **⚠️ Resend deliverability**: keys set, but the Resend account is in
    "testing mode" — only mails to the account owner deliver. To email real
    users, verify a domain at resend.com/domains and change `SENDER_EMAIL`
    to something like `noreply@nexuacademy.com`.
  - **SMS OTP intentionally deferred** — Signup screen has a phone field
    and stores it; user chose "skip SMS for now, add later".
- **Central contacts store** (single source of truth = `profiles`):
  - `GET /api/admin/contacts` — JSON list (admin-only, 403 otherwise)
  - `GET /api/admin/contacts/export.csv` — CSV of name/email/phone/role/
    batch/verified-stamps/signup-date
  - `AdminContactsPane` — new tab in the admin panel with live search,
    verification badges, and one-click CSV download.
- **Frontend wiring**:
  - `api.js` now sends `X-Device-Id` (stable per-browser UUID in
    localStorage) on every request — Emergent Google OAuth is naturally
    excluded because it bypasses `/api/auth/login`.
  - `AuthContext` gained `startSignupOtp`, `verifySignupOtp`,
    `verifyLoginOtp`, `resendLoginOtp` helpers; `login()` returns
    `{requires_otp: true}` instead of tokens when the device is new.
  - `Signup.js` — 2-step form (details → 6-digit code), phone required.
  - `Login.js` — OTP challenge screen shown only when backend requests it.

## Backlog / Roadmap
- P1: SMS OTP (Twilio / MSG91 / Fast2SMS) — user picked "add later"
- P1: Domain verification on Resend so OTP emails deliver to any address
- P1: Free-tier paywall UI wired to `access_tier`
- P2: Referral rewards + dismiss-all live banners + receipt audit log
- P2: Bulk-upload questions to bank (CSV + zipped images)
- P2: Duplicate-question detection at save time

## Phase 19 (Feb 2026) — Question Bank + Smart Test Creation (Nitin Saini)
- **Teacher seeded**: `nitin@nexuacademy.com` / `nitin@123` (bcrypt-hashed by
  Supabase Auth) — added to `seed_service.SEEDS`.
- **Feature flag**: `routes/question_bank_routes.QUESTION_BANK_TEACHERS`
  (allow-list of teacher emails; admins bypass). Exposed on the client via
  `user.features.question_bank` from both `/auth/login` and `/auth/me`.
- **New tables (empty at boot, populated organically by teacher):**
  - `topics` (unique name, subject, created_by)
  - `subtopics` (topic-scoped unique name)
  - `question_bank` (topic_id + subtopic_id + MCQ/Numerical, options JSONB,
    correct_answers[], difficulty, marks, negative_marks, teacher_note)
  - `question_batch_assignments` (question_id + batch_code UNIQUE — "used
    with which batch" ledger, powers the per-batch smart exclusion)
  - Storage bucket `question-bank-images` (public, created lazily).
- **Backend routes** (`/api/teacher/...`, gated to allow-listed teachers):
  - `GET/POST /topics`, `GET /topics/{id}/subtopics`, `POST /subtopics` —
    all case-insensitive create-or-return (no silent duplicates)
  - `POST /question-bank` (multipart: question image + 4 option images)
  - `GET /question-bank`, `GET /question-bank/tree`,
    `GET /question-bank/{id}`, `PUT /question-bank/{id}`
  - `DELETE /question-bank/{id}` (409 if assignments exist; `?force=true` overrides)
  - `GET /question-bank/available?topic_ids=&subtopic_ids=&batch_codes=` —
    per-batch fresh/used arrays; hides questions already used for every
    requested batch
  - `POST /question-bank/record-assignments` — CreateTest calls this after
    inserting bank questions so the ledger "remembers" the pairing
- **Frontend pages**:
  - `/teacher/question-bank` — collapsible tree Topics → Subtopics →
    Questions with counts, live search, empty state, modal preview
  - `/teacher/question-bank/new` — searchable combobox topic/subtopic with
    inline "+ Create" (subject picker for new topics); drag-and-drop image
    upload (question + per-option) with click-to-browse fallback; MCQ/
    Numerical support; keeps topic+subtopic selected after save for rapid
    entry with an "+ Add Another to <subtopic>" shortcut.
  - `/teacher/tests` — new **bank picker step** between config & manual;
    surfaces available questions given the chosen topic × subtopic × batch,
    shows "N available, M already used with these batches, hidden" and per-
    question "Fresh for X / Already used for Y" badges in multi-batch mode.
    Publishing creates the test with bank questions embedded AND inserts
    ledger rows for each (question, batch) pair.
- **Sidebar**: "Question Bank" nav item shown only when
  `user.features.question_bank === true`. Navy #1B3A52 theme applied to
  all new pages.
- **Verified**: iter28 backend 9/9 pytest + frontend E2E (topic-inline
  create, subtopic-inline create, image drop, MCQ save, tree render,
  search, bank picker per-batch exclusion, test creation with assignment
  persistence). Post-testing HIGH bug fixed: `/auth/login` now hydrates
  `user.features` so the sidebar renders instantly (no reload).

