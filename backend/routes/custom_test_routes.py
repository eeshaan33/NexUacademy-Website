"""
Custom Test Routes - For generating and managing custom tests
"""
from fastapi import APIRouter, HTTPException, Request, Query
from config.database import get_database
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import random
from middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/custom-tests", tags=["custom-tests"])

class TopicConfig(BaseModel):
    subject: str
    chapter: str
    topic: str
    questionCount: int
    difficulty: str = "Mixed"

class YearRange(BaseModel):
    start: int
    end: int

class CustomTestCreate(BaseModel):
    examType: str
    selectedTopics: List[TopicConfig]
    yearRange: YearRange
    duration: int
    totalQuestions: int
    totalMarks: int

@router.get("/question-counts")
async def get_question_counts(
    request: Request,
    examType: Optional[str] = None
):
    """Get question counts by subject/chapter/topic"""
    db = get_database()
    
    # Build match query
    match_query = {}
    if examType and examType != "Mixed":
        match_query["examType"] = examType
    
    # Aggregate to get counts
    pipeline = [
        {"$match": match_query} if match_query else {"$match": {}},
        {
            "$group": {
                "_id": {
                    "subject": "$subject",
                    "chapter": "$chapter",
                    "topic": "$topic"
                },
                "count": {"$sum": 1}
            }
        }
    ]
    
    results = await db.questions.aggregate(pipeline).to_list(length=1000)
    
    # Convert to key-value format
    counts = {}
    for r in results:
        key = f"{r['_id']['subject']}-{r['_id']['chapter']}-{r['_id']['topic']}"
        counts[key] = r["count"]
    
    return counts

