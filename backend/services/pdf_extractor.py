import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class JEEQuestionExtractor:
    """
    Extracts JEE questions from text content.
    This is a simplified version - in production, you'd use more sophisticated NLP.
    """
    
    def __init__(self):
        self.chapter_keywords = {
            "Chemical Equilibrium": [
                "solubility", "ksp", "equilibrium", "ph", "poh", "buffer",
                "acid", "base", "titration", "ionization", "dissociation",
                "le chatelier", "catalyst", "reaction quotient"
            ],
            "Thermodynamics": [
                "enthalpy", "entropy", "gibbs", "spontaneous", "heat capacity",
                "hess law", "carnot", "reversible"
            ],
            "Electrochemistry": [
                "electrode", "cell", "nernst", "conductance", "electrolysis",
                "oxidation", "reduction", "galvanic"
            ]
        }
    
    def detect_chapter(self, question_text: str) -> str:
        """
        Detect chapter based on keywords in question text.
        """
        question_lower = question_text.lower()
        
        scores = {}
        for chapter, keywords in self.chapter_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            scores[chapter] = score
        
        # Return chapter with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return "Chemical Equilibrium"  # Default for this PDF
    
    def detect_difficulty(self, question_text: str, has_calculation: bool) -> str:
        """
        Estimate difficulty based on question characteristics.
        """
        # Simple heuristics
        if len(question_text) > 300:
            return "Hard"
        elif has_calculation or "calculate" in question_text.lower():
            return "Medium"
        return "Easy"
    
    def extract_from_analyzed_data(self, questions_data: List[Dict]) -> List[Dict]:
        """
        Convert analyzed PDF data into structured question format.
        """
        structured_questions = []
        
        for q in questions_data:
            try:
                # Extract options
                options = q.get("options", {})
                if not options or len(options) < 4:
                    # Try to parse from question text
                    options = self._extract_options_from_text(q.get("question_text", ""))
                
                # Detect chapter and topic
                chapter = self.detect_chapter(q.get("question_text", ""))
                
                structured_q = {
                    "questionNumber": q.get("question_number", 0),
                    "examType": "JEE_Main",  # Default, can be specified
                    "subject": "Chemistry",  # For this PDF
                    "chapter": chapter,
                    "topic": q.get("topic", "Ionic Equilibrium"),
                    "year": 2024,  # Default, can be specified
                    "difficulty": self.detect_difficulty(
                        q.get("question_text", ""),
                        "calculate" in q.get("question_text", "").lower()
                    ),
                    "questionText": q.get("question_text", ""),
                    "questionImageUrl": "",
                    "options": options,
                    "correctAnswer": q.get("correct_answer", ""),
                    "solution": q.get("solution", ""),
                    "marks": 4,
                    "negativeMarks": -1,
                    "solutionYoutubeUrl": "",
                    "solutionTimestamp": 0
                }
                
                structured_questions.append(structured_q)
                
            except Exception as e:
                logger.error(f"Error processing question {q.get('question_number', '?')}: {e}")
                continue
        
        return structured_questions
    
    def _extract_options_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract options A, B, C, D from question text.
        """
        options = {}
        
        # Try to find options marked as A), B), C), D) or (A), (B), etc.
        pattern = r'[\(\[]?([A-D])[\)\]][\.:]?\s*(.+?)(?=[\(\[]?[A-D][\)\]]|$)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            option_letter = match[0].upper()
            option_text = match[1].strip()
            if option_letter in ['A', 'B', 'C', 'D']:
                options[option_letter] = option_text[:200]  # Limit length
        
        # Ensure all four options exist
        for letter in ['A', 'B', 'C', 'D']:
            if letter not in options:
                options[letter] = "Option not found"
        
        return options
