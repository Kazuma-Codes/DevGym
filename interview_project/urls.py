from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.http import HttpResponse

BASE_DIR = Path(__file__).resolve().parent.parent


def index_view(request):
    dist_index = BASE_DIR / "frontend-react" / "dist" / "index.html"
    if dist_index.exists():
        with open(dist_index, "r", encoding="utf-8") as f:
            return HttpResponse(f.read(), content_type="text/html")
    return HttpResponse(
        '<html><head><title>AI Interview Bot</title></head><body style="font-family:sans-serif;padding:2rem;">'
        '<h2>AI Voice Interview Platform Backend</h2>'
        '<p>The backend API is active on port 8000.</p>'
        '<p>To view the React application, open <a href="http://localhost:5173" target="_blank">http://localhost:5173</a> (when running <code>npm run dev</code> inside <code>frontend-react</code>).</p>'
        '</body></html>',
        content_type="text/html",
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", index_view, name="index"),
    re_path(
        r"^assets/(?P<path>.*)$",
        serve,
        {"document_root": BASE_DIR / "frontend-react" / "dist" / "assets"},
    ),
]