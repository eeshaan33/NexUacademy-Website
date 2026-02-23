"""
Combined PDF Question Extractor for Physics and Math
Extracts questions from large combined PDFs with chapter-wise organization
"""
import fitz
import re
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(Path(__file__).parent.parent / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Math chapters
MATH_CHAPTERS = [
    'Application of Derivatives',
    'Application of Integrals',
    'Arithmetic Progression',
    'Binomial Theorem',
    'Circle',
    'Complex Numbers',
    'Continuity and Differentiability',
    'Definite Integration',
    'Determinants',
    'Differential Equations',
    'Ellipse',
    'Functions',
    'Geometric Progression',
    'Height and Distance',
    'Hyperbola',
    'Indefinite Integration',
    'Inverse Trigonometric Functions',
    'Limits and Derivatives',
    'Linear Programming',
    'Logarithm',
    'Mathematical Induction',
    'Mathematical Reasoning',
    'Matrices',
    'Parabola',
    'Permutation and Combination',
    'Probability',
    'Quadratic Equations',
    'Relations and Functions',
    'Sequence and Series',
    'Sets',
    'Statistics',
    'Straight Lines',
    'Three Dimensional Geometry',
    'Trigonometric Equations',
    'Trigonometric Ratios and Identities',
    'Vector Algebra',
    'Conic Sections',
    'Integrals',
    'Derivatives',
]

# Physics chapters
PHYSICS_CHAPTERS = [
    'Alternating Currents',
    'Atoms',
    'Communication Systems',
    'Current Electricity',
    'Dual Nature of Radiation and Matter',
    'Electric Charges and Fields',
    'Electromagnetic Induction',
    'Electromagnetic Waves',
    'Electrostatic Potential and Capacitance',
    'Gravitation',
    'Kinetic Theory',
    'Laws of Motion',
    'Magnetic Effects of Current and Magnetism',
    'Magnetism and Matter',
    'Mechanical Properties of Fluids',
    'Mechanical Properties of Solids',
    'Motion in a Plane',
    'Motion in a Straight Line',
    'Moving Charges and Magnetism',
    'Nuclei',
    'Oscillations',
    'Physical World',
    'Ray Optics and Optical Instruments',
    'Semiconductor Electronics',
    'Systems of Particles and Rotational Motion',
    'Thermal Properties of Matter',
    'Thermodynamics',
    'Units and Measurements',
    'Wave Optics',
    'Waves',
    'Work, Energy and Power',
    'Center of Mass',
    'Rotational Motion',
    'Simple Harmonic Motion',
    'Fluids',
    'Capacitors',
    'Electrostatics',
    'Magnetism',
    'Modern Physics',
    'Optics',
    'Semiconductors',
]

def extract_year_from_text(text):
    """Extract year from JEE exam text - strict year extraction"""
    patterns = [
        r'JEE\s*Main\s*(\d{4})\s*\(Online\)',
        r'JEE\s*Advanced\s*(\d{4})',
        r'JEE\s*Main\s*(\d{4})',
        r'\[?\d{1,2}[-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-/](\d{4})',
        r'[\[\(](\d{4})[\]\)]',
        r'Online\s+\w+\s+\d{1,2},?\s+(\d{4})',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+\d{1,2},?\s+(\d{4})',
        r'(\d{4})\s*\([IVX]+\)',
        r'\b(20[12]\d)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 2010 <= year <= 2026:
                return year
    return None

def extract_exam_type(text):
    """Extract exam type"""
    if re.search(r'advanced', text, re.IGNORECASE):
        return 'JEE_Advanced'
    return 'JEE_Main'

def extract_shift(text):
    """Extract shift information"""
    text_lower = text.lower()
    if 'morning' in text_lower or 'shift 1' in text_lower or 'shift-1' in text_lower:
        return 'Morning'
    elif 'evening' in text_lower or 'shift 2' in text_lower or 'shift-2' in text_lower:
        return 'Evening'
    return None

def clean_text(text):
    """Clean up extracted text"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'-{5,}', '', text)
    text = re.sub(r'={3,}', '', text)
    return text.strip()

def extract_options(text):
    """Extract MCQ options"""
    options = {}
    patterns = [
        r'(?:^|\n)\s*([A-D])[.\)]\s*(.+?)(?=(?:\n\s*[A-D][.\)]|\nAnswer:|\nSolution:|$))',
        r'\(([A-D])\)\s*(.+?)(?=(?:\([A-D]\)|\nAnswer:|\nSolution:|$))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if matches and len(matches) >= 2:
            for letter, content in matches:
                letter = letter.upper()
                if letter in ['A', 'B', 'C', 'D']:
                    options[letter] = clean_text(content)[:500]
            if len(options) >= 2:
                break
    
    for letter in ['A', 'B', 'C', 'D']:
        if letter not in options:
            options[letter] = ''
    
    return options if any(options.values()) else None

def extract_answer(text):
    """Extract correct answer"""
    patterns = [
        r'Answer:\s*\(?([A-D])\)?',
        r'Ans[.:]?\s*\(?([A-D])\)?',
        r'Correct\s*Answer[.:]?\s*\(?([A-D])\)?',
        r'Answer:\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            ans = match.group(1)
            if ans.upper() in ['A', 'B', 'C', 'D']:
                return ans.upper()
            return ans
    return None

def extract_solution(text):
    """Extract solution text"""
    match = re.search(r'Solution:\s*(.+?)(?=Question\s*\d+|$|-{10,})', text, re.DOTALL | re.IGNORECASE)
    if match:
        solution = clean_text(match.group(1))
        return solution[:2000] if len(solution) > 2000 else solution
    return None

def detect_chapter(text, chapter_list):
    """Detect chapter from text by matching against known chapters"""
    text_lower = text.lower()
    
    for chapter in chapter_list:
        if chapter.lower() in text_lower:
            return chapter
    
    # Try partial matching
    for chapter in chapter_list:
        words = chapter.lower().split()
        if len(words) >= 2:
            if all(word in text_lower for word in words[:2]):
                return chapter
    
    return None

def extract_difficulty(text, question_num):
    """Estimate difficulty"""
    text_lower = text.lower()
    
    hard_keywords = ['assertion', 'reason', 'match the following', 'arrange', 'mechanism']
    medium_keywords = ['calculate', 'find the value', 'determine', 'which of the following']
    
    if any(kw in text_lower for kw in hard_keywords):
        return 'Hard'
    elif any(kw in text_lower for kw in medium_keywords):
        return 'Medium'
    return 'Easy' if question_num <= 10 else 'Medium'

def parse_combined_pdf(filepath, subject, chapter_list):
    """Parse a combined PDF file"""
    doc = fitz.open(filepath)
    full_text = ""
    
    print(f"   Reading {doc.page_count} pages...")
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n---PAGE {page_num + 1}---\n{text}"
    
    doc.close()
    
    # Split by question markers
    question_pattern = r'(?:^|\n)(?:Question|Q)[.\s]*(\d+)\s*\n'
    parts = re.split(question_pattern, full_text, flags=re.IGNORECASE)
    
    questions = []
    current_chapter = None
    
    for i in range(1, len(parts) - 1, 2):
        try:
            q_num = int(parts[i])
            q_text = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Detect chapter from surrounding text
            # Look at the page marker before this question
            page_match = re.search(r'---PAGE (\d+)---', parts[i-1] if i > 0 else "")
            if page_match:
                page_text = parts[i-1].split('---PAGE')[-1]
                detected = detect_chapter(page_text, chapter_list)
                if detected:
                    current_chapter = detected
            
            # Also check if chapter name appears in question text
            detected = detect_chapter(q_text[:200], chapter_list)
            if detected:
                current_chapter = detected
            
            # Find question text (before Options or Answer)
            question_end = re.search(
                r'(?:Options?:|Answer:|Solution:|JEE\s*(?:Main|Advanced)\s*\d{4})',
                q_text,
                re.IGNORECASE
            )
            
            if question_end:
                main_question = q_text[:question_end.start()]
            else:
                main_question = q_text[:800]
            
            main_question = clean_text(main_question)
            
            if len(main_question) < 15:
                continue
            
            # Extract metadata
            year = extract_year_from_text(q_text)
            exam_type = extract_exam_type(q_text)
            shift = extract_shift(q_text)
            options = extract_options(q_text)
            answer = extract_answer(q_text)
            solution = extract_solution(q_text)
            difficulty = extract_difficulty(q_text, q_num)
            question_type = 'MCQ' if options and any(options.values()) else 'Numerical'
            
            # Extract exam info
            exam_info_match = re.search(
                r'(JEE\s*(?:Main|Advanced)\s*\d{4}[^)]*(?:\([^)]+\))?[^,\n]*)',
                q_text,
                re.IGNORECASE
            )
            exam_info = clean_text(exam_info_match.group(1)) if exam_info_match else None
            
            question_data = {
                'questionNumber': q_num,
                'questionText': main_question,
                'year': year,
                'examType': exam_type,
                'shift': shift,
                'examInfo': exam_info,
                'options': options or {'A': '', 'B': '', 'C': '', 'D': ''},
                'correctAnswer': answer or '',
                'difficulty': difficulty,
                'solution': solution,
                'questionType': question_type,
                'chapter': current_chapter,
                'subject': subject
            }
            
            questions.append(question_data)
            
            # Progress indicator
            if len(questions) % 500 == 0:
                print(f"   Extracted {len(questions)} questions...")
            
        except Exception as e:
            continue
    
    return questions

async def seed_combined_pdf(pdf_path, subject, chapter_list):
    """Seed questions from a combined PDF"""
    
    print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
    print(f"   Subject: {subject}")
    
    questions = parse_combined_pdf(pdf_path, subject, chapter_list)
    print(f"   Found {len(questions)} questions")
    
    if not questions:
        print("   ⚠️ No questions extracted!")
        return 0
    
    # Count by year
    year_counts = {}
    for q in questions:
        y = q.get('year') or 'Unknown'
        year_counts[y] = year_counts.get(y, 0) + 1
    print(f"   Years: {dict(sorted(year_counts.items(), key=lambda x: str(x[0])))}")
    
    # Count by chapter
    chapter_counts = {}
    for q in questions:
        ch = q.get('chapter') or 'Unknown'
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
    print(f"   Chapters found: {len(chapter_counts)}")
    
    # Clear existing questions for this subject
    result = await db.questions.delete_many({"subject": subject})
    print(f"   Cleared {result.deleted_count} existing {subject} questions")
    
    # Insert questions
    inserted = 0
    
    for i, q_data in enumerate(questions, 1):
        try:
            if not q_data['questionText'] or len(q_data['questionText']) < 15:
                continue
            
            question_id = f"q_{uuid.uuid4().hex[:12]}"
            chapter = q_data.get('chapter') or f"{subject} General"
            
            # Use extracted year or default
            year = q_data['year'] if q_data['year'] else 2024
            
            question_doc = {
                "question_id": question_id,
                "subject": subject,
                "chapter": chapter,
                "topic": chapter,  # Use chapter as topic for now
                "examType": q_data['examType'],
                "year": year,
                "shift": q_data['shift'],
                "examInfo": q_data.get('examInfo'),
                "questionNumber": q_data['questionNumber'],
                "questionText": q_data['questionText'],
                "options": q_data['options'],
                "correctAnswer": q_data['correctAnswer'],
                "difficulty": q_data['difficulty'],
                "questionType": q_data['questionType'],
                "solution": q_data['solution'],
                "solutionYoutubeUrl": None,
                "solutionTimestamp": 0,
                "created_by": "system",
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.questions.insert_one(question_doc)
            inserted += 1
            
        except Exception as e:
            continue
    
    print(f"   ✅ Inserted {inserted} questions")
    return inserted

async def main():
    """Main function to process Physics and Math PDFs"""
    print("🚀 Processing Combined Physics and Math PDFs")
    print("=" * 60)
    
    pdf_dir = Path(__file__).parent.parent / 'pdfs'
    total = 0
    
    # Process Physics
    physics_pdf = pdf_dir / 'Combined-Physics.pdf'
    if physics_pdf.exists():
        count = await seed_combined_pdf(str(physics_pdf), 'Physics', PHYSICS_CHAPTERS)
        total += count
    
    # Process Math
    math_pdf = pdf_dir / 'Combined-Math.pdf'
    if math_pdf.exists():
        count = await seed_combined_pdf(str(math_pdf), 'Mathematics', MATH_CHAPTERS)
        total += count
    
    print("\n" + "=" * 60)
    print(f"📊 Total Questions Inserted: {total}")
    
    # Summary
    pipeline = [
        {"$group": {"_id": "$subject", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_subject = await db.questions.aggregate(pipeline).to_list(length=100)
    print(f"\nBy Subject:")
    for s in by_subject:
        print(f"  {s['_id']}: {s['count']}")
    
    # By year
    pipeline = [
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}}
    ]
    by_year = await db.questions.aggregate(pipeline).to_list(length=20)
    print(f"\nTop Years:")
    for y in by_year[:10]:
        print(f"  {y['_id']}: {y['count']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
