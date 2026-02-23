# JEE Master - Product Requirements Document

## Original Problem Statement
Build a full-stack JEE preparation web application with:
- Comprehensive PYQ section with Physics, Chemistry, and Mathematics
- Student dashboard with progress tracking
- Online admission form with user account creation and email confirmation
- Admin panel for managing admissions
- Live Classes section with scheduling and recordings

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Email:** Resend API

## Current Implementation Status

### Completed Features ✅

#### Authentication System
- JWT-based session authentication with httpOnly cookies
- Google OAuth via Emergent Auth
- Login with email/password
- Auto-login after admission form submission
- Test accounts: `student@test.com` / `teacher@test.com` (password123)

#### PYQ Section (Fully Implemented)
- **Total Questions: 13,415** across all subjects
  - Physics: 4,246 questions (41 chapters)
  - Mathematics: 5,071 questions (38 chapters)
  - Chemistry: 4,098 questions (25 chapters)
- Year categorization: 2010-2025 (strict extraction)
- Topic categorization within each chapter
- Question types: MCQ (10,730) and Numerical (2,685)
- Navigation: Exam Type → Subject → Chapter → Practice Mode → Questions
- Search with autocomplete
- Year filter pills
- Topic-wise and Year-wise practice modes
- Question tracking with progress analytics

#### Dashboard Analytics ✅
- Questions Solved (real-time)
- Tests Taken
- Average Accuracy
- Current Streak

#### Admission System ✅
**Multi-step admission form with:**
1. **Step 1 - Personal Details:**
   - Student Name, Father/Mother Name
   - Date of Birth, Gender
   - Contact Number, Email
   - **Create Password & Confirm Password**
   
2. **Step 2 - Address & Course:**
   - Full Address, City, State, Pincode
   - Course selection (6 JEE courses)
   
3. **Step 3 - Document Upload:**
   - Camera selfie capture
   - Gallery photo upload
   - ID Proof upload (optional)
   
4. **Step 4 - Digital Signature:**
   - Touch/mouse canvas signature
   - Clear and redraw support

**On Submission:**
- Creates user account with password
- Sends confirmation email (Resend)
- Auto-logs in the student
- Redirects to dashboard

**Admin Panel:**
- View all applications with stats
- Filter by status (Pending/Approved/Rejected)
- Search by name, email, or ID
- View full details with photo and signature
- Approve/Reject applications
- Export to CSV/Excel

#### My Live Classes ✅ (NEW - Feb 2026)
**Features:**
- **NextClassCard:** Featured card with live countdown timer
- **UpcomingClassCard:** Cards for other upcoming classes
- **PastClassCard:** Cards with Watch Recording, Download Notes, Download Slides links
- Subject-based color coding (Physics=blue, Chemistry=green, Math=red)
- Join button activates 10 mins before class
- Teacher photos and meeting platform info
- Timeline and Calendar view toggle

**API Endpoints:**
- `GET /api/classes` - Get all classes with filters
- `GET /api/classes/upcoming` - Get upcoming classes with can_join flag
- `GET /api/classes/past` - Get past classes with recordings
- `GET /api/classes/schedule?days=7` - Get schedule grouped by date
- `POST /api/classes` - Create new class
- `PUT /api/classes/{id}` - Update class
- `POST /api/classes/{id}/attendance` - Mark attendance
- `POST /api/classes/seed-sample` - Seed sample data

**Email Reminders:**
- 24 hours before class
- 1 hour before class
- 15 minutes before class

### Question Database Summary

| Subject | Questions | MCQ | Numerical |
|---------|-----------|-----|-----------|
| Mathematics | 5,071 | 4,200+ | 800+ |
| Physics | 4,246 | 3,500+ | 700+ |
| Chemistry | 4,098 | 3,000+ | 1,000+ |

### Year Distribution
| Year | Questions |
|------|-----------|
| 2025 | 1,247 |
| 2024 | 2,033 |
| 2023 | 1,906 |
| 2022 | 1,739 |
| 2021 | 1,857 |
| 2020 | 1,038 |
| 2019 | 1,242 |
| Older | 2,353 |

### API Endpoints Summary

#### Admissions
- `POST /api/admissions/submit` - Submit admission (creates user, sends email, returns session)
- `GET /api/admissions/list` - List all admissions (admin)
- `GET /api/admissions/detail/{id}` - Get full details
- `PUT /api/admissions/update-status/{id}` - Approve/Reject
- `GET /api/admissions/export/excel` - Export CSV

#### Authentication
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/register` - Register new user
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

#### Questions
- `GET /api/questions` - Get questions with filters
- `GET /api/questions/syllabus` - Get syllabus structure

#### Analytics
- `POST /api/analytics/attempt` - Record question attempt
- `GET /api/analytics/stats` - Get user statistics

#### Classes
- `GET /api/classes` - Get all classes
- `GET /api/classes/upcoming` - Get upcoming classes
- `GET /api/classes/past` - Get past classes
- `POST /api/classes` - Create class
- `PUT /api/classes/{id}` - Update class
- `DELETE /api/classes/{id}` - Delete class
- `POST /api/classes/{id}/attendance` - Mark attendance

### Key Routes
- `/login` - Login page with admission link
- `/admission` - Multi-step admission form
- `/admin` - Admin panel for managing admissions
- `/pyq` - PYQ practice section
- `/dashboard` - Student dashboard
- `/classes` - My Live Classes section

### Integrations
- **Resend:** Email confirmation for admissions and class reminders
- **PyMuPDF:** PDF parsing for question extraction
- **React Signature Canvas:** Digital signatures

---

## Pending Features 🔄
1. Custom Test Builder
2. Teacher dashboards
3. Google Sheets sync for live classes
4. Question bookmarking
5. Email notifications for admission status changes

---
Last Updated: February 23, 2026
