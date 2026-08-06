-- =========================================================================
-- NexUacademy Supabase schema (Phase 12: MongoDB → PostgreSQL)
-- Run inside Supabase Dashboard → SQL Editor
-- =========================================================================

-- Enable UUID gen
create extension if not exists "pgcrypto";

-- =========================================================================
-- BATCHES (reference table)
-- =========================================================================
create table if not exists public.batches (
    id text primary key,                       -- alphanumeric code, e.g. JEEM2027
    code text not null unique,                 -- same as id, kept for API compat
    name text not null,
    year integer,
    is_predefined boolean default false,
    is_custom boolean default false,
    created_by text,
    created_by_id uuid,
    created_at timestamptz default now()
);

-- Force UPPER(TRIM()) on batch codes
create or replace function public.normalize_batch_code() returns trigger as $$
begin
    new.id := upper(trim(new.id));
    new.code := upper(trim(new.code));
    return new;
end;
$$ language plpgsql;

drop trigger if exists batches_normalize on public.batches;
create trigger batches_normalize before insert or update on public.batches
    for each row execute function public.normalize_batch_code();

-- Seed initial batches (JEEM2027, NEX2027, NEX2028 per user)
insert into public.batches (id, code, name, year, is_predefined)
values
    ('JEEM2027', 'JEEM2027', 'JEE Mains 2027', 2027, true),
    ('NEX2027',  'NEX2027',  'NexUacademy 2027', 2027, true),
    ('NEX2028',  'NEX2028',  'NexUacademy 2028', 2028, true)
on conflict (id) do nothing;

-- =========================================================================
-- PROFILES (1:1 with auth.users)
-- =========================================================================
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text unique not null,
    name text,
    role text not null default 'student' check (role in ('student','teacher','admin')),
    phone_number text,
    batch_id text references public.batches(id) on update cascade on delete set null,
    course text,
    roll_number text unique,
    admission_id text,
    father_name text, mother_name text,
    date_of_birth text, gender text,
    address text, city text, state text, pincode text,
    profile_pic text,
    push_subscription jsonb,
    notifications_enabled boolean default true,
    google_id text,
    is_active boolean default true,
    profile_complete boolean default false,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    last_active timestamptz
);

-- Normalize batch_id on profile writes so a misspelt batch is rejected by FK
create or replace function public.normalize_profile_batch() returns trigger as $$
begin
    if new.batch_id is not null then
        new.batch_id := upper(trim(new.batch_id));
    end if;
    new.updated_at := now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists profiles_normalize on public.profiles;
create trigger profiles_normalize before insert or update on public.profiles
    for each row execute function public.normalize_profile_batch();

-- Auto-create profile when a new auth.users row appears (Supabase Auth signup)
create or replace function public.handle_new_user() returns trigger as $$
declare
    v_name text;
    v_role text := 'student';
begin
    v_name := coalesce(new.raw_user_meta_data->>'name', split_part(new.email,'@',1));
    if (new.raw_user_meta_data->>'role') in ('student','teacher','admin') then
        v_role := new.raw_user_meta_data->>'role';
    end if;
    insert into public.profiles (id, email, name, role, batch_id, google_id)
    values (new.id, new.email, v_name, v_role,
            upper(trim(coalesce(new.raw_user_meta_data->>'batch_id', ''))),
            new.raw_user_meta_data->>'sub')
    on conflict (id) do nothing;
    return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
    for each row execute function public.handle_new_user();

-- =========================================================================
-- ADMISSIONS
-- =========================================================================
create table if not exists public.admissions (
    admission_id text primary key,
    user_id uuid references public.profiles(id) on delete cascade,
    roll_number text unique,
    student_name text, father_name text, mother_name text,
    date_of_birth text, gender text,
    contact_number text, email text,
    address text, city text, state text, pincode text,
    course_applying text, batch_code text, batch_id text references public.batches(id),
    photo text, id_proof text, signature text,
    status text default 'pending',
    submitted_at timestamptz default now(),
    reviewed_at timestamptz, reviewed_by text, remarks text
);

