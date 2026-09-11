import json
import uuid
from typing import Any, Dict, Optional, Tuple
import random # making the question random
from config import QUESTION_BANK_PATH


class SessionManager:
    """Manages quiz sessions and provides access to the normalized question bank."""

    def __init__(self):
        # In-memory store for active sessions, keyed by session_id
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # Load and normalize questions once at startup to avoid repeated I/O and formatting issues
        self.question_bank = self._load_question_bank()

    def _load_question_bank(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the question bank from disk and normalizes all subject/difficulty keys.
        
        Normalization (strip + lowercase) ensures consistent lookups regardless of 
        casing or trailing whitespace in the source JSON file.
        """
        with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
            raw_bank = json.load(f)

        normalized_bank: Dict[str, Dict[str, Any]] = {}

        for subject, difficulties in raw_bank.items():
            # Normalize subject key to prevent mismatches like "Math" vs "math"
            subject_key = subject.strip().lower()
            normalized_bank[subject_key] = {}

            for difficulty, questions in difficulties.items():
                # Normalize difficulty key for the same consistency guarantee
                difficulty_key = difficulty.strip().lower()
                normalized_bank[subject_key][difficulty_key] = questions

        return normalized_bank

    def create_session(self, subject: str, difficulty: str) -> Tuple[str, str]:
        """
        Creates a new quiz session and returns the session ID with the first question.
        
        Args:
            subject: The quiz subject (case-insensitive).
            difficulty: The difficulty level (case-insensitive).
            
        Returns:
            A tuple of (session_id, first_question_text).
            
        Raises:
            ValueError: If the subject, difficulty, or question set is invalid/empty.
        """
        subject_key = subject.strip().lower()
        difficulty_key = difficulty.strip().lower()

        # Validate that the requested subject exists in the normalized bank
        if subject_key not in self.question_bank:
            raise ValueError("Subject not supported yet")

        # Validate that the requested difficulty exists for this subject
        if difficulty_key not in self.question_bank[subject_key]:
            raise ValueError("Difficulty not supported")

        questions = self.question_bank[subject_key][difficulty_key]

        # Guard against empty question lists which would cause IndexError later
        if not questions:
            raise ValueError("No questions available for this subject and difficulty")

        # Create a randomized copy of the question list for this session
        shuffled_questions = random.sample(questions, len(questions))


        session_id = str(uuid.uuid4())

        # Initialize session state; history tracks Q&A pairs for post-session review
        self.sessions[session_id] = {
            "session_id": session_id,
            "subject": subject_key,
            "difficulty": difficulty_key,
            "question_index": 0,       # Tracks progress through the question list
            "finished": False,          # Flag to indicate all questions have been answered
            "history": [],               # Accumulates answers, scores, and feedback
            "questions": shuffled_questions,
            "is_follow_up": False,      # True when the current question is a follow-up
            "current_follow_up_question": None  # The LLM-generated follow-up question text
        }

        return session_id, shuffled_questions[0]["question"]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a session by ID, returning None if it doesn't exist."""
        return self.sessions.get(session_id)

    def get_current_question(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns the full question object for the session's current index.
        
        Raises:
            ValueError: If the session has already progressed past all questions.
        """
        # subject = session["subject"]
        # difficulty = session["difficulty"]
        index = session["question_index"]
        # Use the randomized question list stored in the session
        questions = session.get("questions")
            # Fallback for older sessions created before randomization was added
        if not questions:
            subject = session["subject"]
            difficulty = session["difficulty"]
            questions = self.question_bank[subject][difficulty]
        # Safety check: index should never exceed bounds during normal flow,
        # but guard against stale/corrupted session state
        if index >= len(questions):
            raise ValueError("No current question available")

        return questions[index]

    def advance_question(self, session: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Moves the session to the next question.
        
        Returns:
            A tuple of (next_question_text_or_completion_message, is_finished).
        """
        # subject = session["subject"]
        # difficulty = session["difficulty"]
        # questions = self.question_bank[subject][difficulty]

        questions = session.get("questions")

        if not questions:
            subject = session["subject"]
            difficulty = session["difficulty"]
            questions = self.question_bank[subject][difficulty]

        next_index = session["question_index"] + 1
        
        if next_index < len(questions):
            # Advance to next question and signal that the session continues
            session["question_index"] = next_index
            return questions[next_index]["question"], False
            # Fallback for older sessions created before randomization was added

        # No more questions remaining; mark session as complete
        session["finished"] = True
        return "That was the last question in this set.", True

    def add_history(
        self,
        session: Dict[str, Any],
        question: str,
        answer: str,
        evaluation: Dict[str, Any],
        is_follow_up: bool = False
    ):
        """
        Records a completed Q&A pair with AI evaluation results into session history.
        
        Args:
            session: The active session dict (mutated in place).
            question: The question text that was answered.
            answer: The user's submitted answer.
            evaluation: Dict containing 'feedback', 'score', and 'missing_concepts'.
            is_follow_up: Whether this was a follow-up question.
        """
        session["history"].append(
            {
                "question": question,
                "answer": answer,
                "is_follow_up": is_follow_up,
                # Use .get() with defaults to gracefully handle partial evaluations
                "feedback": evaluation.get("feedback", ""),
                "score": evaluation.get("score", 0),
                "missing_concepts": evaluation.get("missing_concepts", [])
            }
        )


# Module-level singleton instance shared across the application
manager = SessionManager()