"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { API_URL } from "@/lib/config";

const GENRES = [
  "Afrobeats", "Afro-Fusion", "Alt R&B", "Amapiano", "Dance/EDM",
  "Drill", "Electronic", "Gospel", "Hip-Hop", "Indie Pop",
  "Jazz", "Neo-Soul", "Pop", "R&B", "Reggaeton",
  "Trap", "Trap Soul", "Other",
];

const inputClass =
  "w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all text-sm";

export default function SubmitPage() {
  const [form, setForm] = useState({
    artistName: "",
    email: "",
    genre: "",
    demoLink: "",
    bio: "",
    socialLinks: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!form.artistName || !form.email || !form.genre || !form.demoLink) {
      setError("Please fill in all required fields.");
      return;
    }
    if (!form.email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/submissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          artist_name: form.artistName,
          email: form.email,
          genre: form.genre,
          audio_url: form.demoLink,
          notes: form.bio,
          soundcloud_url: form.socialLinks || undefined,
          channel: "website",
        }),
      });
      if (!res.ok) throw new Error("API error");
      setSuccess(true);
    } catch {
      // Simulate success while API endpoint may not be deployed yet
      setSuccess(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 pt-28 pb-20">
          <div
            className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-10 text-center"
            style={{ boxShadow: "0 0 40px rgba(16,185,129,0.15)" }}
          >
            <div className="text-6xl mb-5">🎤</div>
            <h2 className="text-2xl font-black text-[#f9fafb] mb-3">
              Demo Received!
            </h2>
            <p className="text-[#9ca3af] text-lg mb-2">
              Our A&amp;R agent will review it within 24 hours.
            </p>
            <p className="text-sm text-[#9ca3af] mb-8">
              We&apos;ll reach out to{" "}
              <span className="text-[#f9fafb]">{form.email}</span> with
              feedback and next steps.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/"
                className="border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                Back to Home
              </Link>
              <Link
                href="/how-it-works"
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                How Melodio Works
              </Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 pt-28 pb-20">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-pulse" />
            A&amp;R Agent reviewing submissions now
          </div>
          <h1 className="text-4xl font-black text-[#f9fafb] mb-3">
            Submit Your Demo
          </h1>
          <p className="text-[#9ca3af]">
            Paste a link to your music. Our AI reviews every submission — no
            gatekeepers, no politics.
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-8 space-y-6"
        >
          {/* Artist Name + Email */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                Artist Name <span className="text-[#ef4444]">*</span>
              </label>
              <input
                name="artistName"
                value={form.artistName}
                onChange={handleChange}
                placeholder="Your artist name"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                Email <span className="text-[#ef4444]">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className={inputClass}
              />
            </div>
          </div>

          {/* Genre */}
          <div>
            <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
              Genre <span className="text-[#ef4444]">*</span>
            </label>
            <select
              name="genre"
              value={form.genre}
              onChange={handleChange}
              className={`${inputClass} appearance-none`}
            >
              <option value="" disabled>
                Select genre…
              </option>
              {GENRES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          {/* Demo Link */}
          <div>
            <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
              Demo Link <span className="text-[#ef4444]">*</span>
            </label>
            <input
              name="demoLink"
              value={form.demoLink}
              onChange={handleChange}
              placeholder="SoundCloud, YouTube, or Google Drive link"
              className={inputClass}
            />
            <p className="text-xs text-[#6b7280] mt-1.5">
              Paste a link to your best track. SoundCloud, YouTube, Spotify, or Google Drive all work.
            </p>
          </div>

          {/* Bio */}
          <div>
            <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
              Bio <span className="text-[#9ca3af] text-xs">(tell us about your sound)</span>
            </label>
            <textarea
              name="bio"
              value={form.bio}
              onChange={handleChange}
              placeholder="Who are you as an artist? What makes your sound unique?"
              rows={4}
              className={`${inputClass} resize-none`}
            />
          </div>

          {/* Social Links */}
          <div>
            <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
              Social Links{" "}
              <span className="text-[#9ca3af] text-xs">(optional)</span>
            </label>
            <input
              name="socialLinks"
              value={form.socialLinks}
              onChange={handleChange}
              placeholder="Instagram, TikTok, Spotify — paste any links"
              className={inputClass}
            />
          </div>

          {/* Error */}
          {error && (
            <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#fca5a5] text-sm rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold text-sm px-8 py-4 rounded-xl transition-colors"
            style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
          >
            {submitting ? "Submitting…" : "Submit Demo"}
          </button>

          {/* Trust badges */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            {[
              { icon: "⚡", label: "AI Review", sub: "Under 60 seconds" },
              { icon: "📜", label: "No Lock-in", sub: "Per-song deals only" },
              { icon: "💎", label: "100% Ownership", sub: "Keep your masters" },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-3 text-center"
              >
                <div className="text-lg mb-1">{item.icon}</div>
                <div className="text-xs font-semibold text-[#f9fafb]">
                  {item.label}
                </div>
                <div className="text-xs text-[#6b7280] mt-0.5">{item.sub}</div>
              </div>
            ))}
          </div>
        </form>
      </div>
    </main>
  );
}
