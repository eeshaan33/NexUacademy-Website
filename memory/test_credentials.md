# Test Credentials — NexUacademy (Supabase Postgres)

All seed users are created idempotently by `backend/services/seed_service.py` at
every backend startup. Passwords below are the canonical dev passwords used by
every automated test.

| Role     | Email                                | Password           | Batch    |
|----------|--------------------------------------|--------------------|----------|
| Admin    | admin@nexuacademy.com                | nexuacademy123     | —        |
| Teacher  | teacher@test.com                     | password123        | —        |
| Teacher2 | teacher2_iter17@nexuacademy.com      | password123        | —        |
| Student  | student@test.com                     | password123        | NEX2027  |

## Predefined batches (in DB, ready to use as batch codes)
- `JEEM2027` — JEE Mains 2027
- `NEX2027`  — NexUacademy 2027
- `NEX2028`  — NexUacademy 2028

## Preseed enrolled students (whitelist for /first-time-setup)
Populated by `backend/services/migration_service.py` on startup into
`public.preseed_students`. Default password format: `firstnamelowercase + batchYear`
(e.g., `arjun2027`, `shantanu2028`).

**NEX2027**: Arjun, Garvit, Khushi, Kartavya, Kovid, Krisha, Naavya, Pragya,
Abhinav, Vivaan, Urveesh, Yashasvi, Madhav, Aniket, Rittam, Eeshaan, Aaryan,
Ayush, Shefali

**NEX2028**: Shantanu, Pranit

Sample claim payload:
```json
POST /api/auth/claim-preseed
{ "first_name": "Arjun", "email": "arjun@example.com", "batch_id": "NEX2027" }
```
Response includes `default_password: "arjun2027"` — shown once to the student
on the First-Time Setup page.

## New Student Application (3-field public form)
`POST /api/admissions/simple-submit` → `{ full_name, email, whatsapp_number }`
Server generates a password = `firstnamelower + last4digits(whatsapp)` and
returns it once so the frontend can display it after payment. User is auto-
logged in and redirected to `/fee-structure` for the ₹30,000 Razorpay flow.
On paid → `profiles.access_tier` is set to `live_batch`.

## Supabase project
- URL: https://nygxykzxvuezeeutzmgh.supabase.co
- Region: ap-southeast-1
- Database password: NexUacademy2026

## Zoom Meeting SDK integration
- S2S OAuth (server) + Meeting SDK (browser) both configured in `backend/.env`.
- Note (external, not code): Add scopes `user:read:token`,
  `dashboard:read:list_meeting_participants:admin`,
  `meeting:delete:meeting:admin` in the Zoom App Marketplace to enable
  participants polling + delete-meeting.
