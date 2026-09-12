"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, CheckCircle2 } from "lucide-react";
import { AuthShell, AuthButton, AuthMessage, BackToLogin } from "@/components/auth/auth-shell";
import { StepDots, RESET_EMAIL_KEY, RESET_TOKEN_KEY } from "../page";
import { apiResetPassword } from "@/lib/api/auth";

export default function NewPasswordPage() {
  const router = useRouter();
  const [resetToken, setResetToken] = useState("");
  const [password, setPassword]     = useState("");
  const [confirm, setConfirm]       = useState("");
  const [showPw, setShowPw]         = useState(false);
  const [showCf, setShowCf]         = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");
  const [done, setDone]             = useState(false);

  // Guard: must have a verified reset token from step 2
  useEffect(() => {
    const t = sessionStorage.getItem(RESET_TOKEN_KEY);
    if (!t) {
      router.replace("/reset-password");
      return;
    }
    setResetToken(t);
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await apiResetPassword(resetToken, password);
      // Clean up reset state
      sessionStorage.removeItem(RESET_TOKEN_KEY);
      sessionStorage.removeItem(RESET_EMAIL_KEY);
      setDone(true);
      setTimeout(() => router.push("/login"), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset password. Please try again.");
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
      <h2 className="text-2xl font-black uppercase tracking-tight">New Password</h2>
      <p className="mb-6 mt-1 text-sm text-white/50">
        Create a strong new password to secure your account.
      </p>

      <StepDots active={3} />

      {done ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-[#c8f000]/30 bg-[#c8f000]/10 p-8 text-center">
          <CheckCircle2 className="h-10 w-10 text-[#c8f000]" />
          <p className="font-bold text-white">Password reset successful!</p>
          <p className="text-xs text-white/60">Redirecting you to login…</p>
        </div>
      ) : (
        <>
          <AuthMessage type="error" text={error} />

          <form onSubmit={handleSubmit}>
            {/* New password */}
            <div className="mb-4">
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  placeholder="SecurePassword123!"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 pr-11 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30"
                />
                <button type="button" onClick={() => setShowPw((s) => !s)} tabIndex={-1}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Confirm password */}
            <div className="mb-6">
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showCf ? "text" : "password"}
                  required
                  placeholder="Re-enter new password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 pr-11 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30"
                />
                <button type="button" onClick={() => setShowCf((s) => !s)} tabIndex={-1}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70">
                  {showCf ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <AuthButton type="submit" loading={loading}>Reset Password &amp; Login</AuthButton>
          </form>

          <BackToLogin />
        </>
      )}
    </AuthShell>
  );
}
