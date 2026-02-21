"""
PDF Question Extractor for JEE PYQs
Extracts questions from chemistry chapter PDFs and stores them in MongoDB
"""
import fitz  # PyMuPDF
import re
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(Path(__file__).parent.parent / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Chapter mapping for proper naming
CHAPTER_MAPPING = {
    'Chemical-Bonding': 'Chemical Bonding and Molecular Structure',
    'Alcohols-Phenols-and-Ethers': 'Alcohols, Phenols and Ethers',
    'Amines': 'Amines',
    'Analytical-Chemistry': 'Analytical Chemistry',
    'Biomolecules': 'Biomolecules',
    'Chemical-Equilibrium': 'Equilibrium',
    'Chemical-Kinetics': 'Chemical Kinetics',
    'Chemical-Thermodynamics': 'Thermodynamics',
    'Chemistry-in-Everyday-Life': 'Chemistry in Everyday Life',
    'Classification-of-Elements': 'Classification of Elements and Periodicity'
}

def extract_year_from_text(text):
    """Extract year from JEE exam text"""
    patterns = [
        r'JEE\s*(?:Main|Advanced)\s*(\d{4})',
        r'(\d{4})\s*(?:Online|Offline)',
        r'(\d{4})\s*(?:January|February|March|April|May|June|July|August|September)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 2024  # Default year

def extract_exam_type(text):
    """Extract exam type (JEE Main or JEE Advanced)"""
    if 'advanced' in text.lower():
        return 'JEE_Advanced'
    return 'JEE_Main'

def extract_shift(text):
    """Extract shift information"""
    if 'morning' in text.lower():
        return 'Morning'
    elif 'evening' in text.lower():
        return 'Evening'
    return None

def clean_text(text):
    """Clean up extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove page breaks
    text = re.sub(r'-{20,}', '', text)
    return text.strip()

def extract_options(text):
    """Extract MCQ options from text"""
    options = {}
    
    # Pattern for options: A. text, B. text, etc.
    option_pattern = r'(?:^|\n)\s*([A-D])[.\)]\s*(.+?)(?=(?:\n\s*[A-D][.\)]|\nAnswer:|$))'
    matches = re.findall(option_pattern, text, re.MULTILINE | re.DOTALL)
    
    for letter, content in matches:
        options[letter] = clean_text(content)
    
    return options if len(options) >= 2 else None

def extract_answer(text):
    """Extract correct answer"""
    # Look for Answer: pattern
    match = re.search(r'Answer:\s*([A-D]|\d+)', text, re.IGNORECASE)
    if match:
        ans = match.group(1).upper()
        if ans in ['A', 'B', 'C', 'D']:
            return ans
        return ans
    return None

def extract_difficulty(text, question_num):
    """Estimate difficulty based on question patterns"""
    # Simple heuristic based on keywords and question complexity
    hard_keywords = ['assertion', 'reason', 'match', 'arrange', 'order', 'compare']
    medium_keywords = ['calculate', 'find', 'determine', 'which of the following']
    
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in hard_keywords):
        return 'Hard'
    elif any(kw in text_lower for kw in medium_keywords):
        return 'Medium'
    else:
        return 'Easy' if question_num <= 10 else 'Medium'

def parse_pdf(filepath):
    """Parse a PDF file and extract questions"""
    doc = fitz.open(filepath)
    full_text = ""
    
    for page in doc:
        full_text += page.get_text() + "\n"
    
    doc.close()
    
    # Split by question markers
    question_pattern = r'(?:^|\n)Question\s*(\d+)\s*\n'
    parts = re.split(question_pattern, full_text)
    
    questions = []
    
    # Parts will be: [preamble, q1_num, q1_text, q2_num, q2_text, ...]
    for i in range(1, len(parts) - 1, 2):
        try:
            q_num = int(parts[i])
            q_text = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Find the question text (before Options or Answer)
            question_end = re.search(r'(?:Options:|Answer:|JEE\s*(?:Main|Advanced)\s*\d{4})', q_text)
            if question_end:
                main_question = q_text[:question_end.start()]
            else:
                main_question = q_text[:500]  # Take first 500 chars if no marker
            
            # Clean up the question text
            main_question = clean_text(main_question)
            
            # Skip if question is too short
            if len(main_question) < 20:
                continue
            
            # Extract metadata
            year = extract_year_from_text(q_text)
            exam_type = extract_exam_type(q_text)
            shift = extract_shift(q_text)
            options = extract_options(q_text)
            answer = extract_answer(q_text)
            difficulty = extract_difficulty(q_text, q_num)
            
            # Extract solution if present
            solution_match = re.search(r'Solution:\s*(.+?)(?=Question\d+|$)', q_text, re.DOTALL)
            solution = clean_text(solution_match.group(1))[:1000] if solution_match else None
            
            question_data = {
                'questionNumber': q_num,
                'questionText': main_question,
                'year': year,
                'examType': exam_type,
                'shift': shift,
                'options': options or {'A': '', 'B': '', 'C': '', 'D': ''},
                'correctAnswer': answer or 'A',
                'difficulty': difficulty,
                'solution': solution,
                'questionType': 'MCQ' if options else 'Numerical'
            }
            
            questions.append(question_data)
            
        except Exception as e:
            print(f"  Warning: Could not parse question {i}: {e}")
            continue
    
    return questions

async def seed_questions_from_pdf(pdf_path, chapter_name):
    """Seed questions from a PDF into MongoDB"""
    
    print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
    print(f"   Chapter: {chapter_name}")
    
    # Parse PDF
    questions = parse_pdf(pdf_path)
    print(f"   Found {len(questions)} questions")
    
    if not questions:
        print("   ⚠️ No questions extracted!")
        return 0
    
    # Clear existing questions for this chapter (optional)
    result = await db.questions.delete_many({"chapter": chapter_name})
    print(f"   Cleared {result.deleted_count} existing questions")
    
    # Insert questions
    inserted = 0
    for i, q_data in enumerate(questions, 1):
        try:
            question_id = f"q_{uuid.uuid4().hex[:12]}"
            row_id = f"{chapter_name[:3].upper()}{str(i).zfill(3)}"
            
            # Determine topic based on question content (simplified)
            topic = determine_topic(q_data['questionText'], chapter_name)
            
            question_doc = {
                "question_id": question_id,
                "googleSheetRowId": row_id,
                "subject": "Chemistry",
                "chapter": chapter_name,
                "topic": topic,
                "examType": q_data['examType'],
                "year": q_data['year'],
                "shift": q_data['shift'],
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
            print(f"   Error inserting question {i}: {e}")
            continue
    
    print(f"   ✅ Inserted {inserted} questions")
    return inserted

def determine_topic(question_text, chapter_name):
    """Determine topic based on question content"""
    text_lower = question_text.lower()
    
    topic_mapping = {
        'Chemical Bonding and Molecular Structure': {
            'hybridization': 'Hybridization',
            'vsepr': 'VSEPR Theory',
            'molecular orbital': 'Molecular Orbital Theory',
            'bond order': 'Bond Order',
            'dipole moment': 'Dipole Moment',
            'hydrogen bond': 'Hydrogen Bonding',
            'ionic': 'Ionic Bonding',
            'covalent': 'Covalent Bonding',
            'resonance': 'Resonance',
            'lewis': 'Lewis Structure',
        },
        'Alcohols, Phenols and Ethers': {
            'alcohol': 'Alcohols',
            'phenol': 'Phenols',
            'ether': 'Ethers',
            'williamson': 'Williamson Synthesis',
            'dehydration': 'Dehydration',
            'oxidation': 'Oxidation Reactions',
            'grignard': 'Grignard Reactions',
        },
        'Amines': {
            'primary amine': 'Primary Amines',
            'secondary amine': 'Secondary Amines',
            'tertiary amine': 'Tertiary Amines',
            'basicity': 'Basicity of Amines',
            'diazonium': 'Diazonium Salts',
            'hoffmann': 'Hoffmann Degradation',
            'gabriel': 'Gabriel Synthesis',
        },
        'Analytical Chemistry': {
            'chromatography': 'Chromatography',
            'titration': 'Titrations',
            'qualitative': 'Qualitative Analysis',
            'quantitative': 'Quantitative Analysis',
        },
        'Biomolecules': {
            'carbohydrate': 'Carbohydrates',
            'protein': 'Proteins',
            'amino acid': 'Amino Acids',
            'nucleic acid': 'Nucleic Acids',
            'enzyme': 'Enzymes',
            'vitamin': 'Vitamins',
            'lipid': 'Lipids',
        }
    }
    
    if chapter_name in topic_mapping:
        for keyword, topic in topic_mapping[chapter_name].items():
            if keyword in text_lower:
                return topic
    
    # Default topic
    return chapter_name.split()[0] + " Basics"

async def main():
    """Main function to process all PDFs"""
    
    print("🚀 Starting PDF Question Extraction")
    print("=" * 50)
    
    pdf_dir = Path(__file__).parent.parent / 'pdfs'
    total_inserted = 0
    
    for pdf_file in pdf_dir.glob('*.pdf'):
        # Get chapter name from filename
        base_name = pdf_file.stem
        chapter_name = CHAPTER_MAPPING.get(base_name, base_name.replace('-', ' '))
        
        inserted = await seed_questions_from_pdf(str(pdf_file), chapter_name)
        total_inserted += inserted
    
    print("\n" + "=" * 50)
    print(f"📊 Total Questions Inserted: {total_inserted}")
    
    # Print summary
    total = await db.questions.count_documents({})
    chemistry = await db.questions.count_documents({"subject": "Chemistry"})
    
    print(f"\n📈 Database Summary:")
    print(f"   Total questions: {total}")
    print(f"   Chemistry questions: {chemistry}")
    
    # Print by chapter
    pipeline = [
        {"$match": {"subject": "Chemistry"}},
        {"$group": {"_id": "$chapter", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    chapters = await db.questions.aggregate(pipeline).to_list(length=100)
    print(f"\n   By Chapter:")
    for ch in chapters:
        print(f"   - {ch['_id']}: {ch['count']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
