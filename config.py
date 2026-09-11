from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# .parent goes one directory up
ROOT_DIR = Path(__file__).resolve().parent

# makes this proejct root directory
QUESTION_BANK_PATH = ROOT_DIR / "backend" / "question_bank.json"

# points to the frontend directory
FRONTEND_DIR = ROOT_DIR / "frontend-react" 

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))

# Whisper settings
"""
"small" - 500MB, balanced (RECOMMENDED)
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

"medium" - 1.5GB, more accurate
whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
"""
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# Text-to-Speech settings
TTS_ENGINE = os.getenv("TTS_ENGINE", "auto").lower()
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_sarah")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "")
MAX_TTS_CHARS = int(os.getenv("MAX_TTS_CHARS", "1200"))