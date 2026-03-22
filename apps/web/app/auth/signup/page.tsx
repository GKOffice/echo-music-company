"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [role, setRole] = useState<"artist" | "producer" | "developer">("artist");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const inputClass = "w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all text-sm";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!email || !password) { setError("Please fill in all fields."); return; }
    if (password !== confirm) { setError("Passwords don't match."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setLoading(true);
    const result = await signup(email, password, role);
    setLoading(false);
    if (result.success) {
      router.push("/dashboard");
    } else {
      setError(result.error || "Could not create account.");
    }
  }

  const roles = [
    { value: "artist", label: "Artist", desc: "Submit music, drop points" },
    { value: "producer", label: "Producer", desc: "Sell beats, find artists" },
    { value: "developer", label: "Developer", desc: "Build on the Melodio API" },
  ] as const;

  return (
    <main className="min-h-screen bg-[#0a0a0f] flex flex-col">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4 pt-24 pb-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">🎵</div>
            <h1 className="text-3xl font-black text-[#f9fafb] mb-2">Join Melodio</h1>
            <p className="text-[#9ca3af] text-sm">Own the music you believe in.</p>
          </div>

          <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-8">
            {/* Google OAuth */}
            <button
              type="button"
              onClick={() => alert("Google OAuth coming soon!")}
              className="w-full flex items-center justify-center gap-3 border border-[#2a2a3a] hover:border-[#8b5cf6] bg-[#0a0a0f] text-[#f9fafb] font-medium text-sm px-4 py-3 rounded-lg transition-all mb-6"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M17.64 9.2a10.34 10.34 0 0 0-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 h-px bg-[#2a2a3a]" />
              <span className="text-xs text-[#6b7280]">or sign up with email</span>
              <div className="flex-1 h-px bg-[#2a2a3a]" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Role selector */}
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-2">I am a…</label>
                <div className="grid grid-cols-2 gap-2">
                  {roles.map((r) => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setRole(r.value)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        role === r.value
                          ? "bg-[#8b5cf6]/20 border-[#8b5cf6] text-[#f9fafb]"
                          : "bg-[#0a0a0f] border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50"
                      }`}
                    >
                      <div className="text-sm font-semibold">{r.label}</div>
                      <div className="text-xs opacity-70 mt-0.5">{r.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" className={inputClass} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 characters" className={inputClass} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Confirm Password</label>
                <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Repeat password" className={inputClass} required />
              </div>

              {error && (
                <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#fca5a5] text-sm rounded-lg px-4 py-3">{error}</div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 text-white font-bold text-sm px-6 py-3.5 rounded-xl transition-colors"
                style={{ boxShadow: "0 0 20px rgba(139,92,246,0.3)" }}
              >
                {loading ? "Creating account…" : "Create Account"}
              </button>

              <p className="text-xs text-[#6b7280] text-center">
                By signing up you agree to Melodio&apos;s Terms of Service and Privacy Policy.
              </p>
            </form>
          </div>

          <p className="text-center text-sm text-[#9ca3af] mt-6">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-[#8b5cf6] hover:underline font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
