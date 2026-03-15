"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import Navbar from "../../components/Navbar";
import { submitDemo } from "../../lib/api";
import type { DemoFormData } from "../../lib/api";

const GENRES = [
  "Afrobeats", "Afro-Fusion", "Alt R&B", "Hip-Hop", "Trap", "Trap Soul",
  "Pop", "Indie Pop", "R&B", "Neo-Soul", "Electronic", "Dance/EDM",
  "Reggaeton", "Drill", "Amapiano", "Gospel", "Jazz", "Other",
];

export default function SubmitPage() {
  const [form, setForm] = useState<Omit<DemoFormData, "audioFile">>({
    artistName: "",
    email: "",
    genre: "",
    spotifyUrl: "",
    instagram: "",
    soundcloudUrl: "",
    bio: "",
  });
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === "audio/mpeg" || file.type === "audio/wav" || file.name.endsWith(".mp3") || file.name.endsWith(".wav"))) {
      setAudioFile(file);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.artistName || !form.email || !form.genre) {
      setError("Please fill in all required fields.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const result = await submitDemo({ ...form, audioFile: audioFile ?? undefined });
      if (result.success) setSuccess(true);
      else setError("Submission failed. Please try again.");
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-2xl mx-auto px-4 pt-28 pb-20">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-pulse" />
            A&R Agent reviewing submissions now
          </div>
          <h1 className="text-4xl font-black text-[#f9fafb] mb-3">Submit Your Demo</h1>
          <p className="text-[#9ca3af]">
            Our A&R Agent listens to every submission. No gatekeepers. Just your music.
          </p>
        </div>

        {success ? (
          /* Success State */
          <div className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-10 text-center" style={{ boxShadow: "0 0 40px rgba(16,185,129,0.15)" }}>
            <div className="text-6xl mb-5">🎤</div>
            <h2 className="text-2xl font-black text-[#f9fafb] mb-3">Demo Received!</h2>
            <p className="text-[#9ca3af] text-lg mb-2">
              We received your demo. Expect a response within 48 hours.
            </p>
            <p className="text-sm text-[#9ca3af] mb-8">
              Our A&R Agent will analyze your music and reach out to <span className="text-[#f9fafb]">{form.email}</span>.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/"
                className="border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                Back to Home
              </Link>
              <Link
                href="/points"
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                Browse Points Store
              </Link>
            </div>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="space-y-5">

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Artist Name */}
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                  Artist Name <span className="text-[#ef4444]">*</span>
                </label>
                <input
                  name="artistName"
                  value={form.artistName}
                  onChange={handleChange}
                  placeholder="Your artist name"
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
                  required
                />
              </div>

              {/* Email */}
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
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
                  required
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
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all appearance-none"
                required
              >
                <option value="" disabled className="text-[#9ca3af]">Select genre...</option>
                {GENRES.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>

            {/* Spotify URL */}
            <div>
              <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                Spotify Artist URL <span className="text-[#ef4444]">*</span>
              </label>
              <input
                name="spotifyUrl"
                value={form.spotifyUrl}
                onChange={handleChange}
                placeholder="https://open.spotify.com/artist/..."
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Instagram */}
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                  Instagram <span className="text-[#ef4444]">*</span>
                </label>
                <div className="flex">
                  <span className="bg-[#2a2a3a] border border-r-0 border-[#2a2a3a] rounded-l-lg px-3 flex items-center text-[#9ca3af] text-sm">
                    @
                  </span>
                  <input
                    name="instagram"
                    value={form.instagram}
                    onChange={handleChange}
                    placeholder="yourhandle"
                    className="flex-1 bg-[#13131a] border border-[#2a2a3a] rounded-r-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* SoundCloud / YouTube */}
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                  SoundCloud or YouTube <span className="text-[#9ca3af] text-xs">(optional)</span>
                </label>
                <input
                  name="soundcloudUrl"
                  value={form.soundcloudUrl}
                  onChange={handleChange}
                  placeholder="soundcloud.com/... or youtube.com/..."
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Audio Upload */}
            <div>
              <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                Upload MP3 <span className="text-[#9ca3af] text-xs">(optional)</span>
              </label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`w-full rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200 ${
                  dragOver
                    ? "border-[#8b5cf6] bg-[#8b5cf6]/10"
                    : audioFile
                    ? "border-[#10b981] bg-[#10b981]/10"
                    : "border-[#2a2a3a] bg-[#13131a] hover:border-[#8b5cf6]"
                }`}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".mp3,.wav,audio/mpeg,audio/wav"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) setAudioFile(f);
                  }}
                />
                {audioFile ? (
                  <div>
                    <div className="text-3xl mb-2">🎵</div>
                    <div className="text-[#10b981] font-semibold text-sm">{audioFile.name}</div>
                    <div className="text-xs text-[#9ca3af] mt-1">{(audioFile.size / 1024 / 1024).toFixed(1)} MB</div>
                  </div>
                ) : (
                  <div>
                    <div className="text-3xl mb-2">📁</div>
                    <div className="text-[#9ca3af] text-sm">Drag & drop your MP3 here, or click to browse</div>
                    <div className="text-xs text-[#9ca3af]/60 mt-1">MP3 or WAV, max 50MB</div>
                  </div>
                )}
              </div>
            </div>

            {/* Bio */}
            <div>
              <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                Tell us about yourself <span className="text-[#ef4444]">*</span>
              </label>
              <textarea
                name="bio"
                value={form.bio}
                onChange={handleChange}
                placeholder="Who are you as an artist? What makes your sound unique? Any releases or achievements we should know about?"
                rows={5}
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all resize-none"
                required
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
              className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold text-base px-6 py-4 rounded-xl transition-colors duration-200"
              style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
            >
              {submitting ? "Submitting..." : "Submit My Demo"}
            </button>

            <p className="text-xs text-[#9ca3af] text-center">
              By submitting you agree to ECHO&apos;s submission terms. We review every demo within 48 hours.
            </p>
          </form>
        )}

        {/* Trust signals */}
        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
          {[
            { icon: "⚡", label: "AI-powered review", sub: "Results in 48h" },
            { icon: "🔒", label: "100% yours", sub: "Keep all masters" },
            { icon: "🚫", label: "No contracts", sub: "No long-term lock-in" },
          ].map((item) => (
            <div key={item.label} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-4">
              <div className="text-2xl mb-1">{item.icon}</div>
              <div className="text-xs font-semibold text-[#f9fafb]">{item.label}</div>
              <div className="text-xs text-[#9ca3af] mt-0.5">{item.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
