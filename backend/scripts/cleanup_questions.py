"""
Question Database Cleanup and Organization Script
Fixes:
1. Question type classification (MCQ vs Numerical)
2. Topic assignments based on question content
3. Empty options cleanup
4. Chapter standardization
"""
import asyncio
import re
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Topic mappings for each subject
PHYSICS_TOPICS = {
    'Alternating Currents': {
        'ac circuit': 'AC Circuits',
        'resonance': 'Resonance in AC',
        'transformer': 'Transformers',
        'power factor': 'Power Factor',
        'impedance': 'Impedance',
        'reactance': 'Reactance',
    },
    'Center of Mass': {
        'collision': 'Collisions',
        'momentum': 'Linear Momentum',
        'impulse': 'Impulse',
        'center of mass': 'Center of Mass',
        'recoil': 'Recoil',
    },
    'Motion in a Plane': {
        'projectile': 'Projectile Motion',
        'circular motion': 'Circular Motion',
        'relative motion': 'Relative Motion',
        'vector': 'Vectors',
    },
    'Gravitation': {
        'satellite': 'Satellites',
        'orbital': 'Orbital Motion',
        'escape velocity': 'Escape Velocity',
        'gravitational potential': 'Gravitational Potential',
        'kepler': 'Kepler Laws',
    },
    'Current Electricity': {
        'ohm': 'Ohm Law',
        'resistance': 'Resistance',
        'kirchhoff': 'Kirchhoff Laws',
        'potentiometer': 'Potentiometer',
        'wheatstone': 'Wheatstone Bridge',
        'meter bridge': 'Meter Bridge',
    },
    'Electrostatics': {
        'coulomb': 'Coulomb Law',
        'electric field': 'Electric Field',
        'gauss': 'Gauss Law',
        'capacitor': 'Capacitors',
        'dipole': 'Electric Dipole',
    },
    'Magnetism': {
        'biot-savart': 'Biot-Savart Law',
        'ampere': 'Ampere Law',
        'solenoid': 'Solenoid',
        'magnetic moment': 'Magnetic Moment',
        'torque': 'Torque on Coil',
    },
    'Optics': {
        'reflection': 'Reflection',
        'refraction': 'Refraction',
        'lens': 'Lenses',
        'mirror': 'Mirrors',
        'interference': 'Interference',
        'diffraction': 'Diffraction',
        'polarization': 'Polarization',
    },
    'Modern Physics': {
        'photoelectric': 'Photoelectric Effect',
        'de broglie': 'de Broglie Wavelength',
        'bohr': 'Bohr Model',
        'nuclear': 'Nuclear Physics',
        'radioactive': 'Radioactivity',
        'decay': 'Radioactive Decay',
        'half-life': 'Half-Life',
    },
    'Thermodynamics': {
        'first law': 'First Law',
        'second law': 'Second Law',
        'carnot': 'Carnot Engine',
        'entropy': 'Entropy',
        'heat engine': 'Heat Engines',
        'isothermal': 'Isothermal Process',
        'adiabatic': 'Adiabatic Process',
    },
    'Waves': {
        'wave equation': 'Wave Equation',
        'standing wave': 'Standing Waves',
        'doppler': 'Doppler Effect',
        'sound': 'Sound Waves',
        'beat': 'Beats',
        'resonance tube': 'Resonance Tube',
    },
    'Simple Harmonic Motion': {
        'shm': 'SHM Basics',
        'pendulum': 'Pendulum',
        'spring': 'Spring Oscillations',
        'time period': 'Time Period',
        'amplitude': 'Amplitude',
    },
    'Rotational Motion': {
        'moment of inertia': 'Moment of Inertia',
        'angular momentum': 'Angular Momentum',
        'torque': 'Torque',
        'rolling': 'Rolling Motion',
        'angular velocity': 'Angular Velocity',
    },
    'Fluids': {
        'bernoulli': 'Bernoulli Theorem',
        'viscosity': 'Viscosity',
        'surface tension': 'Surface Tension',
        'buoyancy': 'Buoyancy',
        'pressure': 'Fluid Pressure',
    },
}

