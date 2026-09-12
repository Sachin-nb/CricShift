"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { AuthShell, AuthInput, AuthButton, AuthMessage } from "@/components/auth/auth-shell";
import { SocialButtons } from "@/components/auth/social-buttons";
import { apiLogin, markSplashPending } from "@/lib/api/auth";
import { useAuth } from "@/context/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { setSession } = useAuth();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [keep, setKeep]         = useState(true);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { token, user } = await apiLogin({ email, password });
      // `keep` → persist in localStorage so the login survives a browser restart.
      // Unchecked → sessionStorage only, forgotten when the tab/browser closes.
      setSession(token, user, keep);
      markSplashPending(); // play the intro animation before the app appears
      router.push("/"); // land on the home page after login
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      eyebrow="Live World Cup Coverage"
      headlineTop="Your Innings"
      headlineBottom="Awaits."
      subtext="Step up to the crease. Experience real-time ball tracking, expert commentary, and competitive fantasy leagues."
      footerSlot={
        <div className="flex gap-10">
          <div>
            <p className="text-2xl font-black text-[#c8f000]">10M+</p>
            <p className="text-[10px] uppercase tracking-widest text-white/50">Active Players</p>
          </div>
          <div>
            <p className="text-2xl font-black text-[#c8f000]">0.03s</p>
            <p className="text-[10px] uppercase tracking-widest text-white/50">Live Latency</p>
          </div>
        </div>
      }
    >
      <h2 className="text-2xl font-black uppercase tracking-tight">Welcome Back</h2>
      <p className="mb-6 mt-1 text-sm text-white/50">Enter your credentials to enter the arena.</p>

      <AuthMessage type="error" text={error} />

      <form onSubmit={handleSubmit}>
        <AuthInput
          label="Email or Username"
          type="email"
          required
          autoComplete="email"
          placeholder="stump.blaster@cricshift.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <div className="mb-4">
          <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
            Password
          </label>
          <div className="relative">
            <input
              type={showPw ? "text" : "password"}
              required
              autoComplete="current-password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 pr-11 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30"
            />
            <button
              type="button"
              onClick={() => setShowPw((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70"
              tabIndex={-1}
            >
              {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div className="mb-6 flex items-center justify-between">
          <label className="flex cursor-pointer items-center gap-2 text-xs text-white/70">
            <input
              type="checkbox"
              checked={keep}
              onChange={(e) => setKeep(e.target.checked)}
              className="h-4 w-4 accent-[#c8f000]"
            />
            Keep me logged in
          </label>
          <Link href="/reset-password" className="text-xs font-bold text-[#c8f000] hover:underline">
            Forgot password?
          </Link>
        </div>

        <AuthButton type="submit" loading={loading}>Log In</AuthButton>
      </form>

      <div className="my-5 flex items-center gap-3 text-[10px] uppercase tracking-widest text-white/30">
        <span className="h-px flex-1 bg-white/10" />
        Or enter with
        <span className="h-px flex-1 bg-white/10" />
      </div>

      <SocialButtons
        onSuccess={(token, user) => {
          setSession(token, user, keep);
          markSplashPending();
          router.push("/");
        }}
        onError={(msg) => setError(msg)}
      />

      <p className="mt-6 text-center text-xs text-white/50">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-bold text-[#c8f000] hover:underline">
          Sign Up Now
        </Link>
      </p>
    </AuthShell>
  );
}
