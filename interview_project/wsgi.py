"""
WSGI config for the AI Interview Platform.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "interview_project.settings")

application = get_wsgi_application()