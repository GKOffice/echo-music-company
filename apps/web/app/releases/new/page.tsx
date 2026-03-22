"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { API_URL } from "@/lib/config";
import { getToken } from "@/lib/auth";

const STEPS = ["Release Type", "Add Tracks", "Artwork", "Metadata", "Review & Submit"];
const RELEASE_TYPES = [
  { value: "single", label: "Single", desc: "One track" },
  { value: "ep", label: "EP", desc: "2-6 tracks" },
  { value: "album", label: "Album", desc: "7+ tracks" },
];

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" };
}

interface Track {
  id?: string;
  title: string;
  audio_url: string;
  isrc?: string;
}

interface Checklist {
  tracks: boolean;
  artwork: boolean;
  genre: boolean;
  release_date: boolean;
  ready_to_submit: boolean;
}

export default function NewReleasePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Release fields
  const [releaseId, setReleaseId] = useState<string | null>(null);
  const [releaseType, setReleaseType] = useState("single");
  const [title, setTitle] = useState("");
  const [tracks, setTracks] = useState<Track[]>([]);
  const [newTrackTitle, setNewTrackTitle] = useState("");
  const [newTrackUrl, setNewTrackUrl] = useState("");
  const [artworkUrl, setArtworkUrl] = useState("");
  const [releaseDate, setReleaseDate] = useState("");
  const [genre, setGenre] = useState("");
  const [credits, setCredits] = useState("");
  const [checklist, setChecklist] = useState<Checklist | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/auth/login?next=/releases/new");
  }, [user, loading, router]);

  async function createRelease() {
    if (!title) { setError("Title is required"); return; }
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/create`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title, type: releaseType }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to create release");
      const data = await res.json();
      setReleaseId(data.release_id);
      setStep(1);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function addTrack() {
    if (!newTrackTitle) { setError("Track title is required"); return; }
    if (!releaseId) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${releaseId}/tracks`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ title: newTrackTitle, audio_url: newTrackUrl || null }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to add track");
      const data = await res.json();
      setTracks([...tracks, { id: data.track_id, title: newTrackTitle, audio_url: newTrackUrl, isrc: data.isrc }]);
      setNewTrackTitle("");
      setNewTrackUrl("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function saveArtwork() {
    if (!releaseId || !artworkUrl) { setError("Cover art URL is required"); return; }
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${releaseId}/artwork`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ artwork_url: artworkUrl }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to save artwork");
      setStep(3);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function saveMetadata() {
    if (!releaseId) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${releaseId}/metadata`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          release_date: releaseDate || null,
          genre: genre || null,
          description: null,
          credits: credits || null,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to save metadata");
      await loadChecklist();
      setStep(4);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function loadChecklist() {
    if (!releaseId) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${releaseId}/checklist`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setChecklist(data.checklist);
      }
    } catch {}
  }

  async function submitRelease() {
    if (!releaseId) return;
    setSaving(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${releaseId}/submit`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to submit");
      router.push("/dashboard");
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
        <div className="h-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>

      <div className="max-w-2xl mx-auto px-4 pt-20 pb-16">
        {/* Step indicators */}
        <div className="flex items-center justify-center gap-1 mb-12 flex-wrap">
          {STEPS.map((label, i) => (
            <button
              key={label}
              onClick={() => i < step && setStep(i)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs transition-all ${
                i === step
                  ? "bg-purple-600/20 text-purple-400 border border-purple-500/30"
                  : i < step
                  ? "bg-emerald-600/20 text-emerald-400 cursor-pointer"
                  : "bg-[#13131a] text-[#52525b]"
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                i < step ? "bg-emerald-500 text-white" : i === step ? "bg-purple-600 text-white" : "bg-[#1a1a2e] text-[#52525b]"
              }`}>
                {i < step ? "\u2713" : i + 1}
              </span>
              <span className="hidden md:inline">{label}</span>
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Release Type + Title */}
        {step === 0 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">New Release</h1>
              <p className="text-[#a1a1aa]">Choose the release type and give it a title.</p>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {RELEASE_TYPES.map((rt) => (
                <button
                  key={rt.value}
                  onClick={() => setReleaseType(rt.value)}
                  className={`p-4 rounded-xl border text-center transition-all ${
                    releaseType === rt.value
                      ? "border-purple-500 bg-purple-600/10"
                      : "border-[#2a2a3a] bg-[#13131a] hover:border-[#3a3a4a]"
                  }`}
                >
                  <p className="font-semibold">{rt.label}</p>
                  <p className="text-xs text-[#a1a1aa] mt-1">{rt.desc}</p>
                </button>
              ))}
            </div>
            <div>
              <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Release Title</label>
              <input
                type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                placeholder="My New Release"
              />
            </div>
            <button
              onClick={createRelease} disabled={saving || !title}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              {saving ? "Creating..." : "Continue"}
            </button>
          </div>
        )}

        {/* Step 2: Add Tracks */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Add Tracks</h1>
              <p className="text-[#a1a1aa]">Add tracks to your {releaseType}. Each track gets an auto-generated ISRC code.</p>
            </div>

            {/* Existing tracks */}
            {tracks.length > 0 && (
              <div className="space-y-2">
                {tracks.map((t, i) => (
                  <div key={t.id || i} className="flex items-center gap-3 bg-[#13131a] border border-[#2a2a3a] rounded-lg p-3">
                    <span className="w-8 h-8 rounded-full bg-purple-600/20 text-purple-400 flex items-center justify-center text-sm font-bold">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{t.title}</p>
                      {t.isrc && <p className="text-xs text-[#52525b]">ISRC: {t.isrc}</p>}
                    </div>
                    <span className="text-emerald-400 text-sm">Added</span>
                  </div>
                ))}
              </div>
            )}

            {/* Add new track form */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 space-y-3">
              <input
                type="text" value={newTrackTitle} onChange={(e) => setNewTrackTitle(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-4 py-2.5 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                placeholder="Track title"
              />
              <input
                type="url" value={newTrackUrl} onChange={(e) => setNewTrackUrl(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-4 py-2.5 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                placeholder="Audio URL (optional)"
              />
              <button
                onClick={addTrack} disabled={saving || !newTrackTitle}
                className="w-full bg-[#2a2a3a] hover:bg-[#3a3a4a] disabled:opacity-50 text-[#f9fafb] font-medium py-2.5 rounded-lg transition-colors"
              >
                {saving ? "Adding..." : "+ Add Track"}
              </button>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setStep(0)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={() => setStep(2)} disabled={tracks.length === 0}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Artwork */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Cover Artwork</h1>
              <p className="text-[#a1a1aa]">Set the cover art for your release. Recommended: 3000x3000 JPEG or PNG.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Artwork URL</label>
              <input
                type="url" value={artworkUrl} onChange={(e) => setArtworkUrl(e.target.value)}
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors"
                placeholder="https://..."
              />
            </div>
            {artworkUrl && (
              <div className="flex justify-center">
                <div className="w-48 h-48 rounded-xl border border-[#2a2a3a] overflow-hidden bg-[#13131a]">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={artworkUrl} alt="Cover art preview" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                </div>
              </div>
            )}
            <div className="flex gap-3">
              <button onClick={() => setStep(1)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={saveArtwork} disabled={saving || !artworkUrl}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {saving ? "Saving..." : "Continue"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Metadata */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Release Details</h1>
              <p className="text-[#a1a1aa]">Set the release date, genre, and credits.</p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Release Date</label>
                <input
                  type="date" value={releaseDate} onChange={(e) => setReleaseDate(e.target.value)}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] focus:outline-none focus:border-purple-500 transition-colors"
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
                <label className="block text-sm font-medium text-[#a1a1aa] mb-1">Credits</label>
                <textarea
                  value={credits} onChange={(e) => setCredits(e.target.value)} rows={3}
                  className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder-[#52525b] focus:outline-none focus:border-purple-500 transition-colors resize-none"
                  placeholder="Producer, mixing engineer, features..."
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setStep(2)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={saveMetadata} disabled={saving}
                className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {saving ? "Saving..." : "Review Release"}
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Review & Submit */}
        {step === 4 && (
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Review & Submit</h1>
              <p className="text-[#a1a1aa]">Review your release details before submitting for distribution.</p>
            </div>

            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 space-y-4">
              <div className="flex items-start gap-4">
                {artworkUrl && (
                  <div className="w-24 h-24 rounded-lg overflow-hidden bg-[#0a0a0f] shrink-0">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={artworkUrl} alt="Cover" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                  </div>
                )}
                <div>
                  <h2 className="text-xl font-bold">{title}</h2>
                  <p className="text-sm text-[#a1a1aa] capitalize">{releaseType} &middot; {tracks.length} track{tracks.length !== 1 ? "s" : ""}</p>
                  {genre && <p className="text-sm text-purple-400 capitalize mt-1">{genre}</p>}
                  {releaseDate && <p className="text-sm text-[#52525b] mt-1">Release: {releaseDate}</p>}
                </div>
              </div>

              <hr className="border-[#2a2a3a]" />

              <div>
                <h3 className="text-sm font-medium text-[#a1a1aa] mb-2">Tracks</h3>
                {tracks.map((t, i) => (
                  <div key={t.id || i} className="flex items-center gap-2 py-1">
                    <span className="text-[#52525b] text-sm w-6">{i + 1}.</span>
                    <span className="flex-1">{t.title}</span>
                    <span className="text-xs text-[#52525b]">{t.isrc}</span>
                  </div>
                ))}
              </div>

              {checklist && (
                <>
                  <hr className="border-[#2a2a3a]" />
                  <div>
                    <h3 className="text-sm font-medium text-[#a1a1aa] mb-2">Checklist</h3>
                    {Object.entries(checklist).filter(([k]) => k !== "ready_to_submit").map(([key, done]) => (
                      <div key={key} className="flex items-center gap-2 py-1">
                        <span className={done ? "text-emerald-400" : "text-red-400"}>{done ? "\u2713" : "\u2717"}</span>
                        <span className="capitalize text-sm">{key.replace("_", " ")}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="flex gap-3">
              <button onClick={() => setStep(3)} className="px-6 py-3 border border-[#2a2a3a] rounded-lg text-[#a1a1aa] hover:bg-[#13131a] transition-colors">
                Back
              </button>
              <button
                onClick={submitRelease} disabled={saving || tracks.length === 0}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {saving ? "Submitting..." : "Submit for Distribution"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
