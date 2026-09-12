"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell, AuthButton, AuthMessage, BackToLogin } from "@/components/auth/auth-shell";
import { apiSendOtp } from "@/lib/api/auth";

// sessionStorage keys shared across the 3 reset steps
export const RESET_EMAIL_KEY = "cs_reset_email";
export const RESET_TOKEN_KEY = "cs_reset_token";

export default function ResetEmailPage() {
  const router = useRouter();
  const [email, setEmail]     = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [info, setInfo]       = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const res = await apiSendOtp(email.trim().toLowerCase());

      // If the backend confirms the email is NOT registered, tell the user
      // instead of sending them to a verify page where nothing will work.
      if (res.registered === false) {
        setError(
          "No account is registered with this email address. Please check it or sign up first.",
        );
        return;
      }

      // Persist the email so step 2 can verify against it
      sessionStorage.setItem(RESET_EMAIL_KEY, email.trim().toLowerCase());

      setInfo("A verification code has been sent to your email. Check your inbox (and spam).");
      setTimeout(() => router.push("/reset-password/verify-otp"), 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the code. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      eyebrow="CricShift Reset Initiative"
      headlineTop="Every Champion Gets"
      headlineBottom="A Second Chance."
      subtext="Back to the crease. Secure your profile, reset your credentials, and jump straight back into the match-day action."
    >
      <h2 className="text-2xl font-black uppercase tracking-tight">Reset Password</h2>
      <p className="mb-6 mt-1 text-sm text-white/50">
        Enter your registered email address to receive a verification code and secure your account.
      </p>

      {/* Step indicator */}
      <StepDots active={1} />

      <AuthMessage type="error" text={error} />
      <AuthMessage type="success" text={info} />

      <form onSubmit={handleSubmit}>
        <div className="mb-5">
          <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
            Email Address
          </label>
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border-l-2 border-l-[#c8f000] border-y border-r border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30"
          />
        </div>

        <AuthButton type="submit" loading={loading}>Send OTP Code</AuthButton>
      </form>

      <BackToLogin />
    </AuthShell>
  );
}

/** Small 3-step progress indicator shown on each reset page. */
export function StepDots({ active }: { active: 1 | 2 | 3 }) {
  return (
    <div className="mb-6 flex items-center gap-2">
      {[1, 2, 3].map((n) => (
        <div key={n} className="flex items-center gap-2">
          <span
            className={
              "grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold " +
              (n <= active ? "bg-[#c8f000] text-black" : "bg-white/10 text-white/40")
            }
          >
            {n}
          </span>
          {n < 3 && (
            <span className={"h-px w-6 " + (n < active ? "bg-[#c8f000]" : "bg-white/10")} />
          )}
        </div>
      ))}
    </div>
  );
}
