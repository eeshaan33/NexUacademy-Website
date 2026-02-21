"""
PDF Question Extractor v2 for JEE PYQs
Improved extraction with better year handling, option parsing, and image detection
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
    'Classification-of-Elements': 'Classification of Elements and Periodicity',
    'Coordination-Compounds': 'Coordination Compounds',
    'D-and-F-Block-Elements': 'The d- and f-Block Elements',
    'Electrochemistry': 'Electrochemistry',
    'Environmental-Chemistry': 'Environmental Chemistry',
    'Equilibrium-New': 'Equilibrium',
    'General-Principles': 'General Principles and Processes of Isolation of Elements',
    'Haloalkanes-and-Haloarenes': 'Haloalkanes and Haloarenes',
    'Hydrocarbons': 'Hydrocarbons',
    'Hydrogen': 'Hydrogen',
    'Organic-Chemistry-Some-Basic-Principles': 'Organic Chemistry - Some Basic Principles and Techniques',
    'Organic-Chemistry-Basics': 'Organic Chemistry - Some Basic Principles and Techniques',
    'P-Block-Elements-15-18': 'p-Block Elements (Group 15-18)',
    'P-Block-Elements-Group-13-14': 'p-Block Elements (Group 13-14)',
    'Polymers': 'Polymers',
    'Redox-Reactions': 'Redox Reactions',
    'S-Block': 's-Block Elements',
}

def extract_year_from_text(text):
    """Extract year from JEE exam text - improved version"""
    # Priority patterns for year extraction
    patterns = [
        # JEE Main 2025 (Online) 22nd January Evening Shift
        r'JEE\s*Main\s*(\d{4})\s*\(Online\)',
        # JEE Advanced 2024
        r'JEE\s*Advanced\s*(\d{4})',
        # JEE Main 2023
        r'JEE\s*Main\s*(\d{4})',
        # [24-Jan-2023 Shift 1] - date format
        r'\[?\d{1,2}[-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-/](\d{4})',
        # [2023] or (2023)
        r'[\[\(](\d{4})[\]\)]',
        # Online April 19, 2014
        r'Online\s+\w+\s+\d{1,2},?\s+(\d{4})',
        # Sep. 02, 2020
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+\d{1,2},?\s+(\d{4})',
        # 2020 (II) or 2020 (I)
        r'(\d{4})\s*\([IVX]+\)',
        # Just a 4-digit year between 2010-2026
        r'\b(20[12]\d)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 2010 <= year <= 2026:
                return year
    
    return None  # Return None instead of default to handle missing years

def extract_exam_type(text):
    """Extract exam type (JEE Main or JEE Advanced)"""
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
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove page breaks
    text = re.sub(r'-{10,}', '', text)
    # Clean up common OCR artifacts
    text = re.sub(r'={3,}', '', text)
    return text.strip()

def clean_option_text(text):
    """Clean option text - handle subscripts, superscripts, chemical formulas"""
    text = clean_text(text)
    # Remove trailing option letters that might have been captured
    text = re.sub(r'\s+[A-D]\.$', '', text)
    # Clean up common chemical notation issues
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # Join split numbers
    return text.strip()

def extract_options_improved(text):
    """Extract MCQ options with improved parsing"""
    options = {}
    
    # Multiple patterns for different option formats
    patterns = [
        # Pattern 1: A. text (newline or next option)
        r'(?:^|\n)\s*([A-D])[.\)]\s*(.+?)(?=(?:\n\s*[A-D][.\)]|\nAnswer:|\nSolution:|$))',
        # Pattern 2: Options: followed by A., B., etc
        r'Options?:.*?([A-D])[.\)]\s*(.+?)(?=(?:[A-D][.\)]|\nAnswer:|\nSolution:|$))',
        # Pattern 3: (A) text format
        r'\(([A-D])\)\s*(.+?)(?=(?:\([A-D]\)|\nAnswer:|\nSolution:|$))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if matches and len(matches) >= 2:
            for letter, content in matches:
                letter = letter.upper()
                if letter in ['A', 'B', 'C', 'D']:
                    options[letter] = clean_option_text(content)
            if len(options) >= 2:
                break
    
    # Ensure we have all 4 options
    for letter in ['A', 'B', 'C', 'D']:
        if letter not in options:
            options[letter] = ''
    
    return options if any(options.values()) else None

def extract_answer_improved(text):
    """Extract correct answer with improved parsing"""
    # Multiple patterns for answer extraction
    patterns = [
        # Answer: A or Answer: (A)
        r'Answer:\s*\(?([A-D])\)?',
        # Ans: A or Ans. A
        r'Ans[.:]?\s*\(?([A-D])\)?',
        # Correct Answer: A
        r'Correct\s*Answer[.:]?\s*\(?([A-D])\)?',
        # For numerical answers
        r'Answer:\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            ans = match.group(1)
            if ans.upper() in ['A', 'B', 'C', 'D']:
                return ans.upper()
            # Return numerical answer as is
            return ans
    
    return None

def extract_solution(text):
    """Extract solution text"""
    match = re.search(r'Solution:\s*(.+?)(?=Question\s*\d+|$)', text, re.DOTALL | re.IGNORECASE)
    if match:
        solution = clean_text(match.group(1))
        # Limit solution length
        return solution[:2000] if len(solution) > 2000 else solution
    return None

def detect_has_image(text, page_images=None):
    """Detect if question likely has an image"""
    # Text indicators of images
    image_indicators = [
        r'(?:figure|diagram|structure|graph|image|picture|shown|below|above)\s*(?:is|are|given|shows)',
        r'(?:as shown|see figure|refer to|in the figure)',
        r'(?:the following|given below)',
        r'(?:match|column|list).+(?:with|to)',
    ]
    
    for pattern in image_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return page_images and len(page_images) > 0

def extract_difficulty(text, question_num):
    """Estimate difficulty based on question patterns"""
    text_lower = text.lower()
    
    # Hard indicators
    hard_keywords = ['assertion', 'reason', 'match the following', 'arrange in order', 
                     'correct order', 'rank', 'compare', 'mechanism', 'multi-step']
    # Medium indicators
    medium_keywords = ['calculate', 'find the value', 'determine', 'which of the following',
                       'how many', 'number of', 'ratio', 'percentage']
    # Easy indicators
    easy_keywords = ['identify', 'name', 'define', 'what is', 'which is']
    
    if any(kw in text_lower for kw in hard_keywords):
        return 'Hard'
    elif any(kw in text_lower for kw in medium_keywords):
        return 'Medium'
    elif any(kw in text_lower for kw in easy_keywords):
        return 'Easy'
    
    # Default based on position (earlier questions tend to be easier)
    if question_num <= 5:
        return 'Easy'
    elif question_num <= 15:
        return 'Medium'
    return 'Hard'

def determine_question_type(text, options):
    """Determine if MCQ or Numerical"""
    if options and any(options.values()):
        return 'MCQ'
    
    # Check for numerical indicators
    if re.search(r'(?:answer|value|result)\s*(?:is|=|:)\s*\d', text, re.IGNORECASE):
        return 'Numerical'
    if re.search(r'calculate|find the value|determine the', text, re.IGNORECASE):
        return 'Numerical'
    
    return 'MCQ'

def parse_pdf_improved(filepath):
    """Parse a PDF file with improved extraction"""
    doc = fitz.open(filepath)
    full_text = ""
    page_images = []
    
    for page_num, page in enumerate(doc):
        full_text += f"\n---PAGE {page_num + 1}---\n"
        full_text += page.get_text()
        
        # Count images on this page
        images = page.get_images()
        if images:
            page_images.append((page_num, len(images)))
    
    doc.close()
    
    # Split by question markers
    # Handle formats: Question1, Question 1, Q1, Q.1
    question_pattern = r'(?:^|\n)(?:Question|Q)[.\s]*(\d+)\s*\n'
    parts = re.split(question_pattern, full_text, flags=re.IGNORECASE)
    
    questions = []
    
    # Parts will be: [preamble, q1_num, q1_text, q2_num, q2_text, ...]
    for i in range(1, len(parts) - 1, 2):
        try:
            q_num = int(parts[i])
            q_text = parts[i + 1] if i + 1 < len(parts) else ""
            
            # Find the question text (before Options or Answer)
            question_end = re.search(
                r'(?:Options?:|Answer:|Solution:|JEE\s*(?:Main|Advanced)\s*\d{4})',
                q_text,
                re.IGNORECASE
            )
            
            if question_end:
                main_question = q_text[:question_end.start()]
            else:
                main_question = q_text[:800]  # Take more text if no clear marker
            
            # Clean up the question text
            main_question = clean_text(main_question)
            
            # Skip if question is too short
            if len(main_question) < 15:
                continue
            
            # Extract metadata
            year = extract_year_from_text(q_text)
            exam_type = extract_exam_type(q_text)
            shift = extract_shift(q_text)
            options = extract_options_improved(q_text)
            answer = extract_answer_improved(q_text)
            solution = extract_solution(q_text)
            difficulty = extract_difficulty(q_text, q_num)
            question_type = determine_question_type(q_text, options)
            has_image = detect_has_image(q_text)
            
            # Extract exam info string for display
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
                'hasImage': has_image
            }
            
            questions.append(question_data)
            
        except Exception as e:
            print(f"  Warning: Could not parse question {i}: {e}")
            continue
    
    return questions

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
        'p-Block Elements (Group 15-18)': {
            'nitrogen': 'Nitrogen Family',
            'phosphorus': 'Phosphorus',
            'oxygen': 'Oxygen Family',
            'sulphur': 'Sulphur',
            'sulfur': 'Sulphur',
            'halogen': 'Halogens',
            'noble gas': 'Noble Gases',
            'ozone': 'Ozone',
            'h2so4': 'Sulphuric Acid',
            'hno3': 'Nitric Acid',
        },
        'p-Block Elements (Group 13-14)': {
            'boron': 'Boron Family',
            'aluminium': 'Aluminium',
            'aluminum': 'Aluminium',
            'carbon': 'Carbon Family',
            'silicon': 'Silicon',
            'allotrope': 'Allotropes',
        },
        'Polymers': {
            'addition polymer': 'Addition Polymers',
            'condensation polymer': 'Condensation Polymers',
            'natural polymer': 'Natural Polymers',
            'synthetic polymer': 'Synthetic Polymers',
            'rubber': 'Rubber',
            'nylon': 'Nylon',
            'polyester': 'Polyester',
            'bakelite': 'Bakelite',
        },
        'Redox Reactions': {
            'oxidation': 'Oxidation',
            'reduction': 'Reduction',
            'disproportionation': 'Disproportionation',
            'oxidation state': 'Oxidation States',
            'oxidising agent': 'Oxidising Agents',
            'oxidizing agent': 'Oxidising Agents',
            'reducing agent': 'Reducing Agents',
            'balancing': 'Balancing Redox Reactions',
            'titration': 'Redox Titrations',
        },
        's-Block Elements': {
            'alkali metal': 'Alkali Metals',
            'alkaline earth': 'Alkaline Earth Metals',
            'sodium': 'Sodium Compounds',
            'potassium': 'Potassium Compounds',
            'calcium': 'Calcium Compounds',
            'magnesium': 'Magnesium Compounds',
            'lithium': 'Lithium',
        },
        'Hydrocarbons': {
            'alkane': 'Alkanes',
            'alkene': 'Alkenes',
            'alkyne': 'Alkynes',
            'aromatic': 'Aromatic Compounds',
            'benzene': 'Benzene',
            'markovnikov': 'Markovnikov Rule',
            'anti-markovnikov': 'Anti-Markovnikov Rule',
            'hydrogenation': 'Hydrogenation',
            'combustion': 'Combustion',
            'isomerism': 'Isomerism',
            'conformations': 'Conformations',
        },
        'Haloalkanes and Haloarenes': {
            'sn1': 'SN1 Mechanism',
            'sn2': 'SN2 Mechanism',
            'elimination': 'Elimination Reactions',
            'nucleophilic': 'Nucleophilic Substitution',
            'grignard': 'Grignard Reagent',
            'wurtz': 'Wurtz Reaction',
            'halogenation': 'Halogenation',
        },
        'Hydrogen': {
            'isotope': 'Isotopes of Hydrogen',
            'hydrogen peroxide': 'Hydrogen Peroxide',
            'hydride': 'Hydrides',
            'water': 'Properties of Water',
            'heavy water': 'Heavy Water',
        },
        'General Principles and Processes of Isolation of Elements': {
            'extraction': 'Extraction of Metals',
            'reduction': 'Reduction Processes',
            'refining': 'Refining of Metals',
            'leaching': 'Leaching',
            'electrolytic': 'Electrolytic Reduction',
            'roasting': 'Roasting',
            'calcination': 'Calcination',
            'ore': 'Ores and Minerals',
        },
        'Organic Chemistry - Some Basic Principles and Techniques': {
            'nomenclature': 'IUPAC Nomenclature',
            'isomerism': 'Isomerism',
            'resonance': 'Resonance',
            'inductive effect': 'Inductive Effect',
            'hyperconjugation': 'Hyperconjugation',
            'carbocation': 'Carbocations',
            'carbanion': 'Carbanions',
            'free radical': 'Free Radicals',
            'electrophile': 'Electrophiles',
            'nucleophile': 'Nucleophiles',
        },
        'Equilibrium': {
            'le chatelier': 'Le Chatelier Principle',
            'equilibrium constant': 'Equilibrium Constant',
            'buffer': 'Buffer Solutions',
            'ph': 'pH and pOH',
            'solubility': 'Solubility Product',
            'ionic equilibrium': 'Ionic Equilibrium',
        },
        'Chemical Kinetics': {
            'rate': 'Rate of Reaction',
            'order': 'Order of Reaction',
            'half life': 'Half Life',
            'activation energy': 'Activation Energy',
            'arrhenius': 'Arrhenius Equation',
        },
        'Thermodynamics': {
            'enthalpy': 'Enthalpy',
            'entropy': 'Entropy',
            'gibbs': 'Gibbs Energy',
            'hess': 'Hess Law',
            'bond energy': 'Bond Energy',
        },
        'Electrochemistry': {
            'electrode potential': 'Electrode Potential',
            'nernst': 'Nernst Equation',
            'electrolysis': 'Electrolysis',
            'faraday': 'Faraday Laws',
            'cell': 'Electrochemical Cells',
        },
        'Coordination Compounds': {
            'ligand': 'Ligands',
            'coordination number': 'Coordination Number',
            'isomer': 'Isomerism',
            'crystal field': 'Crystal Field Theory',
            'chelate': 'Chelation',
        },
        'The d- and f-Block Elements': {
            'transition': 'Transition Elements',
            'lanthanide': 'Lanthanides',
            'actinide': 'Actinides',
            'oxidation state': 'Oxidation States',
        },
        'Biomolecules': {
            'carbohydrate': 'Carbohydrates',
            'protein': 'Proteins',
            'amino acid': 'Amino Acids',
            'nucleic acid': 'Nucleic Acids',
            'enzyme': 'Enzymes',
            'vitamin': 'Vitamins',
        },
    }
    
    if chapter_name in topic_mapping:
        for keyword, topic in topic_mapping[chapter_name].items():
            if keyword in text_lower:
                return topic
    
    # Default topic
    return chapter_name.split()[0] + " Basics"

async def seed_questions_from_pdf(pdf_path, chapter_name, clear_existing=True):
    """Seed questions from a PDF into MongoDB with improved extraction"""
    
    print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
    print(f"   Chapter: {chapter_name}")
    
    # Parse PDF with improved extraction
    questions = parse_pdf_improved(pdf_path)
    print(f"   Found {len(questions)} questions")
    
    if not questions:
        print("   ⚠️ No questions extracted!")
        return 0
    
    # Count questions by year
    year_counts = {}
    for q in questions:
        y = q.get('year') or 'Unknown'
        year_counts[y] = year_counts.get(y, 0) + 1
    print(f"   Years: {dict(sorted(year_counts.items(), key=lambda x: str(x[0])))}")
    
    if clear_existing:
        # Clear existing questions for this chapter
        result = await db.questions.delete_many({"chapter": chapter_name})
        print(f"   Cleared {result.deleted_count} existing questions")
    
    # Insert questions
    inserted = 0
    skipped = 0
    
    for i, q_data in enumerate(questions, 1):
        try:
            # Skip questions with missing critical data
            if not q_data['questionText'] or len(q_data['questionText']) < 15:
                skipped += 1
                continue
            
            question_id = f"q_{uuid.uuid4().hex[:12]}"
            row_id = f"{chapter_name[:3].upper()}{str(i).zfill(3)}"
            
            # Determine topic based on question content
            topic = determine_topic(q_data['questionText'], chapter_name)
            
            # Use extracted year or default to current year if none found
            year = q_data['year'] if q_data['year'] else 2024
            
            question_doc = {
                "question_id": question_id,
                "googleSheetRowId": row_id,
                "subject": "Chemistry",
                "chapter": chapter_name,
                "topic": topic,
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
                "hasImage": q_data.get('hasImage', False),
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
            skipped += 1
            continue
    
    print(f"   ✅ Inserted {inserted} questions (skipped {skipped})")
    return inserted

async def process_specific_pdfs(pdf_names):
    """Process specific PDFs"""
    pdf_dir = Path(__file__).parent.parent / 'pdfs'
    total = 0
    
    for pdf_name in pdf_names:
        pdf_path = pdf_dir / pdf_name
        if pdf_path.exists():
            base_name = pdf_path.stem
            chapter_name = CHAPTER_MAPPING.get(base_name, base_name.replace('-', ' '))
            count = await seed_questions_from_pdf(str(pdf_path), chapter_name)
            total += count
        else:
            print(f'PDF not found: {pdf_name}')
    
    return total

async def reprocess_all_pdfs():
    """Reprocess all PDFs with improved extraction"""
    print("🚀 Reprocessing ALL PDFs with improved extraction")
    print("=" * 60)
    
    pdf_dir = Path(__file__).parent.parent / 'pdfs'
    total_inserted = 0
    
    for pdf_file in sorted(pdf_dir.glob('*.pdf')):
        base_name = pdf_file.stem
        chapter_name = CHAPTER_MAPPING.get(base_name, base_name.replace('-', ' '))
        inserted = await seed_questions_from_pdf(str(pdf_file), chapter_name)
        total_inserted += inserted
    
    print("\n" + "=" * 60)
    print(f"📊 Total Questions Inserted: {total_inserted}")
    
    # Print summary
    total = await db.questions.count_documents({})
    
    print(f"\n📈 Database Summary:")
    print(f"   Total questions: {total}")
    
    # Print by year
    pipeline = [
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}}
    ]
    by_year = await db.questions.aggregate(pipeline).to_list(length=100)
    print(f"\n   By Year:")
    for y in by_year:
        print(f"   - {y['_id']}: {y['count']}")
    
    # Print by chapter
    pipeline = [
        {"$group": {"_id": "$chapter", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    chapters = await db.questions.aggregate(pipeline).to_list(length=100)
    print(f"\n   By Chapter:")
    for ch in chapters:
        print(f"   - {ch['_id']}: {ch['count']}")
    
    client.close()

async def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        await reprocess_all_pdfs()
    else:
        # Process just the 5 new PDFs
        new_pdfs = [
            'P-Block-Elements-15-18.pdf',
            'P-Block-Elements-Group-13-14.pdf',
            'Polymers.pdf',
            'Redox-Reactions.pdf',
            'S-Block.pdf'
        ]
        total = await process_specific_pdfs(new_pdfs)
        print(f"\nTotal new questions: {total}")
        
        # Summary
        total_q = await db.questions.count_documents({})
        print(f"Total in database: {total_q}")
        
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
