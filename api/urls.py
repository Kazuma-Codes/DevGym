from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health, name="health"),

    path("profile", views.create_profile, name="create-profile"),

    path("start", views.start_interview, name="start-interview"),
    path("answer/<uuid:session_id>", views.submit_answer, name="submit-answer"),

    path(
        "session/<uuid:session_id>/finish",
        views.finish_session,
        name="finish-session",
    ),
    path(
        "session/<uuid:session_id>/summary",
        views.session_summary,
        name="session-summary",
    ),

    path("tts/status", views.tts_status, name="tts-status"),
    path("tts", views.text_to_speech, name="tts"),
    path("tts/answer", views.speak_answer_feedback, name="tts-answer"),
]