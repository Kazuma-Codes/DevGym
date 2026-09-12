import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Session countdown that fires `onExpire` exactly once when time runs out.
 * `stopEarly` lets callers (e.g. the recorder) freeze the timer while audio
 * is being finalized.
 */
export function useCountdown(initialSeconds: number, onExpire: () => void) {
  const [timeLeft, setTimeLeft] = useState(initialSeconds);
  const expiredRef = useRef(false);
  const onExpireRef = useRef(onExpire);

  onExpireRef.current = onExpire;

  useEffect(() => {
    if (initialSeconds <= 0) return;
    setTimeLeft(initialSeconds);
    expiredRef.current = false;
  }, [initialSeconds]);

  useEffect(() => {
    if (initialSeconds <= 0 || expiredRef.current) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [initialSeconds]);

  useEffect(() => {
    if (initialSeconds > 0 && timeLeft === 0 && !expiredRef.current) {
      expiredRef.current = true;
      onExpireRef.current();
    }
  }, [timeLeft, initialSeconds]);

  const stopEarly = useCallback(() => {
    expiredRef.current = true;
  }, []);

  return { timeLeft, stopEarly };
}
