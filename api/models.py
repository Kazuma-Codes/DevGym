import uuid
from django.db import models


MODE_CHOICES = [
    ("SUBJECT", "Subject-Based"),
    ("RESUME", "Resume Deep-Dive"),
    ("PROJECT_GRILL", "Project Interrogator"),
    ("RAPID_FIRE", "CS Fundamentals Flash-Fire"),
    ("BEHAVIORAL", "STAR / Gap Defense"),
    ("SYSTEM_DESIGN", "System Design / Production Debugging"),
    ("JD_MATCH", "Job Description Alignment"),
]


class CandidateProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True)

    resume_text = models.TextField(blank=True)
    resume_json = models.JSONField(default=dict, blank=True)

    job_description = models.TextField(blank=True)
    project_text = models.TextField(blank=True)
    focus_areas = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Candidate'} - {str(self.id)[:8]}"


class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sessions",
    )

    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default="SUBJECT")
    subject = models.CharField(max_length=80, blank=True, default="OOP")
    difficulty = models.CharField(max_length=20, default="easy")

    status = models.CharField(max_length=20, default="active")

    current_question = models.TextField(blank=True)
    current_expected_concepts = models.JSONField(default=list, blank=True)

    is_follow_up = models.BooleanField(default=False)

    question_number = models.PositiveIntegerField(default=0)
    max_questions = models.PositiveIntegerField(default=5)

    time_limit_seconds = models.PositiveIntegerField(default=0)

    config = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.mode} session {str(self.id)[:8]}"


class InterviewTurn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="turns",
    )

    question_text = models.TextField()
    answer_text = models.TextField(blank=True)

    score = models.IntegerField(default=0)
    feedback = models.TextField(blank=True)
    missing_concepts = models.JSONField(default=list, blank=True)

    voice = models.JSONField(default=dict, blank=True)
    analytics = models.JSONField(default=dict, blank=True)

    duration_seconds = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Turn {str(self.id)[:8]} - score {self.score}"