@router.get("/syllabus")
async def get_syllabus(request: Request):
    """Get syllabus structure with chapters and topics"""
    db = get_database()
    
    # Get unique chapters and topics for each subject
    pipeline = [
        {
            "$group": {
                "_id": {
                    "subject": "$subject",
                    "chapter": "$chapter"
                },
                "topics": {"$addToSet": "$topic"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    results = await db.questions.aggregate(pipeline).to_list(length=500)
    
    # Organize by subject
    syllabus = {
        "Physics": {"Class11": [], "Class12": []},
        "Chemistry": {"Class11": [], "Class12": []},
        "Mathematics": {"Class11": [], "Class12": []}
    }
    
    # Class 11 chapters (approximate mapping)
    class11_chapters = {
        "Physics": ["Units and Measurements", "Motion in a Straight Line", "Motion in a Plane", 
                   "Laws of Motion", "Work, Energy and Power", "System of Particles", 
                   "Gravitation", "Mechanical Properties", "Thermal Properties", 
                   "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
        "Chemistry": ["Some Basic Concepts", "Structure of Atom", "Classification of Elements",
                     "Chemical Bonding", "States of Matter", "Thermodynamics", "Equilibrium",
                     "Redox Reactions", "Hydrogen", "s-Block Elements", "Organic Chemistry",
                     "Hydrocarbons", "Environmental Chemistry"],
        "Mathematics": ["Sets", "Relations and Functions", "Trigonometric Functions",
                       "Complex Numbers", "Linear Inequalities", "Permutation and Combination",
                       "Binomial Theorem", "Sequence and Series", "Straight Lines", "Conic Sections",
                       "Introduction to 3D", "Limits and Derivatives", "Statistics", "Probability"]
    }
    
    for r in results:
        subject = r["_id"]["subject"]
        chapter = r["_id"]["chapter"]
        topics = [t for t in r["topics"] if t]  # Filter out None/empty topics
        
        if subject not in syllabus:
            continue
        
        chapter_data = {
            "chapter": chapter,
            "topics": topics,
            "questionCount": r["count"]
        }
        
        # Determine if class 11 or 12 based on chapter name
        is_class11 = any(c11 in chapter for c11 in class11_chapters.get(subject, []))
        
        if is_class11:
            syllabus[subject]["Class11"].append(chapter_data)
        else:
            syllabus[subject]["Class12"].append(chapter_data)
    
    return syllabus

@router.post("/generate")
async def generate_custom_test(test_config: CustomTestCreate, request: Request):
    """Generate a custom test from the question bank"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
        user_name = user.get("name", "Student")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    all_selected_questions = []
    insufficient_topics = []
    
    for topic_config in test_config.selectedTopics:
        # Build query
        query = {
            "subject": topic_config.subject,
            "chapter": topic_config.chapter,
            "year": {"$gte": test_config.yearRange.start, "$lte": test_config.yearRange.end}
        }
        
        # Only add topic filter if it's not the same as chapter
        if topic_config.topic and topic_config.topic != topic_config.chapter:
            query["topic"] = topic_config.topic
        
        if test_config.examType != "Mixed":
            query["examType"] = test_config.examType
        
        if topic_config.difficulty != "Mixed":
            query["difficulty"] = topic_config.difficulty
        
        # Fetch questions
        questions = await db.questions.find(
            query,
            {"_id": 0}
        ).to_list(length=topic_config.questionCount * 3)  # Fetch more for randomization
        
        if len(questions) < topic_config.questionCount:
            insufficient_topics.append({
                "topic": topic_config.topic or topic_config.chapter,
                "subject": topic_config.subject,
                "available": len(questions),
                "requested": topic_config.questionCount
            })
            # Use all available questions
            selected = questions
        else:
            # Randomly select required number
            random.shuffle(questions)
            selected = questions[:topic_config.questionCount]
        
        all_selected_questions.extend(selected)
    
    if not all_selected_questions:
        raise HTTPException(
            status_code=400,
            detail="No questions found matching your criteria. Please adjust your filters."
        )
    
    # Shuffle all questions
    random.shuffle(all_selected_questions)
    
    # Create test document
    test_id = f"test_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Prepare questions with numbers
    test_questions = []
    for i, q in enumerate(all_selected_questions, 1):
        test_questions.append({
            "questionNumber": i,
            "question_id": q.get("question_id"),
            "questionText": q.get("questionText"),
            "options": q.get("options"),
            "correctAnswer": q.get("correctAnswer"),
            "questionType": q.get("questionType", "MCQ"),
            "subject": q.get("subject"),
            "chapter": q.get("chapter"),
            "topic": q.get("topic"),
            "marks": 4,
            "negativeMarks": -1,
            "year": q.get("year"),
            "difficulty": q.get("difficulty")
        })
    
    # Calculate subject breakdown
    subject_breakdown = {"Physics": 0, "Chemistry": 0, "Mathematics": 0}
    for q in test_questions:
        subject_breakdown[q["subject"]] = subject_breakdown.get(q["subject"], 0) + 1
    
    test_doc = {
        "test_id": test_id,
        "test_name": f"Custom Test - {now.strftime('%d %b %Y %I:%M %p')}",
        "test_type": "custom",
        "exam_type": test_config.examType,
        "created_by": user_id,
        "created_by_name": user_name,
        "duration": test_config.duration,
        "total_questions": len(test_questions),
        "total_marks": len(test_questions) * 4,
        "questions": test_questions,
        "subject_breakdown": subject_breakdown,
        "year_range": test_config.yearRange.dict(),
        "status": "ready",
        "created_at": now,
        "starts_at": now,
        "ends_at": now + timedelta(minutes=test_config.duration + 30)
    }
    
    await db.tests.insert_one(test_doc)
    
    response = {
        "success": True,
        "test_id": test_id,
        "test_name": test_doc["test_name"],
        "total_questions": len(test_questions),
        "total_marks": test_doc["total_marks"],
        "duration": test_config.duration,
        "subject_breakdown": subject_breakdown
    }
    
    if insufficient_topics:
        response["warnings"] = insufficient_topics
        response["message"] = f"Test created with {len(test_questions)} questions. Some topics had fewer questions than requested."
    else:
        response["message"] = "Test generated successfully"
    
    return response

@router.get("/{test_id}")
async def get_test(test_id: str, request: Request):
    """Get test details for taking the test"""
    db = get_database()
    
    test = await db.tests.find_one(
        {"test_id": test_id},
        {"_id": 0}
    )
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Remove correct answers for test-taking (they'll be revealed after submission)
    for q in test.get("questions", []):
        if "correctAnswer" in q:
            del q["correctAnswer"]
    
    return test

@router.get("/{test_id}/questions")
async def get_test_questions(test_id: str, request: Request):
    """Get test questions without answers"""
    db = get_database()
    
    test = await db.tests.find_one(
        {"test_id": test_id},
        {"_id": 0, "questions": 1, "total_questions": 1, "duration": 1}
    )
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Remove correct answers
    questions = []
    for q in test.get("questions", []):
        q_clean = {k: v for k, v in q.items() if k != "correctAnswer"}
        questions.append(q_clean)
    
    return {
        "questions": questions,
        "total_questions": test.get("total_questions"),
        "duration": test.get("duration")
    }

class TestSubmission(BaseModel):
    answers: dict  # {questionNumber: selectedAnswer}
    timeSpent: int  # seconds

@router.post("/{test_id}/submit")
async def submit_test(test_id: str, submission: TestSubmission, request: Request):
    """Submit test answers and get results"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get test with correct answers
    test = await db.tests.find_one({"test_id": test_id})
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Calculate results
    correct = 0
    incorrect = 0
    unattempted = 0
    total_marks = 0
    
    question_results = []
    
    for q in test.get("questions", []):
        q_num = q["questionNumber"]
        correct_ans = q.get("correctAnswer", "")
        user_ans = submission.answers.get(str(q_num), "")
        
        result = {
            "questionNumber": q_num,
            "userAnswer": user_ans,
            "correctAnswer": correct_ans,
            "marks": 0,
            "status": "unattempted"
        }
        
        if not user_ans:
            unattempted += 1
            result["status"] = "unattempted"
        elif user_ans == correct_ans:
            correct += 1
            result["marks"] = q.get("marks", 4)
            result["status"] = "correct"
            total_marks += q.get("marks", 4)
        else:
            incorrect += 1
            result["marks"] = q.get("negativeMarks", -1)
            result["status"] = "incorrect"
            total_marks += q.get("negativeMarks", -1)
        
        question_results.append(result)
    
    # Calculate percentage
    max_marks = test.get("total_marks", len(test.get("questions", [])) * 4)
    percentage = round((total_marks / max_marks) * 100, 2) if max_marks > 0 else 0
    
    # Calculate accuracy
    attempted = correct + incorrect
    accuracy = round((correct / attempted) * 100, 2) if attempted > 0 else 0
    
    # Save attempt
    attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
    attempt_doc = {
        "attempt_id": attempt_id,
        "test_id": test_id,
        "user_id": user_id,
        "answers": submission.answers,
        "time_spent": submission.timeSpent,
        "correct": correct,
        "incorrect": incorrect,
        "unattempted": unattempted,
        "total_marks": total_marks,
        "max_marks": max_marks,
        "percentage": percentage,
        "accuracy": accuracy,
        "question_results": question_results,
        "submitted_at": datetime.now(timezone.utc)
    }
    
    await db.test_attempts.insert_one(attempt_doc)
    
    # Update user progress
    await db.user_progress.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "tests_taken": 1,
                "total_questions_attempted": attempted,
                "total_correct": correct
            },
            "$set": {"last_test_date": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    return {
        "success": True,
        "attempt_id": attempt_id,
        "results": {
            "correct": correct,
            "incorrect": incorrect,
            "unattempted": unattempted,
            "totalMarks": total_marks,
            "maxMarks": max_marks,
            "percentage": percentage,
            "accuracy": accuracy,
            "timeSpent": submission.timeSpent
        },
        "questionResults": question_results
    }

@router.get("/history/mine")
async def get_my_test_history(request: Request, limit: int = 20):
    """Get user's test history"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    attempts = await db.test_attempts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("submitted_at", -1).limit(limit).to_list(length=limit)
    
    # Get test names
    for attempt in attempts:
        test = await db.tests.find_one(
            {"test_id": attempt["test_id"]},
            {"test_name": 1, "exam_type": 1, "subject_breakdown": 1}
        )
        if test:
            attempt["test_name"] = test.get("test_name")
            attempt["exam_type"] = test.get("exam_type")
            attempt["subject_breakdown"] = test.get("subject_breakdown")
    
    return {"attempts": attempts}
