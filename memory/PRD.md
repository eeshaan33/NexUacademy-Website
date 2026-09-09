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

## Phase 16 (Feb 2026) — Streamlined admission + Preseed claim + Tier system + Upgrade packs
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
- **Google OAuth redirect** — `/auth/google/url` now prefers SITE_URL / FRONTEND_URL
  over REACT_APP_BACKEND_URL for the callback redirect (fixes production
  callback going to the wrong domain).

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
- iter20: 5/5 (time-guard) · iter21: 14/14 (admission/claim) · **iter22: 13/13 (upgrade packs)**

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
