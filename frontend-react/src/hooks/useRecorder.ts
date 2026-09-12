import { useCallback, useEffect, useRef, useState } from "react";

function describeMicError(err: unknown): string {
  if (err instanceof DOMException) {
    switch (err.name) {
      case "NotAllowedError":
        return "Microphone permission was denied. Allow mic access in your browser settings and try again.";
      case "NotFoundError":
        return "No microphone was found. Connect a microphone and try again.";
      case "NotReadableError":
        return "Your microphone is busy or blocked by another app. Close other apps using it and retry.";
      case "OverconstrainedError":
        return "The selected microphone is not supported in this browser.";
      default:
        break;
    }
  }

  if (typeof navigator !== "undefined" && !navigator.mediaDevices?.getUserMedia) {
    return "Voice recording requires HTTPS (or localhost) in this browser.";
  }

  return "Microphone access failed. Please allow microphone permission.";
}

export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const resolveRef = useRef<((blob: Blob | null) => void) | null>(null);

  const release = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    setRecording(false);
  }, []);

  // Stop the mic and finalize any pending recording when the component unmounts.
  useEffect(() => {
    return () => {
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      if (resolveRef.current) {
        resolveRef.current(null);
        resolveRef.current = null;
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  const start = useCallback(async () => {
    setError("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Voice recording requires HTTPS (or localhost) in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      streamRef.current = stream;

      const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];

      const options: MediaRecorderOptions = {};

      for (const mimeType of candidates) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          options.mimeType = mimeType;
          break;
        }
      }

      const recorder = new MediaRecorder(stream, options);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        release();

        if (resolveRef.current) {
          resolveRef.current(blob);
          resolveRef.current = null;
        }
      };

      recorder.start();

      mediaRecorderRef.current = recorder;
      setRecording(true);
    } catch (err) {
      console.error(err);
      setError(describeMicError(err));
      release();

      if (resolveRef.current) {
        resolveRef.current(null);
        resolveRef.current = null;
      }
    }
  }, [release]);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;

      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }

      resolveRef.current = resolve;
      recorder.stop();
    });
  }, []);

  return {
    recording,
    error,
    start,
    stop,
    /** Silently release the microphone without resolving a blob. */
    release,
  };
}
