"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ScanFace, Loader2, ShieldCheck, Camera, AlertCircle, ArrowLeft, Lock } from "lucide-react";
import { useWebcam } from "@/lib/face/use-webcam";
import { captureFaceDescriptor, loadFaceModels } from "@/lib/face/face-api";
import {
  apiFaceStatus,
  apiFaceEnroll,
  apiFaceVerify,
} from "@/lib/api/auth";

type Phase = "loading" | "verify" | "enroll" | "success";

/**
 * FaceLock — the admin biometric-style gate.
 *
 * On mount it checks whether the admin has a face registered:
 *   • Registered  → "verify" mode: scan the camera, match against stored faces.
 *   • Not set up  → "enroll" mode: admin enters password, then scans to register.
 *
 * On a successful verify (or right after enrollment) it calls onUnlock().
 */
export function FaceLock({ onUnlock }: { onUnlock: () => void }) {
  const { videoRef, ready, error: camError, start, stop } = useWebcam();

  const [phase, setPhase] = useState<Phase>("loading");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [password, setPassword] = useState("");

  // 1. On mount: warm up the models and check enrollment status.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Kick off model loading in parallel with the status check.
        loadFaceModels().catch(() => {});
        const status = await apiFaceStatus();
        if (cancelled) return;
        setPhase(status.enrolled ? "verify" : "enroll");
      } catch {
        if (!cancelled) {
          // If status can't be read, default to enroll (safe: still password-gated).
          setPhase("enroll");
        }
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Start the camera whenever we're on a phase that needs it.
  useEffect(() => {
    if (phase === "verify" || phase === "enroll") {
      start();
    }
    return () => { if (phase === "success") stop(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  async function handleVerify() {
    if (!videoRef.current || busy) return;
    setBusy(true);
    setError("");
    setMsg("Scanning…");
    const cap = await captureFaceDescriptor(videoRef.current);
    if (!cap.ok) {
      setBusy(false);
      setMsg("");
      setError(cap.message);
      return;
    }
    try {
      await apiFaceVerify(cap.descriptor);
      setMsg("");
      setPhase("success");
      stop();
      setTimeout(onUnlock, 900);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Face not recognised. Access denied.");
      setMsg("");
    } finally {
      setBusy(false);
    }
  }

  async function handleEnroll() {
    if (!videoRef.current || busy) return;
    if (!password) { setError("Enter your admin password to set up Face Lock."); return; }
    setBusy(true);
    setError("");
    setMsg("Capturing your face…");
    const cap = await captureFaceDescriptor(videoRef.current);
    if (!cap.ok) {
      setBusy(false);
      setMsg("");
      setError(cap.message);
      return;
    }
    try {
      await apiFaceEnroll(password, cap.descriptor);
      setMsg("");
      setPassword("");
      setPhase("success");
      stop();
      setTimeout(onUnlock, 900);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not enable Face Lock.");
      setMsg("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0b0b0b] px-4">
      {/* brand-tinted glows */}
      <div
        className="pointer-events-none fixed inset-0 -z-10"
        style={{
          backgroundColor: "#08090c",
          backgroundImage:
            "radial-gradient(50% 45% at 50% 0%, rgba(0,200,83,0.10) 0%, rgba(0,200,83,0) 60%)," +
            "linear-gradient(180deg, #0d1117 0%, #08090c 100%)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md rounded-3xl border border-white/10 bg-[#141414]/80 p-8 backdrop-blur-sm shadow-2xl"
      >
        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-500/15 text-emerald-400">
            {phase === "success" ? <ShieldCheck className="h-6 w-6" /> : <ScanFace className="h-6 w-6" />}
          </div>
          <div>
            <h2 className="text-xl font-black uppercase tracking-tight text-white">
              {phase === "enroll" ? "Set Up Face Lock" : phase === "success" ? "Access Granted" : "Face Lock"}
            </h2>
            <p className="text-xs text-white/50">
              {phase === "loading" && "Preparing secure camera…"}
              {phase === "verify" && "Scan your face to enter the admin console."}
              {phase === "enroll" && "Register your face to secure the admin console."}
              {phase === "success" && "Welcome back, admin."}
            </p>
          </div>
        </div>

        {phase === "loading" && (
          <div className="flex h-56 items-center justify-center">
            <Loader2 className="h-7 w-7 animate-spin text-emerald-500" />
          </div>
        )}

        {(phase === "verify" || phase === "enroll" || phase === "success") && (
          <>
            {/* Camera preview */}
            <div className="relative mx-auto mb-5 aspect-square w-56 overflow-hidden rounded-2xl border border-white/10 bg-black">
              <video
                ref={videoRef}
                muted
                playsInline
                className="h-full w-full scale-x-[-1] object-cover"
              />
              {/* scan frame */}
              <div className="pointer-events-none absolute inset-0 rounded-2xl ring-2 ring-emerald-500/40" />
              {phase === "success" && (
                <div className="absolute inset-0 grid place-items-center bg-emerald-500/20 backdrop-blur-sm">
                  <ShieldCheck className="h-14 w-14 text-emerald-300" />
                </div>
              )}
              {!ready && phase !== "success" && (
                <div className="absolute inset-0 grid place-items-center text-white/40">
                  <Camera className="h-8 w-8" />
                </div>
              )}
            </div>

            {/* Camera error */}
            {camError && (
              <div className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-xs text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0" /> {camError}
              </div>
            )}

            {/* Enroll: password field */}
            {phase === "enroll" && (
              <div className="mb-4">
                <label className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-white/50">
                  <Lock className="h-3 w-3" /> Admin Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(""); }}
                  placeholder="Confirm your password to enable"
                  className="w-full rounded-lg border border-white/10 bg-[#0d0d0d] px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none transition-colors focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/40"
                />
              </div>
            )}

            {/* status / error */}
            {msg && !error && (
              <p className="mb-3 text-center text-xs text-emerald-400">{msg}</p>
            )}
            {error && (
              <div className="mb-3 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-xs text-red-300">
                {error}
              </div>
            )}

            {/* action button */}
            {phase !== "success" && (
              <button
                onClick={phase === "enroll" ? handleEnroll : handleVerify}
                disabled={busy || !ready}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 py-3.5 text-sm font-bold uppercase tracking-widest text-emerald-950 transition-all hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {busy ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Please wait…</>
                ) : phase === "enroll" ? (
                  <><ScanFace className="h-4 w-4" /> Register My Face</>
                ) : (
                  <><ScanFace className="h-4 w-4" /> Scan to Unlock</>
                )}
              </button>
            )}

            {/* privacy note (enroll only) */}
            {phase === "enroll" && (
              <p className="mt-4 text-center text-[11px] leading-relaxed text-white/40">
                Only a numeric face signature is stored — never a photo. After this,
                admin access requires your registered face.
              </p>
            )}
          </>
        )}

        {/* Back to app */}
        <a
          href="/"
          className="mt-6 flex items-center justify-center gap-1.5 text-xs text-white/40 transition-colors hover:text-white/70"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to app
        </a>
      </motion.div>
    </div>
  );
}
