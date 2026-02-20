"""Seed database with Chemical Equilibrium questions"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
from seed.chemical_equilibrium_questions import CHEMICAL_EQUILIBRIUM_QUESTIONS

load_dotenv(Path(__file__).parent.parent / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_questions():
    """Seed questions into database"""
    
    print("🌱 Seeding Chemical Equilibrium questions...")
    
    # Clear existing questions (optional)
    result = await db.questions.delete_many({"chapter": "Chemical Equilibrium"})
    print(f"   Cleared {result.deleted_count} existing questions")
    
    # Insert questions
    inserted_count = 0
    for i, q_data in enumerate(CHEMICAL_EQUILIBRIUM_QUESTIONS, 1):
        question_id = f"q_{uuid.uuid4().hex[:12]}"
        row_id = f"Q{str(i).zfill(3)}"
        
        question_doc = {
            "question_id": question_id,
            "googleSheetRowId": row_id,
            **q_data,
            "created_by": "system",
            "created_at": datetime.now(timezone.utc)
        }
        
        # Remove _id if it exists
        question_doc.pop("_id", None)
        
        await db.questions.insert_one(question_doc)
        inserted_count += 1
    
    print(f"✅ Successfully seeded {inserted_count} questions!")
    
    # Print summary
    total = await db.questions.count_documents({})
    chemistry = await db.questions.count_documents({"subject": "Chemistry"})
    chem_eq = await db.questions.count_documents({"chapter": "Chemical Equilibrium"})
    
    print(f"\n📊 Database Summary:")
    print(f"   Total questions: {total}")
    print(f"   Chemistry questions: {chemistry}")
    print(f"   Chemical Equilibrium questions: {chem_eq}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_questions())