-- =========================================================================
-- CLASSES + LIVE CLASSES
-- =========================================================================
create table if not exists public.classes (
    class_id text primary key,
    title text not null,
    subject text, chapter text, topic text,
    teacher_id uuid references public.profiles(id) on delete set null,
    teacher_name text, teacher_photo text,
    meeting_link text, meeting_platform text default 'Zoom',
    scheduled_date_time timestamptz,
    duration integer default 60,
    description text, prerequisites text,
    assigned_batches text[] default '{}',
    recording_url text, notes_url text, slides_url text,
    -- Zoom fields
    zoom_meeting_id text, zoom_meeting_password text,
    zoom_start_url text, zoom_join_url text,
    is_live boolean default false,
    live_started_at timestamptz, live_ended_at timestamptz,
    status text default 'upcoming',
    attendance jsonb default '[]'::jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists classes_batches_idx on public.classes using gin (assigned_batches);
create index if not exists classes_teacher_idx on public.classes(teacher_id);
create index if not exists classes_live_idx on public.classes(is_live) where is_live = true;

-- Normalize assigned_batches to UPPER(TRIM(...))
create or replace function public.normalize_classes_batches() returns trigger as $$
begin
    if new.assigned_batches is not null then
        new.assigned_batches := array(select upper(trim(b)) from unnest(new.assigned_batches) b where b is not null and length(trim(b)) > 0);
    end if;
    new.updated_at := now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists classes_normalize on public.classes;
create trigger classes_normalize before insert or update on public.classes
    for each row execute function public.normalize_classes_batches();

-- Raised hands
create table if not exists public.raised_hands (
    id uuid primary key default gen_random_uuid(),
    class_id text references public.classes(class_id) on delete cascade,
    student_id uuid references public.profiles(id) on delete cascade,
    student_name text,
    raised_at timestamptz default now(),
    unique (class_id, student_id)
);

-- =========================================================================
-- TESTS + QUESTIONS + ATTEMPTS
-- =========================================================================
create table if not exists public.tests (
    test_id text primary key,
    test_name text not null,
    exam_type text, test_pattern text,
    subject text, test_type text,
    chapters text[] default '{}', topics text[] default '{}',
    scheduled_date_time timestamptz,
    duration integer default 60,
    total_questions integer default 0, total_marks integer default 0,
    instructions text,
    allow_reattempts boolean default false, max_attempts integer default 1,
    show_solutions_after_submit boolean default true,
    show_results_immediately boolean default true,
    randomize_questions boolean default false,
    assigned_batches text[] default '{}',
    created_by_id uuid references public.profiles(id) on delete set null,
    created_by text,
    questions jsonb default '[]'::jsonb,  -- inline questions per test
    status text default 'draft',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists tests_batches_idx on public.tests using gin (assigned_batches);
create index if not exists tests_creator_idx on public.tests(created_by_id);

create or replace function public.normalize_tests_batches() returns trigger as $$
begin
    if new.assigned_batches is not null then
        new.assigned_batches := array(select upper(trim(b)) from unnest(new.assigned_batches) b where b is not null and length(trim(b)) > 0);
    end if;
    new.updated_at := now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists tests_normalize on public.tests;
create trigger tests_normalize before insert or update on public.tests
    for each row execute function public.normalize_tests_batches();

-- Standalone question bank (PYQ + samples + admin single-question creator)
create table if not exists public.questions (
    question_id text primary key,
    exam_type text, subject text, chapter text, topic text,
    year integer, difficulty text,
    question_text text, question_image_url text,
    question_type text default 'MCQ_Single',
    options jsonb default '{}'::jsonb,       -- {A:{text,imageUrl}, B:{...}, ...}
    correct_answers text[] default '{}',
    numerical_answer numeric, answer_range jsonb,
    marks integer default 4, negative_marks integer default -1,
    explanation text, teacher_note text,
    is_sample boolean default false,
    created_by text,
    created_at timestamptz default now()
);
create index if not exists questions_subject_idx on public.questions(subject);
create index if not exists questions_sample_idx on public.questions(is_sample) where is_sample = true;

-- Test attempts
create table if not exists public.test_attempts (
    attempt_id text primary key,
    test_id text references public.tests(test_id) on delete cascade,
    student_id uuid references public.profiles(id) on delete cascade,
    student_name text,
    answers jsonb default '[]'::jsonb,
    saved_answers jsonb default '[]'::jsonb,
    total_score integer default 0, max_score integer default 0,
    correct_answers integer default 0, incorrect_answers integer default 0,
    unattempted integer default 0,
    accuracy numeric default 0,
    started_at timestamptz default now(),
    submitted_at timestamptz,
    time_spent integer default 0,
    status text default 'in_progress',
    created_at timestamptz default now()
);
create index if not exists attempts_student_idx on public.test_attempts(student_id);
create index if not exists attempts_test_idx on public.test_attempts(test_id);

-- =========================================================================
-- NOTIFICATIONS + ANNOUNCEMENTS (Part 5)
-- =========================================================================
create table if not exists public.notifications (
    notification_id text primary key,
    user_id uuid references public.profiles(id) on delete cascade,
    type text,
    title text, message text,
    data jsonb default '{}'::jsonb,
    is_read boolean default false,
    created_at timestamptz default now()
);
create index if not exists notif_user_idx on public.notifications(user_id, is_read);

create table if not exists public.announcements (
    announcement_id text primary key default gen_random_uuid()::text,
    title text not null,
    message text not null,
    assigned_batches text[] default '{}',
    created_by uuid references public.profiles(id) on delete set null,
    created_by_name text,
    is_pinned boolean default false,
    created_at timestamptz default now()
);
create index if not exists announcements_batches_idx on public.announcements using gin (assigned_batches);
create index if not exists announcements_pinned_idx on public.announcements(is_pinned desc, created_at desc);

create or replace function public.normalize_announcement_batches() returns trigger as $$
begin
    if new.assigned_batches is not null then
        new.assigned_batches := array(select upper(trim(b)) from unnest(new.assigned_batches) b where b is not null and length(trim(b)) > 0);
    end if;
    return new;
end;
$$ language plpgsql;

drop trigger if exists announcements_normalize on public.announcements;
create trigger announcements_normalize before insert or update on public.announcements
    for each row execute function public.normalize_announcement_batches();

-- =========================================================================
-- MISC (page analytics, suggestions, demo bookings, bookmarks)
-- =========================================================================
create table if not exists public.page_analytics (
    id uuid primary key default gen_random_uuid(),
    page text, path text,
    visits integer default 0,
    unique_visitors jsonb default '[]'::jsonb,
    total_time_spent integer default 0,
    date date default current_date
);

create table if not exists public.student_suggestions (
    suggestion_id text primary key default gen_random_uuid()::text,
    student_id uuid references public.profiles(id) on delete cascade,
    student_name text, student_email text,
    suggestion_type text, subject text,
    message text,
    priority text default 'normal',
    status text default 'new',
    admin_notes text, is_read boolean default false,
    upvotes integer default 0,
    created_at timestamptz default now()
);

create table if not exists public.bookmarks (
    bookmark_id text primary key default gen_random_uuid()::text,
    user_id uuid references public.profiles(id) on delete cascade,
    source text,
    question_id text,
    test_id text, question_number integer,
    snapshot jsonb,
    created_at timestamptz default now()
);
create index if not exists bookmarks_user_idx on public.bookmarks(user_id);

create table if not exists public.contacts (
    contact_id text primary key default gen_random_uuid()::text,
    name text, email text, phone text, course text,
    message text,
    status text default 'new',
    created_at timestamptz default now()
);

-- =========================================================================
-- STORAGE BUCKETS (create via Dashboard OR run:)
-- =========================================================================
-- insert into storage.buckets (id, name, public) values ('question-images','question-images', true) on conflict do nothing;
-- insert into storage.buckets (id, name, public) values ('class-materials','class-materials', true) on conflict do nothing;

-- =========================================================================
-- ROW LEVEL SECURITY (permissive for now — API layer enforces role checks)
-- Enable RLS but grant open policies since we authenticate via service role
-- =========================================================================
alter table public.profiles enable row level security;
alter table public.batches enable row level security;
alter table public.classes enable row level security;
alter table public.tests enable row level security;
alter table public.questions enable row level security;
alter table public.test_attempts enable row level security;
alter table public.notifications enable row level security;
alter table public.announcements enable row level security;
alter table public.raised_hands enable row level security;
alter table public.admissions enable row level security;
alter table public.bookmarks enable row level security;
alter table public.student_suggestions enable row level security;

-- Allow authenticated users to read their own profile and batches (public read)
drop policy if exists "batches_public_read" on public.batches;
create policy "batches_public_read" on public.batches for select using (true);
drop policy if exists "profiles_self_read" on public.profiles;
create policy "profiles_self_read" on public.profiles for select using (auth.uid() = id);
drop policy if exists "profiles_self_update" on public.profiles;
create policy "profiles_self_update" on public.profiles for update using (auth.uid() = id);
-- Service role bypasses RLS automatically, so backend has full access.
