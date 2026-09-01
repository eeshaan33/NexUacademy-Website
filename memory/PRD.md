# NexUacademy - Product Requirements & State (Phase 13)

## Overview
JEE/NEET learning platform with Teacher Dashboard, Student Portal, Admin Panel,
embedded Zoom live classes, batch-targeted content, Razorpay-powered admission
fees, and analytics dashboards.

## Current Stack
- **Backend**: Python 3 / FastAPI + `asyncpg` + Supabase Postgres + Auth
- **Frontend**: React + Tailwind + shadcn + Supabase JWT (localStorage)
- **Storage**: Supabase Storage (`question-images` public bucket)
- **Auth**: Supabase Auth (email/password + Google OAuth)
- **Live video**: Zoom Meeting SDK (Web SDK, client view, embedded)
- **Zoom API**: Server-to-Server OAuth for meeting create/delete/participants
- **Payments**: Razorpay (test keys wired) — create-order → checkout → verify (HMAC-SHA256) → DB + webhook

## Phase 13 (Feb 2026) — Payments + Analytics
- Razorpay integration: `/api/payments/{create-order, verify, my, webhook}` + `payments` table + `profiles.payment_status`. Verify endpoint enforces ownership (order.user_id must match caller).
- AdmissionForm success now routes to `/fee-structure` (₹30,000 one-time) → opens Razorpay Checkout → verifies signature → redirects to /dashboard.
- Webhook signature-verified when `RAZORPAY_WEBHOOK_SECRET` is set (dev-mode bypass when empty).
- Analytics re-ported: `/api/analytics/{dashboard, subject-wise, admin/overview}`.
- Student `/analytics` page: 6 stat cards + subject-wise accuracy bars.
- Admin panel new default tab "Analytics" with revenue, batch distribution, recent signups, recent payments.

## Phase 12 (Feb 2026) — MongoDB → Supabase migration
See prior sections; 37/37 tests passed after Supabase cutover.

## What's implemented (full list)
✅ Auth (login/signup/me/logout/Google OAuth URL)
✅ Batches (JEEM2027, NEX2027, NEX2028 seeded + admin CRUD with alphanumeric codes)
✅ Admissions (batch-code verify → auto-create user + profile + admission + roll_number)
✅ Classes (teacher/student, batch-filtered)
✅ Live Classes (Zoom SDK create + host/attendee join + raise-hand)
✅ Tests + Attempts (resume-on-existing in_progress)
✅ Questions with option-images (jsonb)
✅ Announcements (batch-targeted + in-app notifications)
✅ Notifications
✅ Uploads → Supabase Storage
✅ Contacts (landing form)
✅ **Payments (Razorpay)** — new in Phase 13
✅ **Analytics (student + admin)** — new in Phase 13
✅ Profile page (roll number, batch, personal details)

## Deferred / Not yet re-ported
- PYQ browser & bulk CSV seeder
- Custom Test builder
- Bookmarks
- Suggestion moderation
- Teacher CRUD in admin panel (creating teacher accounts)
- Page-view analytics middleware
- Test reminder scheduler (email)

## Test Credentials
See `/app/memory/test_credentials.md`.

## Verified via Testing Agent
- iter14: 32/37 (3 blockers)
- iter15: 37/37 (Supabase migration solid)
- iter16: **18/18 (Razorpay + Analytics all green)**
- iter17: Zoom live-class end-to-end (teacher create/start/end/participants/lower-hand/delete + student list/join/raise-hand/lower-hand + host_zak + signature roles)

## Session Feb-2026 wrap
- Fixed pre-completion oxlint blocker in `frontend/public/service-worker.js` (`clients.openWindow` → `self.clients.openWindow`).

## External to-do (not code)
1. Set `RAZORPAY_WEBHOOK_SECRET` in prod after configuring the webhook in Razorpay Dashboard (Settings → Webhooks → Add URL `<REACT_APP_BACKEND_URL>/api/payments/webhook`, events: payment.captured, payment.failed, order.paid). Currently empty → dev mode.
2. Enable Google OAuth provider in Supabase Dashboard (Client ID/Secret already shared by user).
3. Add Zoom S2S scopes `user:read:token`, `dashboard:read:list_meeting_participants:admin`, `meeting:delete:meeting:admin` for full participants panel + delete-meeting.

## Backlog
- P1: Re-port PYQ Bank + CSV seeder
- P2: Shareable batch join links `/join/JEEM2027`
- P2: Real-time "live now" banner via Supabase Realtime  *(currently polling every 30 s in `LiveNowBanner`)*
- P2: Bookmarks + Custom Test builder + Teacher-CRUD admin flow

## Phase 14 (Feb 2026) — Score integrity + Live Now + Receipt emails
- **Server-side score verification** — `services/scoring.py` recomputes correctness from `tests.questions` (MCQ_Single, MCQ_Multiple, Numerical Integer/Decimal with `answer_range` tolerance). Client `is_correct` is discarded. `negative_marks` is clamped to `<=0` defensively. Idempotent submit + `total_score`/`max_score` persisted.
- **Autosave endpoint** — `PUT /api/student/tests/attempts/{id}/autosave` (matches the JEEMainInterface 30 s cadence).
- **Live Now banner** — `LiveNowBanner` mounted inside `Layout`; polls `/student/live-classes/` every 30 s (pauses when tab hidden), shows red pulsing bar with a "Join Now" CTA whenever any is_live=true class is assigned to the student's batch. Session-persisted dismiss per class_id.
- **Branded PDF payment receipts** — `services/receipt_service.py` builds an A4 receipt (reportlab) and sends it via Resend. Dispatched via **FastAPI BackgroundTasks** on `POST /payments/verify` so /verify latency stays fast; also dispatched from webhook `payment.captured` / `order.paid` with a `already_paid` dedupe.

## Verified via Testing Agent
- iter14: 32/37 · iter15: 37/37 · iter16: 18/18 · iter17: 20/20 · **iter18: 50/50 (12 new + 38 regression)**
- P2: Shareable batch join links `/join/JEEM2027`
- P2: Real-time "live now" banner via Supabase Realtime
- P2: Bookmarks + Custom Test builder + Teacher-CRUD admin flow
