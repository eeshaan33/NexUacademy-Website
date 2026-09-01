# Test Credentials — NexUacademy (Supabase Postgres)

All seed users are created idempotently by `backend/services/seed_service.py` at
every backend startup. Passwords below are the canonical dev passwords used by
every automated test.

| Role     | Email                                | Password           | Batch    |
|----------|--------------------------------------|--------------------|----------|
| Admin    | admin@nexuacademy.com                | nexuacademy123     | —        |
| Teacher  | teacher@test.com                     | password123        | —        |
| Teacher2 | teacher2_iter17@nexuacademy.com      | password123        | —        |
| Student  | student@test.com                     | password123        | JEEM2027 |

## Predefined batches (in DB, ready to use as batch codes)
- `JEEM2027` — JEE Mains 2027
- `NEX2027`  — NexUacademy 2027
- `NEX2028`  — NexUacademy 2028

Admin can create more batches with any alphanumeric code from `/admin` → Batches tab.

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
