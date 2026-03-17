"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { submitDemo } from "@/lib/api";
import type { DemoFormData } from "@/lib/api";

const GENRES = [
  "Afrobeats", "Afro-Fusion", "Alt R&B", "Hip-Hop", "Trap", "Trap Soul",
  "Pop", "Indie Pop", "R&B", "Neo-Soul", "Electronic", "Dance/EDM",
  "Reggaeton", "Drill", "Amapiano", "Gospel", "Jazz", "Other",
];

const STEPS = [
  { num: 1, label: "Artist Info" },
  { num: 2, label: "Upload Demo" },
  { num: 3, label: "Deal Prefs" },
  { num: 4, label: "Review" },
];

const inputClass = "w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all text-sm";

export default function SubmitPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<Omit<DemoFormData, "audioFile">>({
    artistName: "", email: "", genre: "", spotifyUrl: "", instagram: "", soundcloudUrl: "", bio: "",
  });
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [pointsToOffer, setPointsToOffer] = useState(10);
  const [marketingSplit, setMarketingSplit] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type.includes("audio") || file.name.match(/\.(mp3|wav|aac|flac)$/i))) {
      setAudioFile(file);
    }
  }

  function validateStep() {
    if (step === 1) {
      if (!form.artistName || !form.email || !form.genre) {
        setError("Please fill in Artist Name, Email, and Genre.");
        return false;
      }
      if (!form.email.includes("@")) { setError("Please enter a valid email."); return false; }
    }
    return true;
  }

  function nextStep() {
    if (validateStep()) { setError(""); setStep((s) => Math.min(s + 1, 4)); }
  }
  function prevStep() { setStep((s) => Math.max(s - 1, 1)); setError(""); }

  async function handleSubmit() {
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

  if (success) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 pt-28 pb-20">
          <div className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-10 text-center" style={{ boxShadow: "0 0 40px rgba(16,185,129,0.15)" }}>
            <div className="text-6xl mb-5">🎤</div>
            <h2 className="text-2xl font-black text-[#f9fafb] mb-3">Demo Received!</h2>
            <p className="text-[#9ca3af] text-lg mb-2">We received your demo. Expect a response within 48 hours.</p>
            <p className="text-sm text-[#9ca3af] mb-8">Our A&R Agent will reach out to <span className="text-[#f9fafb]">{form.email}</span>.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/" className="border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-6 py-3 rounded-lg transition-colors">Back to Home</Link>
              <Link href="/points" className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-3 rounded-lg transition-colors">Browse Points Store</Link>
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
            A&R Agent reviewing submissions now
          </div>
          <h1 className="text-4xl font-black text-[#f9fafb] mb-3">Submit Your Demo</h1>
          <p className="text-[#9ca3af]">Our A&R Agent listens to every submission. No gatekeepers.</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-between mb-10 relative">
          <div className="absolute top-4 left-0 right-0 h-0.5 bg-[#2a2a3a] z-0" />
          <div className="absolute top-4 left-0 h-0.5 bg-[#8b5cf6] z-0 transition-all duration-300" style={{ width: `${((step - 1) / 3) * 100}%` }} />
          {STEPS.map((s) => (
            <div key={s.num} className="flex flex-col items-center relative z-10">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                step > s.num ? "bg-[#10b981] text-white" : step === s.num ? "bg-[#8b5cf6] text-white" : "bg-[#13131a] border border-[#2a2a3a] text-[#6b7280]"
              }`}>
                {step > s.num ? "✓" : s.num}
              </div>
              <span className={`text-xs mt-2 font-medium ${step === s.num ? "text-[#f9fafb]" : "text-[#6b7280]"}`}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-8">
          {step === 1 && (
            <div className="space-y-5">
              <h2 className="text-xl font-bold text-[#f9fafb] mb-6">Tell us about yourself</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Artist Name <span className="text-[#ef4444]">*</span></label>
                  <input name="artistName" value={form.artistName} onChange={handleChange} placeholder="Your artist name" className={inputClass} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Email <span className="text-[#ef4444]">*</span></label>
                  <input type="email" name="email" value={form.email} onChange={handleChange} placeholder="you@example.com" className={inputClass} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Genre <span className="text-[#ef4444]">*</span></label>
                <select name="genre" value={form.genre} onChange={handleChange} className={`${inputClass} appearance-none`}>
                  <option value="" disabled>Select genre…</option>
                  {GENRES.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Spotify Artist URL <span className="text-[#9ca3af] text-xs">(optional)</span></label>
                <input name="spotifyUrl" value={form.spotifyUrl} onChange={handleChange} placeholder="https://open.spotify.com/artist/..." className={inputClass} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Instagram <span className="text-[#9ca3af] text-xs">(optional)</span></label>
                  <div className="flex">
                    <span className="bg-[#2a2a3a] border border-r-0 border-[#2a2a3a] rounded-l-lg px-3 flex items-center text-[#9ca3af] text-sm">@</span>
                    <input name="instagram" value={form.instagram} onChange={handleChange} placeholder="yourhandle" className="flex-1 bg-[#13131a] border border-[#2a2a3a] rounded-r-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all text-sm" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">SoundCloud / YouTube <span className="text-[#9ca3af] text-xs">(optional)</span></label>
                  <input name="soundcloudUrl" value={form.soundcloudUrl} onChange={handleChange} placeholder="soundcloud.com/..." className={inputClass} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">Bio <span className="text-[#ef4444]">*</span></label>
                <textarea name="bio" value={form.bio} onChange={handleChange} placeholder="Who are you as an artist? What makes your sound unique?" rows={4} className={`${inputClass} resize-none`} />
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-xl font-bold text-[#f9fafb] mb-6">Upload Your Demo</h2>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`w-full rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-200 ${
                  dragOver ? "border-[#8b5cf6] bg-[#8b5cf6]/10"
                  : audioFile ? "border-[#10b981] bg-[#10b981]/10"
                  : "border-[#2a2a3a] bg-[#0a0a0f] hover:border-[#8b5cf6]/50"
                }`}
              >
                <input ref={fileRef} type="file" accept=".mp3,.wav,.aac,.flac,audio/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setAudioFile(f); }} />
                {audioFile ? (
                  <div>
                    <div className="text-4xl mb-3">🎵</div>
                    <div className="text-[#10b981] font-semibold">{audioFile.name}</div>
                    <div className="text-xs text-[#9ca3af] mt-1">{(audioFile.size / 1024 / 1024).toFixed(1)} MB</div>
                    <button type="button" onClick={(e) => { e.stopPropagation(); setAudioFile(null); }} className="mt-4 text-xs text-[#9ca3af] hover:text-[#ef4444] transition-colors">Remove file</button>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-3">📁</div>
                    <div className="text-[#f9fafb] font-semibold mb-1">Drag & drop your track here</div>
                    <div className="text-[#9ca3af] text-sm">or click to browse</div>
                    <div className="text-xs text-[#6b7280] mt-3">MP3, WAV, AAC, FLAC — max 50MB</div>
                  </div>
                )}
              </div>
              <div className="mt-6 bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-4">
                <p className="text-xs text-[#9ca3af] leading-relaxed">
                  <span className="text-[#f9fafb] font-semibold">No demo file?</span> That&apos;s okay — you can still submit with a Spotify or SoundCloud link. The A&R Agent will review your streaming catalog directly.
                </p>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-8">
              <h2 className="text-xl font-bold text-[#f9fafb] mb-6">Deal Preferences</h2>
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium text-[#e8e8f0]">Points to Offer Fans</label>
                  <span className="text-[#8b5cf6] font-bold text-lg">{pointsToOffer}%</span>
                </div>
                <input type="range" min={0} max={50} step={5} value={pointsToOffer} onChange={(e) => setPointsToOffer(Number(e.target.value))} className="w-full accent-[#8b5cf6] mb-2" />
                <div className="flex justify-between text-xs text-[#6b7280]"><span>0% (no points)</span><span>50% (max)</span></div>
                <p className="text-xs text-[#9ca3af] mt-3">
                  Offer fans a % of your streaming royalties via Melodio Points. You keep all publishing. We take 10% admin fee only. No long-term contracts.
                </p>
              </div>

              <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-5">
                <label className="flex items-start gap-3 cursor-pointer">
                  <div className="relative mt-0.5 shrink-0">
                    <input type="checkbox" checked={marketingSplit} onChange={(e) => setMarketingSplit(e.target.checked)} className="sr-only" />
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${marketingSplit ? "bg-[#8b5cf6] border-[#8b5cf6]" : "border-[#2a2a3a] bg-[#13131a]"}`}>
                      {marketingSplit && <svg width="10" height="8" fill="none" viewBox="0 0 10 8"><path d="M1 4l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-[#f9fafb]">Opt into Melodio Marketing</div>
                    <div className="text-xs text-[#9ca3af] mt-1">Allow our Marketing Agent to promote your releases across editorial playlists, social campaigns, and sync opportunities. A 5% additional revenue share applies only on deals we directly source.</div>
                  </div>
                </label>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                {[
                  { icon: "📜", label: "No Contracts", sub: "Per-song deals only" },
                  { icon: "💎", label: "100% Publishing", sub: "Always yours" },
                  { icon: "⚡", label: "10% Admin Fee", sub: "On royalties collected" },
                ].map((item) => (
                  <div key={item.label} className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-4">
                    <div className="text-2xl mb-2">{item.icon}</div>
                    <div className="text-xs font-semibold text-[#f9fafb]">{item.label}</div>
                    <div className="text-xs text-[#9ca3af] mt-0.5">{item.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-5">
              <h2 className="text-xl font-bold text-[#f9fafb] mb-6">Review & Submit</h2>
              <div className="space-y-3">
                {[
                  { label: "Artist Name", value: form.artistName },
                  { label: "Email", value: form.email },
                  { label: "Genre", value: form.genre },
                  { label: "Spotify", value: form.spotifyUrl || "—" },
                  { label: "Instagram", value: form.instagram ? `@${form.instagram}` : "—" },
                  { label: "Demo File", value: audioFile ? audioFile.name : "No file uploaded" },
                  { label: "Points Offered", value: `${pointsToOffer}% royalty share` },
                  { label: "Marketing Opt-in", value: marketingSplit ? "Yes" : "No" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2.5 border-b border-[#2a2a3a] last:border-0">
                    <span className="text-sm text-[#9ca3af]">{item.label}</span>
                    <span className="text-sm text-[#f9fafb] font-medium max-w-xs truncate text-right">{item.value}</span>
                  </div>
                ))}
              </div>
              {form.bio && (
                <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-4">
                  <div className="text-xs text-[#9ca3af] mb-2 font-medium">Bio</div>
                  <div className="text-sm text-[#f9fafb] leading-relaxed">{form.bio}</div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#fca5a5] text-sm rounded-lg px-4 py-3">{error}</div>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between mt-6">
          <button
            onClick={prevStep}
            disabled={step === 1}
            className="text-sm font-medium text-[#9ca3af] hover:text-[#f9fafb] disabled:opacity-30 disabled:cursor-not-allowed transition-colors px-4 py-2"
          >
            ← Back
          </button>
          {step < 4 ? (
            <button
              onClick={nextStep}
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-sm px-8 py-3 rounded-xl transition-colors"
            >
              Continue →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold text-sm px-8 py-3 rounded-xl transition-colors"
              style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
            >
              {submitting ? "Submitting…" : "Submit Demo 🚀"}
            </button>
          )}
        </div>
      </div>
    </main>
  );
}
