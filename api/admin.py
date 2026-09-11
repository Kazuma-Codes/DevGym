from django.contrib import admin
from .models import CandidateProfile, InterviewSession, InterviewTurn


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mode",
        "subject",
        "difficulty",
        "status",
        "question_number",
        "max_questions",
        "created_at",
    )
    list_filter = ("mode", "status", "difficulty", "subject")


@admin.register(InterviewTurn)
class InterviewTurnAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "score", "created_at")
    list_filter = ("score",)