# NexUacademy - Product Requirements Document

## Original Problem Statement
Build a full-stack JEE preparation web application with:
- Comprehensive PYQ section with Physics, Chemistry, and Mathematics
- Student dashboard with progress tracking
- Online admission form with user account creation and email confirmation
- Admin panel for managing admissions
- Live Classes section with scheduling and recordings
- Custom Test Builder for personalized practice tests

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

#### My Live Classes ✅
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

#### Custom Test Builder ✅ (NEW - Feb 23, 2026)
**4-Step Test Creation Wizard:**
1. **Step 1 - Exam Type:** Select JEE Main, JEE Advanced, or Mixed Practice
2. **Step 2 - Topic Selection:**
   - Physics/Chemistry/Mathematics tabs
   - Expandable chapters with topic counts
   - Select topics with available question counts
   - Search chapters and topics
3. **Step 3 - Configure:**
   - Set question count per topic
   - Year range selector (2010-2025)
   - Duration setting with recommended time
   - Subject-wise marks breakdown
4. **Step 4 - Preview:**
   - Summary cards (Total Questions, Marks, Duration, Year Range)
   - Subject-wise distribution chart
   - Save as Template option
   - Generate & Start Test button

**Test Taking Interface:**
- Real-time countdown timer (turns red when < 5 mins)
- Question display with subject badges and marks
- MCQ options with selection highlighting
- Numerical input for numerical questions
- Question Palette showing answered/flagged/remaining
- Flag questions for review
- Clear answer button
- Previous/Next navigation
- Direct question navigation via palette
- Auto-submit on timer expiry
- Confirmation dialog for early submission

**Test Results Display:**
- Score summary card with gradient background
- Correct/Incorrect/Skipped counts
- Time taken
- Percentage and Accuracy metrics
- Question-wise analysis with:
  - User answer vs correct answer
  - Marks per question (+4/-1/0)
  - Status indicator (green/red/gray)
- Back to My Tests button
- Retake Test option

**API Endpoints:**
- `GET /api/custom-tests/syllabus` - Get chapters/topics by subject
- `GET /api/custom-tests/question-counts` - Get topic-wise question counts
- `POST /api/custom-tests/generate` - Generate test from selected topics
- `GET /api/custom-tests/{test_id}` - Get test details
- `GET /api/custom-tests/{test_id}/questions` - Get questions (no answers)
- `POST /api/custom-tests/{test_id}/submit` - Submit and get results
- `GET /api/custom-tests/history/mine` - Get user's test history
- `GET /api/test-templates` - Get saved templates
- `POST /api/test-templates` - Create template
- `PUT /api/test-templates/{id}` - Update template
- `DELETE /api/test-templates/{id}` - Delete template

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

### Key Routes
- `/login` - Login page with NexUacademy branding
- `/signup` - Sign up page
- `/admission` - Multi-step admission form
- `/admin` - Admin panel for managing admissions
- `/pyq` - PYQ practice section
- `/dashboard` - Student dashboard
- `/classes` - My Live Classes section
- `/my-tests` - Custom Test Builder
- `/test/:testId/take` - Test taking interface
- `/assigned-tests` - Tests assigned by teacher (placeholder)
- `/analytics` - Performance analytics (placeholder)
- `/bookmarks` - Saved questions (placeholder)

### Integrations
- **Resend:** Email confirmation for admissions and class reminders
- **PyMuPDF:** PDF parsing for question extraction
- **React Signature Canvas:** Digital signatures

---

## Pending Features 🔄
1. ~~Custom Test Builder~~ ✅ COMPLETED
2. Teacher dashboards
3. Google Sheets sync for live classes
4. Question bookmarking
5. Email notifications for admission status changes
6. Assigned tests from teachers

---
Last Updated: February 23, 2026
