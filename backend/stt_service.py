import os
import tempfile

from faster_whisper import WhisperModel

from config import (
    WHISPER_MODEL_SIZE,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
)

_whisper_model = None


def get_whisper_model():
    global _whisper_model

    if _whisper_model is None:
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )

    return _whisper_model


def transcribe_bytes_detailed(
    audio_bytes: bytes,
    suffix: str = ".webm",
    initial_prompt: str = None,
):
    """
    Returns:
        transcript, segments, duration_seconds
    """
    if not audio_bytes:
        return "", [], 0.0

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()

        segments, info = model.transcribe(
            tmp_path,
            language="en",
            vad_filter=True,
            initial_prompt=initial_prompt,
        )

        segment_list = []
        text_parts = []

        for segment in segments:
            text = str(segment.text or "").strip()
            if not text:
                continue

            text_parts.append(text)
            segment_list.append({
                "text": text,
                "start": float(segment.start or 0.0),
                "end": float(segment.end or 0.0),
            })

        duration = 0.0

        if info and getattr(info, "duration", None):
            duration = float(info.duration)
        elif segment_list:
            duration = float(segment_list[-1]["end"])

        transcript = " ".join(text_parts).strip()

        return transcript, segment_list, duration

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def transcribe_bytes(
    audio_bytes: bytes,
    suffix: str = ".webm",
    initial_prompt: str = None,
) -> str:
    """
    Backward-compatible helper.
    """
    transcript, _, _ = transcribe_bytes_detailed(
        audio_bytes,
        suffix,
        initial_prompt,
    )
    return transcript