MATH_TOPICS = {
    'Circle': {
        'equation of circle': 'Equation of Circle',
        'tangent': 'Tangent to Circle',
        'chord': 'Chords',
        'radical axis': 'Radical Axis',
        'family of circles': 'Family of Circles',
    },
    'Functions': {
        'domain': 'Domain and Range',
        'range': 'Domain and Range',
        'composition': 'Composite Functions',
        'inverse': 'Inverse Functions',
        'even': 'Even/Odd Functions',
        'odd': 'Even/Odd Functions',
        'periodic': 'Periodic Functions',
    },
    'Parabola': {
        'focus': 'Focus and Directrix',
        'directrix': 'Focus and Directrix',
        'tangent': 'Tangent to Parabola',
        'normal': 'Normal to Parabola',
        'chord': 'Focal Chord',
    },
    'Probability': {
        'bayes': 'Bayes Theorem',
        'conditional': 'Conditional Probability',
        'binomial': 'Binomial Distribution',
        'independent': 'Independent Events',
        'multiplication': 'Multiplication Rule',
    },
    'Limits and Derivatives': {
        'limit': 'Limits',
        'derivative': 'Derivatives',
        'differentiation': 'Differentiation',
        'continuity': 'Continuity',
        'l\'hospital': 'L\'Hospital Rule',
    },
    'Application of Derivatives': {
        'maxima': 'Maxima and Minima',
        'minima': 'Maxima and Minima',
        'tangent': 'Tangent and Normal',
        'rate of change': 'Rate of Change',
        'mean value': 'Mean Value Theorem',
        'rolle': 'Rolle Theorem',
    },
    'Definite Integration': {
        'area': 'Area Under Curves',
        'bounded region': 'Area Under Curves',
        'integration': 'Integration Techniques',
        'properties': 'Properties of Definite Integrals',
    },
    'Differential Equations': {
        'order': 'Order and Degree',
        'degree': 'Order and Degree',
        'linear': 'Linear Differential Equations',
        'homogeneous': 'Homogeneous Equations',
        'bernoulli': 'Bernoulli Equation',
    },
    'Three Dimensional Geometry': {
        'direction cosines': 'Direction Cosines',
        'direction ratios': 'Direction Ratios',
        'line': 'Line in 3D',
        'plane': 'Plane in 3D',
        'distance': 'Distance in 3D',
    },
    'Vector Algebra': {
        'dot product': 'Dot Product',
        'cross product': 'Cross Product',
        'scalar triple': 'Scalar Triple Product',
        'vector triple': 'Vector Triple Product',
        'collinear': 'Collinearity',
    },
    'Matrices': {
        'determinant': 'Determinants',
        'inverse': 'Inverse of Matrix',
        'adjoint': 'Adjoint Matrix',
        'rank': 'Rank of Matrix',
        'eigenvalue': 'Eigenvalues',
    },
    'Sequence and Series': {
        'arithmetic': 'Arithmetic Progression',
        'geometric': 'Geometric Progression',
        'harmonic': 'Harmonic Progression',
        'sum of series': 'Sum of Series',
        'nth term': 'nth Term',
    },
    'Complex Numbers': {
        'argand': 'Argand Plane',
        'modulus': 'Modulus',
        'argument': 'Argument',
        'de moivre': 'De Moivre Theorem',
        'roots of unity': 'Roots of Unity',
    },
    'Binomial Theorem': {
        'expansion': 'Binomial Expansion',
        'general term': 'General Term',
        'coefficient': 'Binomial Coefficients',
        'middle term': 'Middle Term',
    },
    'Permutation and Combination': {
        'permutation': 'Permutations',
        'combination': 'Combinations',
        'arrangement': 'Arrangements',
        'selection': 'Selections',
        'circular': 'Circular Permutations',
    },
}

