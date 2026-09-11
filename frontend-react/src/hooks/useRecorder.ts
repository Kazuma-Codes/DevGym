import { useRef, useState } from "react";

export function useRecorder() {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const resolveRef = useRef<((blob: Blob | null) => void) | null>(null);

  const start = async () => {
    setError("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      streamRef.current = stream;

      const candidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
      ];

      let options: MediaRecorderOptions = {};

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

        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        setRecording(false);

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
      setError("Microphone access failed. Please allow microphone permission.");
      setRecording(false);

      if (resolveRef.current) {
        resolveRef.current(null);
        resolveRef.current = null;
      }
    }
  };

  const stop = (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;

      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }

      resolveRef.current = resolve;
      recorder.stop();
    });
  };

  return {
    recording,
    error,
    start,
    stop,
  };
}