import json
import random

from config import QUESTION_BANK_PATH


class QuestionBank:
    def __init__(self):
        self.bank = self._load()

    def _load(self):
        try:
            with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
                raw_bank = json.load(f)
        except Exception:
            return {}

        normalized = {}

        for subject, difficulties in raw_bank.items():
            subject_key = str(subject).strip().lower()
            normalized[subject_key] = {}

            for difficulty, questions in difficulties.items():
                difficulty_key = str(difficulty).strip().lower()
                normalized[subject_key][difficulty_key] = []

                for index, question in enumerate(questions):
                    if not isinstance(question, dict):
                        continue

                    normalized[subject_key][difficulty_key].append({
                        "id": str(question.get("id") or f"{subject_key}-{difficulty_key}-{index}"),
                        "question": str(question.get("question", "")).strip(),
                        "expected_concepts": [
                            str(concept).strip()
                            for concept in question.get("expected_concepts", [])
                            if str(concept).strip()
                        ],
                    })

        return normalized

    def has(self, subject, difficulty):
        subject_key = subject.strip().lower()
        difficulty_key = difficulty.strip().lower()
        return bool(self.bank.get(subject_key, {}).get(difficulty_key))

    def random_question(self, subject, difficulty, exclude_ids=None):
        subject_key = subject.strip().lower()
        difficulty_key = difficulty.strip().lower()
        exclude_ids = set(exclude_ids or [])

        questions = self.bank.get(subject_key, {}).get(difficulty_key, [])
        valid_questions = [q for q in questions if q["id"] not in exclude_ids]

        if not valid_questions:
            for diff in ["easy", "medium", "hard"]:
                alt_questions = self.bank.get(subject_key, {}).get(diff, [])
                alt_valid = [q for q in alt_questions if q["id"] not in exclude_ids]
                if alt_valid:
                    valid_questions = alt_valid
                    break

        if not valid_questions and questions:
            valid_questions = questions

        if not valid_questions:
            return None

        return random.choice(valid_questions)

    def random_rapid_question(self, exclude_ids=None):
        subjects = ["oop", "os", "dbms", "cn", "dsa"]
        difficulties = ["easy", "medium", "hard"]
        exclude_ids = set(exclude_ids or [])

        candidates = []

        for subject in subjects:
            for difficulty in difficulties:
                questions = self.bank.get(subject, {}).get(difficulty, [])
                candidates.extend(questions)

        valid_candidates = [q for q in candidates if q["id"] not in exclude_ids]

        if not valid_candidates and candidates:
            valid_candidates = candidates

        if not valid_candidates:
            return None

        return random.choice(valid_candidates)


bank = QuestionBank()