CHEMISTRY_TOPICS = {
    'Coordination Compounds': {
        'ligand': 'Ligands',
        'isomerism': 'Isomerism',
        'crystal field': 'Crystal Field Theory',
        'nomenclature': 'IUPAC Nomenclature',
        'chelate': 'Chelation',
        'werner': 'Werner Theory',
        'magnetic': 'Magnetic Properties',
    },
    'Equilibrium': {
        'le chatelier': 'Le Chatelier Principle',
        'equilibrium constant': 'Equilibrium Constant',
        'buffer': 'Buffer Solutions',
        'ph': 'pH Calculations',
        'solubility product': 'Solubility Product',
        'ionic equilibrium': 'Ionic Equilibrium',
        'common ion': 'Common Ion Effect',
        'hydrolysis': 'Salt Hydrolysis',
    },
    'Chemical Bonding and Molecular Structure': {
        'hybridization': 'Hybridization',
        'vsepr': 'VSEPR Theory',
        'molecular orbital': 'Molecular Orbital Theory',
        'bond order': 'Bond Order',
        'dipole moment': 'Dipole Moment',
        'resonance': 'Resonance',
        'hydrogen bond': 'Hydrogen Bonding',
    },
    'Organic Chemistry - Some Basic Principles and Techniques': {
        'nomenclature': 'IUPAC Nomenclature',
        'isomerism': 'Isomerism',
        'inductive effect': 'Inductive Effect',
        'resonance': 'Resonance Effect',
        'hyperconjugation': 'Hyperconjugation',
        'carbocation': 'Carbocation Stability',
        'electrophile': 'Electrophilic Reactions',
        'nucleophile': 'Nucleophilic Reactions',
    },
    'Electrochemistry': {
        'nernst': 'Nernst Equation',
        'electrode potential': 'Electrode Potential',
        'electrolysis': 'Electrolysis',
        'faraday': 'Faraday Laws',
        'cell': 'Electrochemical Cells',
        'conductance': 'Conductance',
        'kohlrausch': 'Kohlrausch Law',
    },
    'Thermodynamics': {
        'enthalpy': 'Enthalpy',
        'entropy': 'Entropy',
        'gibbs': 'Gibbs Free Energy',
        'hess': 'Hess Law',
        'bond energy': 'Bond Energy',
        'heat of formation': 'Heat of Formation',
        'spontaneity': 'Spontaneity',
    },
    'Chemical Kinetics': {
        'rate': 'Rate of Reaction',
        'order': 'Order of Reaction',
        'molecularity': 'Molecularity',
        'half-life': 'Half-Life',
        'activation energy': 'Activation Energy',
        'arrhenius': 'Arrhenius Equation',
        'catalyst': 'Catalysis',
    },
    'Amines': {
        'basicity': 'Basicity of Amines',
        'diazonium': 'Diazonium Salts',
        'hoffmann': 'Hoffmann Degradation',
        'gabriel': 'Gabriel Synthesis',
        'carbylamine': 'Carbylamine Test',
    },
    'Alcohols, Phenols and Ethers': {
        'williamson': 'Williamson Synthesis',
        'dehydration': 'Dehydration Reactions',
        'lucas': 'Lucas Test',
        'grignard': 'Grignard Reactions',
        'kolbe': 'Kolbe Reaction',
    },
    'Haloalkanes and Haloarenes': {
        'sn1': 'SN1 Mechanism',
        'sn2': 'SN2 Mechanism',
        'elimination': 'Elimination Reactions',
        'wurtz': 'Wurtz Reaction',
        'sandmeyer': 'Sandmeyer Reaction',
        'finkelstein': 'Finkelstein Reaction',
    },
    'p-Block Elements': {
        'nitrogen': 'Nitrogen Family',
        'phosphorus': 'Phosphorus',
        'sulphur': 'Sulphur',
        'halogen': 'Halogens',
        'noble gas': 'Noble Gases',
        'ozone': 'Ozone',
        'interhalogen': 'Interhalogen Compounds',
    },
    's-Block Elements': {
        'alkali': 'Alkali Metals',
        'alkaline': 'Alkaline Earth Metals',
        'sodium': 'Sodium Compounds',
        'calcium': 'Calcium Compounds',
        'plaster': 'Plaster of Paris',
    },
    'The d- and f-Block Elements': {
        'transition': 'Transition Elements Properties',
        'lanthanide': 'Lanthanide Contraction',
        'oxidation state': 'Variable Oxidation States',
        'colour': 'Colour of Compounds',
        'magnetic': 'Magnetic Properties',
    },
}

def get_topic_for_question(question_text, chapter, subject):
    """Determine topic based on question text and chapter"""
    text_lower = question_text.lower() if question_text else ""
    
    topic_maps = {
        'Physics': PHYSICS_TOPICS,
        'Mathematics': MATH_TOPICS,
        'Chemistry': CHEMISTRY_TOPICS
    }
    
    if subject not in topic_maps:
        return chapter
    
    subject_topics = topic_maps[subject]
    
    # Find matching chapter
    matching_chapter = None
    for ch in subject_topics.keys():
        if ch.lower() in (chapter or '').lower():
            matching_chapter = ch
            break
    
    if not matching_chapter:
        # Try to match by keywords in any chapter
        for ch, topics in subject_topics.items():
            for keyword, topic in topics.items():
                if keyword in text_lower:
                    return topic
        return chapter  # Return chapter as topic if no match
    
    # Search for topic keywords
    for keyword, topic in subject_topics.get(matching_chapter, {}).items():
        if keyword in text_lower:
            return topic
    
    return f"{matching_chapter} - General"

