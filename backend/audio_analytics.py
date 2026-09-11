import re


FILLER_PATTERNS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\blike\b",
    r"\bbasically\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\byou know\b",
    r"\bkind of\b",
    r"\bsort of\b",
]


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def analyze_voice_delivery(segments, total_duration_sec=0.0):
    """
    Analyzes speech delivery using Whisper segments.

    Returns:
        - WPM
        - filler word count
        - pause statistics
        - actionable delivery feedback
    """
    texts = []
    starts = []
    ends = []

    for segment in segments or []:
        text = str(_get(segment, "text", "")).strip()
        start = float(_get(segment, "start", 0.0) or 0.0)
        end = float(_get(segment, "end", 0.0) or 0.0)

        if text:
            texts.append(text)
            starts.append(start)
            ends.append(end)

    full_text = " ".join(texts).lower()

    words = re.findall(r"[a-z0-9']+", full_text)
    word_count = len(words)

    if total_duration_sec <= 0 and ends:
        total_duration_sec = max(ends)

    spoken_duration = 0.0
    for start, end in zip(starts, ends):
        if end > start:
            spoken_duration += end - start

    if spoken_duration <= 0:
        spoken_duration = total_duration_sec

    wpm = int(word_count / (spoken_duration / 60.0)) if spoken_duration > 0 else 0

    filler_count = 0
    for pattern in FILLER_PATTERNS:
        filler_count += len(re.findall(pattern, full_text))

    long_pauses = 0
    max_pause = 0.0

    for i in range(1, len(starts)):
        gap = starts[i] - ends[i - 1]
        if gap > 1.5:
            long_pauses += 1
            if gap > max_pause:
                max_pause = gap

    feedback = []

    if word_count == 0:
        feedback.append("No speech was detected.")
    else:
        if wpm > 160:
            feedback.append("You are speaking quite fast. Slow down slightly for clarity.")
        elif wpm < 90:
            feedback.append("Your pace is slow. Try to speak a little more continuously.")

        if filler_count > 3:
            feedback.append(
                f"You used around {filler_count} filler words. "
                "Replace filler sounds with short silent pauses."
            )

        if max_pause > 4.0:
            feedback.append(
                f"You had a long pause of about {round(max_pause, 1)} seconds. "
                "Use a bridging phrase like: 'Let me structure my answer...'."
            )

    if not feedback:
        feedback.append("Good pacing and fluency.")

    return {
        "wpm": wpm,
        "word_count": word_count,
        "filler_count": filler_count,
        "long_pauses": long_pauses,
        "max_pause_seconds": round(max_pause, 2),
        "speech_duration_seconds": round(spoken_duration, 2),
        "total_duration_seconds": round(total_duration_sec, 2),
        "feedback": " ".join(feedback),
    }