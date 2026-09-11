import os
import re
import wave
import tempfile
import threading

from typing import Optional

from config import (
    TTS_ENGINE,
    KOKORO_VOICE,
    PIPER_MODEL_PATH,
    MAX_TTS_CHARS,
)

_kokoro_pipeline = None
_kokoro_lock = threading.Lock()

_piper_voice = None
_piper_lock = threading.Lock()

_active_engine_cache = None


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_TTS_CHARS:
        text = text[:MAX_TTS_CHARS].strip()

    return text


def _kokoro_available() -> bool:
    try:
        import pykokoro  # noqa: F401
        return True
    except Exception:
        return False


def _piper_available() -> bool:
    try:
        from piper.voice import PiperVoice  # noqa: F401
        return bool(PIPER_MODEL_PATH and os.path.exists(PIPER_MODEL_PATH))
    except Exception:
        return False


def get_active_engine(force: bool = False) -> str:
    global _active_engine_cache

    if _active_engine_cache is not None and not force:
        return _active_engine_cache

    if TTS_ENGINE == "none":
        _active_engine_cache = "none"

    elif TTS_ENGINE == "kokoro":
        _active_engine_cache = "kokoro" if _kokoro_available() else "none"

    elif TTS_ENGINE == "piper":
        _active_engine_cache = "piper" if _piper_available() else "none"

    else:
        if _kokoro_available():
            _active_engine_cache = "kokoro"
        elif _piper_available():
            _active_engine_cache = "piper"
        else:
            _active_engine_cache = "none"

    return _active_engine_cache


def get_tts_status() -> dict:
    engine = get_active_engine()

    return {
        "engine": engine,
        "configured": engine != "none",
        "selected_env_engine": TTS_ENGINE,
        "kokoro_voice": KOKORO_VOICE,
        "piper_model_path": PIPER_MODEL_PATH,
        "supported_engines": ["kokoro", "piper"],
    }


def _synthesize_with_kokoro(text: str) -> Optional[bytes]:
    global _kokoro_pipeline

    try:
        with _kokoro_lock:
            if _kokoro_pipeline is None:
                from pykokoro import KokoroPipeline, PipelineConfig

                _kokoro_pipeline = KokoroPipeline(
                    PipelineConfig(
                        voice=KOKORO_VOICE
                    )
                )

            result = _kokoro_pipeline.run(text)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result.save_wav(tmp_path)

            with open(tmp_path, "rb") as f:
                return f.read()

        finally:
            try:
                if hasattr(result, "release_audio"):
                    result.release_audio()
            except Exception:
                pass

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception:
        return None


def _synthesize_with_piper(text: str) -> Optional[bytes]:
    global _piper_voice

    try:
        with _piper_lock:
            if _piper_voice is None:
                from piper.voice import PiperVoice

                if not PIPER_MODEL_PATH:
                    return None

                if not os.path.exists(PIPER_MODEL_PATH):
                    return None

                _piper_voice = PiperVoice.load(PIPER_MODEL_PATH)

            voice = _piper_voice

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with wave.open(tmp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(voice.config.sample_rate)
                voice.synthesize(text, wav_file)

            with open(tmp_path, "rb") as f:
                return f.read()

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception:
        return None


def synthesize_text(text: str) -> Optional[bytes]:
    text = clean_text(text)

    if not text:
        return None

    engine = get_active_engine()

    if engine == "kokoro":
        audio = _synthesize_with_kokoro(text)
        if audio:
            return audio

        if _piper_available():
            return _synthesize_with_piper(text)

        return None

    if engine == "piper":
        return _synthesize_with_piper(text)

    return None


def synthesize_feedback_and_next_question(
    feedback: str,
    score=None,
    next_question: Optional[str] = None,
) -> Optional[bytes]:
    parts = []

    if feedback:
        parts.append(feedback.strip())

    if score is not None:
        parts.append(f"Your score is {score} out of 5.")

    if next_question:
        parts.append(f"Next question: {next_question.strip()}")

    if not parts:
        return None

    spoken_text = " ".join(parts)
    return synthesize_text(spoken_text)