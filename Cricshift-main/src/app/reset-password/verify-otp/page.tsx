"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell, AuthButton, AuthMessage, BackToLogin } from "@/components/auth/auth-shell";
import { StepDots, RESET_EMAIL_KEY, RESET_TOKEN_KEY } from "../page";
import { apiSendOtp, apiVerifyOtp } from "@/lib/api/auth";

const OTP_LENGTH = 6;

export default function VerifyOtpPage() {
  const router = useRouter();
  const [email, setEmail]     = useState("");
  const [digits, setDigits]   = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [info, setInfo]       = useState("");
  const [resendIn, setResendIn] = useState(30);
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);

  // Guard: must have an email from step 1
  useEffect(() => {
    const e = sessionStorage.getItem(RESET_EMAIL_KEY);
    if (!e) {
      router.replace("/reset-password");
      return;
    }
    setEmail(e);
    inputsRef.current[0]?.focus();
  }, [router]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendIn <= 0) return;
    const t = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [resendIn]);

  function handleChange(idx: number, val: string) {
    // Only accept a single digit
    const d = val.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[idx] = d;
    setDigits(next);
    if (d && idx < OTP_LENGTH - 1) {
      inputsRef.current[idx + 1]?.focus();
    }
  }

  function handleKeyDown(idx: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[idx] && idx > 0) {
      inputsRef.current[idx - 1]?.focus();
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (!pasted) return;
    const next = Array(OTP_LENGTH).fill("");
    for (let i = 0; i < pasted.length; i++) next[i] = pasted[i];
    setDigits(next);
    inputsRef.current[Math.min(pasted.length, OTP_LENGTH - 1)]?.focus();
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const code = digits.join("");
    if (code.length !== OTP_LENGTH) {
      setError(`Please enter all ${OTP_LENGTH} digits.`);
      return;
    }
    setLoading(true);
    try {
      const { reset_token } = await apiVerifyOtp(email, code);
      // Persist the reset token for step 3
      sessionStorage.setItem(RESET_TOKEN_KEY, reset_token);
      router.push("/reset-password/new-password");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid code. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (resendIn > 0) return;
    setError("");
    setInfo("");
    try {
      await apiSendOtp(email);
      setResendIn(30);
      setDigits(Array(OTP_LENGTH).fill(""));
      inputsRef.current[0]?.focus();
      setInfo("A new verification code has been sent to your email.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend the code.");
    }
  }

  return (
    <AuthShell
      eyebrow="CricShift Reset Initiative"
      headlineTop="Every Champion Gets"
      headlineBottom="A Second Chance."
      subtext="Back to the crease. Secure your profile, reset your credentials, and jump straight back into the match-day action."
    >
      <h2 className="text-2xl font-black uppercase tracking-tight">OTP Verification</h2>
      <p className="mb-6 mt-1 text-sm text-white/50">
        Enter the 6-digit code sent to{" "}
        <span className="font-semibold text-white/80">{email || "your email"}</span>.
      </p>

      <StepDots active={2} />

      <AuthMessage type="error" text={error} />
      <AuthMessage type="success" text={info} />

      <form onSubmit={handleVerify}>
        <div className="mb-2 flex items-center justify-between">
          <label className="text-[11px] font-bold uppercase tracking-widest text-white/50">
            OTP Verification
          </label>
          <button
            type="button"
            onClick={handleResend}
            disabled={resendIn > 0}
            className="text-xs font-bold text-[#c8f000] hover:underline disabled:cursor-not-allowed disabled:text-white/30 disabled:no-underline"
          >
            {resendIn > 0 ? `Resend OTP (${resendIn}s)` : "Resend OTP"}
          </button>
        </div>

        <div className="mb-6 flex gap-3" onPaste={handlePaste}>
          {digits.map((d, i) => (
            <input
              key={i}
              ref={(el) => { inputsRef.current[i] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={d}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className={
                "h-14 w-full rounded-xl border bg-black/40 text-center text-xl font-bold text-white outline-none transition-all " +
                (d
                  ? "border-[#c8f000] ring-2 ring-[#c8f000]/30"
                  : "border-white/10 focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30")
              }
            />
          ))}
        </div>

        <AuthButton type="submit" loading={loading}>Verify Code</AuthButton>
      </form>

      <BackToLogin />
    </AuthShell>
  );
}
