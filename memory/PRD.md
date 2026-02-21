# JEE Master - Product Requirements Document

## Original Problem Statement
Build a full-stack JEE preparation web application called "JEE Master" with:
- Previous Year Questions (PYQ) section with filtering capabilities
- PDF question extraction
- Google Sheets integration for YouTube solution links
- Custom Test Builder
- Analytics Dashboard
- Teacher features

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python) - *Note: Originally requested Node.js but implemented in Python*
- **Database:** MongoDB

## Current Implementation Status

### Completed Features ✅

#### Authentication
- JWT-based authentication with session cookies
- Login/Signup pages
- Google OAuth support (via Emergent Auth)
- Test accounts: `student@test.com` / `teacher@test.com` (password: `password123`)

#### PYQ Section (Fully Implemented)
- **Navigation Flow:** Exam Type → Subject → Chapter → Practice Mode → Questions
- **Practice Modes:**
  - PYQs (Year-wise): Scrollable question grid sorted by year
  - Topic-wise: Questions grouped by topic
- **Search Functionality:**
  - Search bar with autocomplete dropdown
  - Search by question text, year, or topic
- **Year Filter Pills:** Filter questions by year (All, 2025, 2024, etc.)
- **Question View:**
  - MCQ questions with A/B/C/D options
  - Numerical questions with text input
  - Answer submission with correct/incorrect feedback
  - Solution display
  - Quick Navigation (numbered buttons)
  - "All Questions" sidebar with search and filter
- **Question Count:** 881 total questions
  - Chemical Bonding: 212 questions
  - Amines: 195 questions
  - Biomolecules: 171 questions
  - Alcohols, Phenols, Ethers: 156 questions
  - Analytical Chemistry: 122 questions
  - Equilibrium: 25 questions

#### PDF Question Extraction ✅
- Successfully extracted 856 questions from 5 chemistry PDFs:
  - Alcohols-Phenols-and-Ethers.pdf
  - Amines.pdf
  - Analytical-Chemistry.pdf
  - Biomolecules.pdf
  - Chemical-Bonding.pdf
- Extraction script: `/app/backend/scripts/extract_questions.py`

#### Database
- MongoDB with collections: users, questions, user_sessions
- Question schema includes: subject, chapter, topic, year, questionText, options, correctAnswer, difficulty, solution

### Pending Features 🔄

#### P1 - High Priority
1. **Google Sheets Integration**
   - Sync YouTube solution links from Google Sheet
   - Setup guide created at `/app/google_sheets_setup_guide.md`
   - Requires user to provide API credentials

2. **Chapter Name Alignment**
   - Some chapter names need to match NCERT/JEE official naming
   - Syllabus file: `/app/backend/config/syllabus.py`

#### P2 - Medium Priority
1. Custom Test Builder
2. Test Taking Interface
3. Student Analytics Dashboard
4. Question Bookmarking

#### P3 - Future Features
1. Teacher Dashboard
2. Test/Student/Class Management
3. Live Classes section
4. Notifications (Email/WhatsApp/Telegram)

## Key Files

### Backend
- `/app/backend/server.py` - Main FastAPI application
- `/app/backend/routes/question_routes.py` - Question API endpoints
- `/app/backend/routes/auth_routes.py` - Authentication endpoints
- `/app/backend/config/syllabus.py` - JEE syllabus data
- `/app/backend/scripts/extract_questions.py` - PDF extraction script

### Frontend
- `/app/frontend/src/App.js` - Main routing
- `/app/frontend/src/pages/PYQSection.js` - PYQ component (fully implemented)
- `/app/frontend/src/context/AuthContext.js` - Auth state management
- `/app/frontend/src/utils/api.js` - API client

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout
- `POST /api/auth/google/session` - Google OAuth

### Questions
- `GET /api/questions/` - Get questions with filters (subject, chapter, topic, year, limit)
- `GET /api/questions/syllabus` - Get complete syllabus
- `GET /api/questions/syllabus/{subject}` - Get subject syllabus
- `GET /api/questions/chapters/{subject}` - Get chapters
- `GET /api/questions/{question_id}` - Get single question

## Testing
- Test credentials: `student@test.com` / `password123`
- Test report: `/app/test_reports/iteration_1.json`
- All major features tested and working (95% success rate)

## Known Issues (Low Priority)
1. Some MCQ questions have corrupted options from PDF extraction
2. Question text formatting could be improved for complex formulas

---
Last Updated: February 2026
