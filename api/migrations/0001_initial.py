# Generated clean initial migration for current models

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CandidateProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, max_length=200)),
                ("resume_text", models.TextField(blank=True)),
                ("resume_json", models.JSONField(blank=True, default=dict)),
                ("job_description", models.TextField(blank=True)),
                ("project_text", models.TextField(blank=True)),
                ("focus_areas", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="InterviewSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("SUBJECT", "Subject-Based"),
                            ("RESUME", "Resume Deep-Dive"),
                            ("PROJECT_GRILL", "Project Interrogator"),
                            ("RAPID_FIRE", "CS Fundamentals Flash-Fire"),
                            ("BEHAVIORAL", "STAR / Gap Defense"),
                            ("SYSTEM_DESIGN", "System Design / Production Debugging"),
                            ("JD_MATCH", "Job Description Alignment"),
                        ],
                        default="SUBJECT",
                        max_length=30,
                    ),
                ),
                ("subject", models.CharField(blank=True, default="OOP", max_length=80)),
                ("difficulty", models.CharField(default="easy", max_length=20)),
                ("status", models.CharField(default="active", max_length=20)),
                ("current_question", models.TextField(blank=True)),
                ("current_expected_concepts", models.JSONField(blank=True, default=list)),
                ("is_follow_up", models.BooleanField(default=False)),
                ("question_number", models.PositiveIntegerField(default=0)),
                ("max_questions", models.PositiveIntegerField(default=5)),
                ("time_limit_seconds", models.PositiveIntegerField(default=0)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "profile",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="api.candidateprofile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InterviewTurn",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("question_text", models.TextField()),
                ("answer_text", models.TextField(blank=True)),
                ("score", models.IntegerField(default=0)),
                ("feedback", models.TextField(blank=True)),
                ("missing_concepts", models.JSONField(blank=True, default=list)),
                ("voice", models.JSONField(blank=True, default=dict)),
                ("analytics", models.JSONField(blank=True, default=dict)),
                ("duration_seconds", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="turns",
                        to="api.interviewsession",
                    ),
                ),
            ],
        ),
    ]
