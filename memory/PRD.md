# NexUacademy - Product Requirements & State (Phase 12)

## Overview
JEE/NEET learning platform with Teacher Dashboard, Student Portal, Admin Panel,
embedded Zoom live classes, batch-targeted content, and a stunning landing page.

## Current Stack (Phase 12 — Feb 2026)
- **Backend**: Python 3 / FastAPI, `asyncpg` connection pool, Supabase Postgres + Auth
- **Frontend**: React (Tailwind + shadcn), Supabase JWT stored in localStorage
- **Storage**: Supabase Storage (public bucket `question-images`)
- **Auth**: Supabase Auth (email/password + Google OAuth)
- **Live video**: Zoom Meeting SDK (Web SDK, client view, embedded)
- **Zoom API**: Server-to-Server OAuth for meeting create/delete/participants

## Migration History
- **Phase 11** — Batch IDs, Profile page, connection fixes on MongoDB
- **Phase 12 (Feb 2026)** — Full migration MongoDB → Supabase Postgres:
  - All Motor code removed; `config/database.py` now exposes an `asyncpg` pool + `supabase-py` clients (`get_supabase()` anon fresh-per-call, `get_supabase_admin()` service role).
  - Schema in `backend/schema.sql`: batches (reference table w/ FK) + normalize triggers (`UPPER(TRIM(...))` on batch_id / assigned_batches / codes), profiles (1:1 with `auth.users` + auto-create trigger), admissions, classes (with Zoom + is_live + assigned_batches text[]), tests, questions (options jsonb with per-option imageUrl), test_attempts (resume by finding `in_progress`), announcements (NEW), notifications, raised_hands, page_analytics, bookmarks, student_suggestions, contacts.
  - Seed batches: `JEEM2027`, `NEX2027`, `NEX2028`.
  - Seed users idempotent via `services/seed_service.py`.
  - Auth middleware: verifies Supabase JWT via `supabase.auth.get_user(token)`.

## What's implemented in Phase 12
- ✅ **Auth**: `/api/auth/login`, `/signup`, `/me`, `/logout`, `/google/url` — 100% tests pass
- ✅ **Batches**: `/api/batches/{,by-code/:code,POST,DELETE}` — 100% tests pass
- ✅ **Admissions**: `/api/admissions/submit` (with batch verify + roll_number), `/me` — 100%
- ✅ **Classes**: teacher create/list/delete + student list (batch-filtered) — 100%
- ✅ **Live Classes (Zoom)**: create + start (host signature + zak) + student join (attendee signature) + raise-hand/lower-hand — 100% API contract passing (browser embed component in `frontend/src/components/live/ZoomMeetingEmbed.js`)
- ✅ **Tests + Attempts**: teacher create + student assigned/start (resume-on-existing) + submit
- ✅ **Questions with option images (Part 6)**: `/api/questions/single` accepts options jsonb `{A:{text,imageUrl}, B:{...}}`
- ✅ **Announcements (NEW Part 5)**: `/api/announcements/{,POST,DELETE}` — batch-targeted, notifies every student in batch
- ✅ **Notifications**: `/api/notifications/`, mark-read, mark-all-read
- ✅ **Uploads**: `/api/upload/image` → Supabase Storage `question-images` public URL
- ✅ **Contacts**: `/api/contacts/submit` (landing page form)
- ✅ **Zoom Live Class Embed**: `@zoom/meetingsdk@6.2.0` client view, launched from teacher/student LiveClasses pages
- ✅ **Batch isolation**: JEEM2027 content invisible to NEX2028 (verified via testing agent)
- ✅ **Profile page** (`/profile`): full personal details + copyable roll number + batch code

## Deferred (to be re-ported)
These modules were removed in Phase 12 because their MongoDB rewrite is heavy.
Bring them back once Zoom rollout is stable:
- Analytics dashboards (student + admin) — `analytics_routes`, `student_analytics_routes`, `admin_dashboard_routes`
- PYQ browser & bulk CSV seeder
- Custom Test builder (`custom_test_routes`)
- Bookmarks
- Suggestion moderation (`student_suggestion_routes`)
- Teacher admin CRUD (`admin_routes` — creating teacher accounts from admin)
- Page-view analytics middleware
- Reminder scheduler (test/class reminders via email)

## Test Credentials
See `/app/memory/test_credentials.md`.

## Landing Page Facts (in code)
- Hero: "8+ Years Experience"
- Founder Skills — all 100% (Organic, Physical, Inorganic, Thermodynamics, Reaction Mechanisms)
- Founder bio: 8+ years HOD Chemistry at Vidyamandir Classes

## Prioritized Backlog
### P0 (before Zoom rollout)
- None — Zoom flow tested at API level; browser embed component ready.

### P1
- Re-port Analytics dashboard on Supabase
- Re-port PYQ browser + CSV seeder
- Fix student_test_routes score-verification (client is trusted for is_correct)

### P2
- Custom Test builder re-port
- Bookmarks re-port
- Landing page contact-form → new `/api/contacts/submit` UI wiring
- Admin Teachers CRUD re-port (create teacher accounts from admin panel)

### Backlog / Ideas
- Shareable batch join links `/join/JEEM2027`
- AI Solution Explainer on Sample Questions (EMERGENT_LLM_KEY)

## Verified via Testing Agent
- Iteration 14: 32/37 (3 critical fixes required)
- Iteration 15: **37/37 (100%)** — all critical fixes verified.
