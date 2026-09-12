"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * useWebcam — manages a getUserMedia camera stream bound to a <video> element.
 * Returns a ref to attach to the <video>, ready/error state, and controls.
 */
export function useWebcam() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setReady(false);
  }, []);

  const start = useCallback(async () => {
    setError(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera not supported in this browser.");
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 480 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setReady(true);
    } catch (err) {
      const msg =
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Camera permission denied. Allow camera access to use Face Lock."
          : err instanceof Error
            ? err.message
            : "Could not start the camera.";
      setError(msg);
      setReady(false);
    }
  }, []);

  // Clean up the stream on unmount.
  useEffect(() => () => stop(), [stop]);

  return { videoRef, ready, error, start, stop };
}
