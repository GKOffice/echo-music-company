"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { API_URL } from "@/lib/config";
import { getToken } from "@/lib/auth";

const STEPS = ["Profile", "Connect Platforms", "Upload Demo", "Review"];

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" };
}

export default function OnboardingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Profile fields
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [genre, setGenre] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");

  // Socials
  const [spotifyUrl, setSpotifyUrl] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");

  // Demo
  const [demoTitle, setDemoTitle] = useState("");
  const [demoGenre, setDemoGenre] = useState("");
  const [demoUrl, setDemoUrl] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login?next=/onboarding");
    }
  }, [user, loading, router]);

  // Load existing onboarding status
  useEffect(() => {
    if (!user) return;
    fetch(`${API_URL}/api/v1/onboarding/status`, { headers: authHeaders() })
      .then((r) => r.json())
      .then((data) => {
        if (data.onboarding_step) setStep(Math.min(data.onboarding_step, 3));
        if (data.profile) {
          if (data.profile.name) setName(data.profile.name);
          if (data.profile.bio) setBio(data.profile.bio);
          if (data.profile.genre) setGenre(data.profile.genre);
          if (data.profile.photo_url) setPhotoUrl(data.profile.photo_url);
        }
      })
      .catch(() => {});
  }, [user]);

  async function saveProfile() {
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/onboarding/profile`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name, bio, genre, photo_url: photoUrl }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to save");
      setStep(1);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function saveSocials() {
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/onboarding/connect-socials`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          spotify_url: spotifyUrl || null,
          instagram_url: instagramUrl || null,
          youtube_url: youtubeUrl || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to save");
      setStep(2);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function submitDemo() {
    if (!demoTitle || !demoUrl) {
      setError("Title and audio URL are required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/onboarding/demo`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title: demoTitle, genre: demoGenre || null, audio_url: demoUrl }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to submit");
      setStep(3);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 z-50 h-1 bg-[#1a1a2e]">
        <div
          className="h-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="max-w-2xl mx-auto px-4 pt-20 pb-16">
        {/* Step indicators */}
        <div className="flex items-center justify-center gap-2 mb-12">
          {STEPS.map((label, i) => (
            <button
              key={label}
              onClick={() => i < step && setStep(i)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                i === step
                  ? "bg-purple-600/20 text-purple-400 border border-purple-500/30"
                  : i < step
                  ? "bg-emerald-600/20 text-emerald-400 cursor-pointer"
                  : "bg-[#13131a] text-[#52525b]"
              }`}
            >
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                i < step ? "bg-emerald-500 text-white" : i === step ? "bg-purple-600 text-white" : "bg-[#1a1a2e] text-[#52525b]"
              }`}>
                {i < step ? "\u2713" : i + 1}
              </span>
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Profile */}
        {step === 0 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Create your artist profile</h1>
              <p className="text-[#a1a1aa]">Tell us about yourself. This will be visible on your Melodio artist page.</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Artist / Stage Name</label>
                <input
                  type="text" value={name} onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="Your artist name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Bio</label>
                <textarea
                  value={bio} onChange={(e) => setBio(e.target.value)} rows={4}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors resize-none"
                  placeholder="Tell your story..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Genre</label>
                <select
                  value={genre} onChange={(e) => setGenre(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] focus:outline-none focus:border-purple-500 transition-colors"
                >
                  <option value="">Select genre</option>
                  {["Pop", "Hip-Hop", "R&B", "Rock", "Electronic", "Country", "Latin", "Indie", "Jazz", "Classical", "Afrobeats", "K-Pop", "Other"].map(
                    (g) => <option key={g} value={g.toLowerCase()}>{g}</option>
                  )}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Profile Photo URL</label>
                <input
                  type="url" value={photoUrl} onChange={(e) => setPhotoUrl(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="https://..."
                />
              </div>
            </div>
            <button
              onClick={saveProfile} disabled={saving || !name}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              {saving ? "Saving..." : "Continue"}
            </button>
          </div>
        )}

        {/* Step 2: Connect Platforms */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Connect your platforms</h1>
              <p className="text-[#a1a1aa]">Link your existing profiles so our agents can analyze your audience and reach.</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Spotify Profile URL</label>
                <input
                  type="url" value={spotifyUrl} onChange={(e) => setSpotifyUrl(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="https://open.spotify.com/artist/..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Instagram URL</label>
                <input
                  type="url" value={instagramUrl} onChange={(e) => setInstagramUrl(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="https://instagram.com/..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">YouTube Channel URL</label>
                <input
                  type="url" value={youtubeUrl} onChange={(e) => setYoutubeUrl(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="https://youtube.com/@..."
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(0)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={saveSocials} disabled={saving}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {saving ? "Saving..." : "Continue"}
              </button>
            </div>
            <button onClick={() => setStep(2)} className="w-full text-[#52525b] hover:text-[#a1a1aa] text-sm transition-colors">
              Skip for now
            </button>
          </div>
        )}

        {/* Step 3: Upload Demo */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Upload your first demo</h1>
              <p className="text-[#a1a1aa]">Share a track with our A&R agent. We will review it within 24 hours.</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Track Title</label>
                <input
                  type="text" value={demoTitle} onChange={(e) => setDemoTitle(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="My Best Track"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Genre</label>
                <input
                  type="text" value={demoGenre} onChange={(e) => setDemoGenre(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="e.g. hip-hop, pop, r&b"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Audio URL (SoundCloud, Google Drive, Dropbox, etc.)</label>
                <input
                  type="url" value={demoUrl} onChange={(e) => setDemoUrl(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                  placeholder="https://..."
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={submitDemo} disabled={saving || !demoTitle || !demoUrl}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {saving ? "Submitting..." : "Submit Demo"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Review / Complete */}
        {step === 3 && (
          <div className="space-y-6 text-center">
            <div className="w-20 h-20 mx-auto bg-emerald-500/20 rounded-full flex items-center justify-center">
              <svg className="w-10 h-10 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold">You are all set!</h1>
            <p className="text-[#a1a1aa] max-w-md mx-auto">
              Your profile is complete and your demo has been submitted. Our 21 AI agents are already analyzing your music and audience.
            </p>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 text-left space-y-3">
              <h3 className="font-semibold text-purple-400 mb-3">What happens next</h3>
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-purple-600/20 text-purple-400 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">1</span>
                <p className="text-sm text-[#a1a1aa]"><strong className="text-[#f9fafb]">A&R Review</strong> — Our A&R agent reviews your demo within 24 hours</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-purple-600/20 text-purple-400 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">2</span>
                <p className="text-sm text-[#a1a1aa]"><strong className="text-[#f9fafb]">Growth Report</strong> — Personalized recommendations based on your audience data</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-purple-600/20 text-purple-400 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">3</span>
                <p className="text-sm text-[#a1a1aa]"><strong className="text-[#f9fafb]">Release Pipeline</strong> — Start releasing music to 150+ platforms</p>
              </div>
            </div>
            <div className="flex gap-3 justify-center pt-4">
              <button
                onClick={() => router.push("/dashboard/growth")}
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
              >
                View Growth Report
              </button>
              <button
                onClick={() => router.push("/dashboard")}
                className="border border-[#2a2a3a] hover:bg-[#13131a] text-[#f9fafb] font-semibold px-8 py-3 rounded-lg transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