def is_numerical_question(question_text, options, answer):
    """Determine if question is numerical type"""
    # Check if all options are empty
    if options:
        non_empty = sum(1 for v in options.values() if v and v.strip())
        if non_empty == 0:
            return True
    
    # Check question text for numerical indicators
    numerical_patterns = [
        r'is\s*_{2,}',  # is ____
        r'=\s*_{2,}',   # = ____
        r'_{2,}\s*(?:mg|g|kg|m|cm|mm|ml|l|mol|molar|%)',  # _____ units
        r'answer\s*(?:is|=)\s*\d',
        r'value\s+(?:is|=)',
        r'nearest\s+integer',
        r'rounded\s+off',
    ]
    
    text_lower = (question_text or '').lower()
    for pattern in numerical_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Check if answer is numeric
    if answer and re.match(r'^[\d\.\-]+$', str(answer).strip()):
        return True
    
    return False

async def fix_question_types():
    """Fix question type classification"""
    print("Fixing question types...")
    
    # Find MCQ questions with empty options
    cursor = db.questions.find({
        'questionType': 'MCQ',
        '$or': [
            {'options.A': ''},
            {'options.A': None}
        ]
    })
    
    fixed_count = 0
    async for q in cursor:
        if is_numerical_question(q.get('questionText'), q.get('options'), q.get('correctAnswer')):
            await db.questions.update_one(
                {'_id': q['_id']},
                {'$set': {'questionType': 'Numerical'}}
            )
            fixed_count += 1
    
    print(f"  Fixed {fixed_count} questions to Numerical type")
    return fixed_count

async def update_topics():
    """Update topics for all questions"""
    print("Updating topics...")
    
    cursor = db.questions.find({})
    updated_count = 0
    
    async for q in cursor:
        new_topic = get_topic_for_question(
            q.get('questionText', ''),
            q.get('chapter', ''),
            q.get('subject', '')
        )
        
        if new_topic != q.get('topic'):
            await db.questions.update_one(
                {'_id': q['_id']},
                {'$set': {'topic': new_topic}}
            )
            updated_count += 1
        
        if updated_count % 1000 == 0 and updated_count > 0:
            print(f"  Updated {updated_count} topics...")
    
    print(f"  Total topics updated: {updated_count}")
    return updated_count

async def standardize_chapters():
    """Standardize chapter names"""
    print("Standardizing chapter names...")
    
    # Chapter name mappings
    chapter_mappings = {
        'Organic Chemistry - Some Basic Principles': 'Organic Chemistry - Some Basic Principles and Techniques',
        'P-Block Elements (Group 15-18)': 'p-Block Elements (Group 15-18)',
        'P-Block Elements (Group 13-14)': 'p-Block Elements (Group 13-14)',
        'S-Block Elements': 's-Block Elements',
    }
    
    for old_name, new_name in chapter_mappings.items():
        result = await db.questions.update_many(
            {'chapter': old_name},
            {'$set': {'chapter': new_name}}
        )
        if result.modified_count > 0:
            print(f"  Renamed '{old_name}' -> '{new_name}': {result.modified_count}")
    
    # Merge duplicate chapters
    duplicates = [
        ('Organic Chemistry - Some Basic Principles and Techniques', 'Organic Chemistry - Some Basic Principles and Techniques'),
    ]

async def print_summary():
    """Print database summary"""
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY AFTER CLEANUP")
    print("=" * 60)
    
    total = await db.questions.count_documents({})
    print(f"\nTotal questions: {total}")
    
    # By subject
    pipeline = [
        {'$group': {'_id': '$subject', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    by_subject = await db.questions.aggregate(pipeline).to_list(100)
    print("\nBy Subject:")
    for s in by_subject:
        print(f"  {s['_id']}: {s['count']}")
    
    # By question type
    pipeline = [
        {'$group': {'_id': '$questionType', 'count': {'$sum': 1}}}
    ]
    by_type = await db.questions.aggregate(pipeline).to_list(100)
    print("\nBy Question Type:")
    for t in by_type:
        print(f"  {t['_id']}: {t['count']}")
    
    # Sample topics per subject
    for subject in ['Physics', 'Mathematics', 'Chemistry']:
        pipeline = [
            {'$match': {'subject': subject}},
            {'$group': {'_id': '$topic', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        topics = await db.questions.aggregate(pipeline).to_list(10)
        print(f"\nTop {subject} Topics:")
        for t in topics:
            print(f"  {t['_id']}: {t['count']}")

async def main():
    print("Starting question database cleanup...")
    print("=" * 60)
    
    await fix_question_types()
    await update_topics()
    await standardize_chapters()
    await print_summary()
    
    client.close()
    print("\nCleanup complete!")

if __name__ == "__main__":
    asyncio.run(main())
