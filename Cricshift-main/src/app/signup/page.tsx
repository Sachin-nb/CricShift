"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, ShieldCheck, Trophy, MailCheck } from "lucide-react";
import { AuthShell, AuthInput, AuthButton, AuthMessage } from "@/components/auth/auth-shell";
import { SocialButtons } from "@/components/auth/social-buttons";
import {
  apiRegisterSendOtp,
  apiRegisterVerifyOtp,
  markSplashPending,
} from "@/lib/api/auth";
import { useAuth } from "@/context/auth-context";

const OTP_LENGTH = 6;

export default function SignupPage() {
  const router = useRouter();
  const { setSession } = useAuth();

  // Which step we're on: fill the form, or verify the emailed code.
  const [step, setStep] = useState<"form" | "otp">("form");

  // ── Form fields ──
  const [name, setName]       = useState("");
  const [email, setEmail]     = useState("");
  const [mobile, setMobile]   = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [showCf, setShowCf]     = useState(false);
  const [agree, setAgree]       = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [info, setInfo]         = useState("");

  // ── OTP step state ──
  const [pendingToken, setPendingToken] = useState("");
  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [resendIn, setResendIn] = useState(0);
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendIn <= 0) return;
    const t = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [resendIn]);

  // ── Step 1: validate + send the code ──
  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setInfo("");

    if (password !== confirm) return setError("Passwords do not match.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (!agree) return setError("You must agree to the Terms of Service and Privacy Policy.");

    setLoading(true);
    try {
      const { pending_token } = await apiRegisterSendOtp({
        name,
        email: email.trim().toLowerCase(),
        password,
        mobile: mobile.trim() || undefined,
      });
      setPendingToken(pending_token);
      setStep("otp");
      setResendIn(30);
      setDigits(Array(OTP_LENGTH).fill(""));
      setInfo("We've emailed you a 6-digit verification code.");
      setTimeout(() => inputsRef.current[0]?.focus(), 50);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start signup. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2: verify the code + create the account ──
  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const code = digits.join("");
    if (code.length !== OTP_LENGTH) return setError(`Please enter all ${OTP_LENGTH} digits.`);

    setLoading(true);
    try {
      const { token, user } = await apiRegisterVerifyOtp(pendingToken, code);
      setSession(token, user, true);
      markSplashPending();
      router.push("/"); // land on the home page after signup
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (resendIn > 0) return;
    setError("");
    setInfo("");
    try {
      const { pending_token } = await apiRegisterSendOtp({
        name,
        email: email.trim().toLowerCase(),
        password,
        mobile: mobile.trim() || undefined,
      });
      setPendingToken(pending_token);
      setResendIn(30);
      setDigits(Array(OTP_LENGTH).fill(""));
      inputsRef.current[0]?.focus();
      setInfo("A new verification code has been sent to your email.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend the code.");
    }
  }

  // ── OTP box input handlers ──
  function handleDigit(idx: number, val: string) {
    const d = val.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[idx] = d;
    setDigits(next);
    if (d && idx < OTP_LENGTH - 1) inputsRef.current[idx + 1]?.focus();
  }
  function handleKeyDown(idx: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[idx] && idx > 0) inputsRef.current[idx - 1]?.focus();
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

  return (
    <AuthShell
      eyebrow="Join the Largest Cricket Platform"
      headlineTop="Play Your Best"
      headlineBottom="Innings."
      subtext="Create your profile today. Draft your fantasy squad, earn exclusive team badges, and stream premium coverage live in 4K."
      footerSlot={
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm text-white/80">
            <ShieldCheck className="h-4 w-4 text-[#00c853]" /> Verified Match Rankings
          </div>
          <div className="flex items-center gap-2 text-sm text-white/80">
            <Trophy className="h-4 w-4 text-[#00c853]" /> Daily Fantasy Cash Prizes
          </div>
        </div>
      }
    >
      {step === "form" ? (
        <>
          <h2 className="text-2xl font-black uppercase tracking-tight">Join the Squad</h2>
          <p className="mb-6 mt-1 text-sm text-white/50">Set up your account to start playing.</p>

          <AuthMessage type="error" text={error} />

          <form onSubmit={handleSendOtp}>
            <AuthInput
              label="Full Name"
              type="text"
              required
              placeholder="e.g. Katty Smith"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <AuthInput
              label="Email Address"
              type="email"
              required
              autoComplete="email"
              placeholder="Enter email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <AuthInput
              label="Mobile Number (for password recovery)"
              type="tel"
              placeholder="+91 98765 43210"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
            />

            {/* Password */}
            <div className="mb-4">
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  placeholder="Create secure password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 pr-11 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#00c853] focus:bg-black/60 focus:ring-2 focus:ring-[#00c853]/30"
                />
                <button type="button" onClick={() => setShowPw((s) => !s)} tabIndex={-1}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                  {showPw ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                </button>
              </div>
            </div>

            {/* Confirm password */}
            <div className="mb-4">
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showCf ? "text" : "password"}
                  required
                  placeholder="Re-enter password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 pr-11 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#00c853] focus:bg-black/60 focus:ring-2 focus:ring-[#00c853]/30"
                />
                <button type="button" onClick={() => setShowCf((s) => !s)} tabIndex={-1}
                  aria-label={showCf ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                  {showCf ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                </button>
              </div>
            </div>

            <label className="mb-5 flex cursor-pointer items-start gap-2 text-xs text-white/70">
              <input
                type="checkbox"
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                className="mt-0.5 h-4 w-4 accent-[#00c853]"
              />
              <span>
                I agree to the{" "}
                <span className="font-bold text-[#00c853]">Terms of Service</span> and{" "}
                <span className="font-bold text-[#00c853]">Privacy Policy</span>
              </span>
            </label>

            <AuthButton type="submit" loading={loading}>Continue</AuthButton>
          </form>

          <div className="my-5 flex items-center gap-3 text-[10px] uppercase tracking-widest text-white/30">
            <span className="h-px flex-1 bg-white/10" />
            Or signup with
            <span className="h-px flex-1 bg-white/10" />
          </div>

          <SocialButtons
            onSuccess={(token, user) => {
              setSession(token, user, true);
              markSplashPending();
              router.push("/");
            }}
            onError={(msg) => setError(msg)}
          />

          <p className="mt-6 text-center text-xs text-white/50">
            Already have an account?{" "}
            <Link href="/login" className="font-bold text-[#00c853] hover:underline">
              Log In
            </Link>
          </p>
        </>
      ) : (
        <>
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#00c853]/15 text-[#00c853]">
              <MailCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-tight">Verify your email</h2>
              <p className="text-xs text-white/50">
                Enter the 6-digit code sent to{" "}
                <span className="font-semibold text-white/80">{email}</span>
              </p>
            </div>
          </div>

          <AuthMessage type="error" text={error} />
          <AuthMessage type="success" text={info} />

          <form onSubmit={handleVerify}>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-[11px] font-bold uppercase tracking-widest text-white/50">
                Verification Code
              </label>
              <button
                type="button"
                onClick={handleResend}
                disabled={resendIn > 0}
                className="text-xs font-bold text-[#00c853] hover:underline disabled:cursor-not-allowed disabled:text-white/30 disabled:no-underline"
              >
                {resendIn > 0 ? `Resend (${resendIn}s)` : "Resend code"}
              </button>
            </div>

            <div className="mb-6 flex gap-2 sm:gap-3" onPaste={handlePaste}>
              {digits.map((d, i) => (
                <input
                  key={i}
                  ref={(el) => { inputsRef.current[i] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={d}
                  onChange={(e) => handleDigit(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className={
                    "h-14 w-full rounded-xl border bg-black/40 text-center text-xl font-bold text-white outline-none transition-all " +
                    (d
                      ? "border-[#00c853] ring-2 ring-[#00c853]/30"
                      : "border-white/10 focus:border-[#00c853] focus:bg-black/60 focus:ring-2 focus:ring-[#00c853]/30")
                  }
                />
              ))}
            </div>

            <AuthButton type="submit" loading={loading}>Verify &amp; Create Account</AuthButton>
          </form>

          <button
            type="button"
            onClick={() => { setStep("form"); setError(""); setInfo(""); }}
            className="mt-5 w-full text-center text-xs text-white/50 hover:text-white/80"
          >
            ← Back to edit details
          </button>
        </>
      )}
    </AuthShell>
  );
}
