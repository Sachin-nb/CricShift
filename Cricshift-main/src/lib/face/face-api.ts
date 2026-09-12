/**
 * face-api helper — loads the recognition models once and computes a 128-float
 * face descriptor from a live <video> element.
 *
 * Models are fetched from a public CDN (weights only; no external calls at
 * inference time — everything runs in-browser). We store/compare only the
 * numeric descriptor, never an image.
 *
 * Uses @vladmandic/face-api (a maintained fork of face-api.js).
 */

// NOTE: We must NOT statically `import` @vladmandic/face-api at the top level.
// The package (and its TensorFlow.js dependency) runs browser-only code at
// module-evaluation time. Next.js evaluates client-component modules on the
// server during SSR/prerender, where that code crashes with
// "this.util.TextEncoder is not a constructor". So we lazily import it only in
// the browser, inside the functions that actually need it.
type FaceApi = typeof import("@vladmandic/face-api");

// Pre-hosted model weights (TinyFaceDetector + landmarks + recognition).
const MODEL_URL =
  "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model";

let _faceapi: FaceApi | null = null;
let _faceapiPromise: Promise<FaceApi> | null = null;
let _modelsLoaded = false;
let _loadingPromise: Promise<void> | null = null;

/** Dynamically import the face-api module (browser only, once). */
async function getFaceApi(): Promise<FaceApi> {
  if (typeof window === "undefined") {
    throw new Error("Face recognition is only available in the browser.");
  }
  if (_faceapi) return _faceapi;
  if (!_faceapiPromise) {
    _faceapiPromise = import("@vladmandic/face-api").then((mod) => {
      _faceapi = mod;
      return mod;
    });
  }
  return _faceapiPromise;
}

/** Load the required models once (idempotent). */
export async function loadFaceModels(): Promise<void> {
  if (_modelsLoaded) return;
  if (_loadingPromise) return _loadingPromise;

  _loadingPromise = (async () => {
    const faceapi = await getFaceApi();
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    _modelsLoaded = true;
  })();

  return _loadingPromise;
}

export type CaptureResult =
  | { ok: true; descriptor: number[] }
  | { ok: false; reason: "no-face" | "multiple-faces" | "error"; message: string };

/**
 * Detect a single face in the given video element and return its 128-float
 * descriptor. Returns a structured result so the UI can guide the user.
 */
export async function captureFaceDescriptor(
  video: HTMLVideoElement,
): Promise<CaptureResult> {
  try {
    const faceapi = await getFaceApi();
    await loadFaceModels();

    const detections = await faceapi
      .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 }))
      .withFaceLandmarks()
      .withFaceDescriptors();

    if (detections.length === 0) {
      return { ok: false, reason: "no-face", message: "No face detected. Center your face in the frame." };
    }
    if (detections.length > 1) {
      return { ok: false, reason: "multiple-faces", message: "Multiple faces detected. Only you should be in frame." };
    }

    const descriptor = Array.from(detections[0].descriptor as Float32Array);
    return { ok: true, descriptor };
  } catch (err) {
    return {
      ok: false,
      reason: "error",
      message: err instanceof Error ? err.message : "Face scan failed. Please try again.",
    };
  }
}
