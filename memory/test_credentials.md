# Test Credentials — NexUacademy (Supabase Postgres)

All seed users are created idempotently by `backend/services/seed_service.py` at
every backend startup. Passwords below are the canonical dev passwords used by
every automated test.

| Role     | Email                                | Password           | Batch    |
|----------|--------------------------------------|--------------------|----------|
| Admin    | admin@nexuacademy.com                | nexuacademy123     | —        |
| Teacher  | teacher@test.com                     | password123        | —        |
| Teacher (Question Bank) | nitinsaini.iitkgp@gmail.com | nitin@123 | —        |
| Teacher2 | teacher2_iter17@nexuacademy.com      | password123        | —        |
| Student  | student@test.com                     | password123        | NEX2027  |
| OTP Test | otp.tester@example.com               | testpass123        | NEX2027  |

**OTP flow notes for testing:**
- Signup: `POST /api/auth/otp/start-signup` → OTP row saved in `auth_otps` table.
  In testing, recover the plaintext code by brute-forcing the 6-digit space
  against `code_hash` (sha256("email_lowercase::code")).
- Login: send `X-Device-Id: <uuid>` header. Unknown device → `requires_otp: true`.
  Legacy clients without the header still get tokens (backward compat).
- All contacts (name + email + phone + verified stamps) live in `profiles`.
  Admin export: `GET /api/admin/contacts` and `.csv`.

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

## Emergent-managed Google Auth (added Feb 2026)
- Coexists with Supabase Auth. New endpoints:
  - `POST /api/auth/emergent/session` (header `X-Session-ID`) → sets
    httpOnly `session_token` cookie (7-day, SameSite=None, Secure).
  - `POST /api/auth/emergent/logout` → clears cookie + deletes DB row.
- Backend middleware accepts EITHER Supabase Bearer JWT OR the Emergent
  cookie, so all existing routes work with either flow.
- Frontend button `[data-testid=emergent-google-button]` on `/login`
  triggers redirect to `https://auth.emergentagent.com/?redirect=<origin>/dashboard`.
- No app-managed password is stored for Emergent users — they must
  always come back via the Emergent auth portal.
- Full playbook + smoke test: `/app/auth_testing.md`.

