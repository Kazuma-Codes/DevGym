from io import BytesIO

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from llm.llm_service import parse_resume


def extract_text_from_upload(file_obj) -> str:
    """
    Extracts text from an uploaded file.
    Supports:
        - PDF
        - TXT
    """
    if not file_obj:
        return ""

    name = str(getattr(file_obj, "name", "")).lower()
    content_type = str(getattr(file_obj, "content_type", "")).lower()

    try:
        if name.endswith(".pdf") or content_type == "application/pdf":
            if not pdfplumber:
                return ""
            file_bytes = file_obj.read()
            texts = []

            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text:
                        texts.append(page_text)

            return "\n".join(texts).strip()

        file_bytes = file_obj.read()
        return file_bytes.decode("utf-8", errors="ignore")

    except Exception:
        return ""


def parse_resume_text(resume_text: str, job_description: str = "") -> dict:
    """
    Parses resume text into structured JSON using the LLM.
    """
    if not resume_text or not resume_text.strip():
        return {}

    return parse_resume(resume_text, job_description)