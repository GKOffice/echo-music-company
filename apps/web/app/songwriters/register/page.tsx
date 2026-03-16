"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../../components/Navbar";

type Step = 1 | 2 | 3 | 4;

interface CoWriter {
  name: string;
  split: string;
}

interface FormData {
  legalName: string;
  stageName: string;
  email: string;
  pro: string;
  ipi: string;
  songTitle: string;
  coWriters: CoWriter[];
  releaseDate: string;
  isrc: string;
  streamingUrl: string;
  isReleased: boolean;
  syncPitching: boolean;
  sellPoints: boolean;
  pointsQty: number;
  pointsPrice: string;
  acceptCash: boolean;
  acceptPoints: boolean;
  youtubeContentId: boolean;
}

const PROS = ["ASCAP", "BMI", "SESAC", "Not yet a member"];
const STEP_LABELS = ["Your Info", "Your Songs", "Publishing Services", "Review + Submit"];

export default function RegisterPage() {
  const [step, setStep] = useState<Step>(1);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState<FormData>({
    legalName: "",
    stageName: "",
    email: "",
    pro: "",
    ipi: "",
    songTitle: "",
    coWriters: [{ name: "", split: "" }],
    releaseDate: "",
    isrc: "",
    streamingUrl: "",
    isReleased: false,
    syncPitching: false,
    sellPoints: false,
    pointsQty: 10,
    pointsPrice: "",
    acceptCash: true,
    acceptPoints: false,
    youtubeContentId: false,
  });

  function set<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function addCoWriter() {
    setForm((prev) => ({
      ...prev,
      coWriters: [...prev.coWriters, { name: "", split: "" }],
    }));
  }

  function updateCoWriter(idx: number, field: keyof CoWriter, value: string) {
    setForm((prev) => {
      const cw = [...prev.coWriters];
      cw[idx] = { ...cw[idx], [field]: value };
      return { ...prev, coWriters: cw };
    });
  }

  function removeCoWriter(idx: number) {
    setForm((prev) => ({
      ...prev,
      coWriters: prev.coWriters.filter((_, i) => i !== idx),
    }));
  }

  const inputCls =
    "w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-4 py-3 text-[#f9fafb] placeholder:text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all text-sm";

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 pt-28 pb-20">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-black text-[#f9fafb] mb-2">Register Your Songs</h1>
          <p className="text-[#9ca3af] text-sm">
            Get worldwide collection set up in minutes.
          </p>
        </div>

        {submitted ? (
          <div
            className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-10 text-center"
            style={{ boxShadow: "0 0 40px rgba(16,185,129,0.12)" }}
          >
            <div className="text-5xl mb-5">🎵</div>
            <h2 className="text-2xl font-black text-[#f9fafb] mb-3">
              Your songs are registered!
            </h2>
            <p className="text-[#9ca3af] mb-2">
              We&apos;re setting up collection now. Expect your first royalties within 90 days.
            </p>
            <p className="text-sm text-[#9ca3af] mb-8">
              Confirmation sent to{" "}
              <span className="text-[#f9fafb]">{form.email}</span>
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/songwriters"
                className="border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                Back to Songwriter Hub
              </Link>
              <Link
                href="/songwriters/dashboard"
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                View My Dashboard
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Step indicator */}
            <div className="flex items-center gap-2 mb-8">
              {STEP_LABELS.map((label, i) => {
                const s = (i + 1) as Step;
                return (
                  <div key={label} className="flex items-center gap-2 flex-1">
                    <div className="flex flex-col items-center flex-1">
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                          step === s
                            ? "bg-[#8b5cf6] text-white"
                            : step > s
                            ? "bg-[#10b981] text-white"
                            : "bg-[#2a2a3a] text-[#9ca3af]"
                        }`}
                      >
                        {step > s ? "✓" : s}
                      </div>
                      <span
                        className={`text-xs mt-1 whitespace-nowrap hidden sm:block ${
                          step === s ? "text-[#8b5cf6]" : "text-[#9ca3af]"
                        }`}
                      >
                        {label}
                      </span>
                    </div>
                    {i < STEP_LABELS.length - 1 && (
                      <div
                        className={`h-px flex-1 transition-colors ${
                          step > s ? "bg-[#10b981]" : "bg-[#2a2a3a]"
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-8">
              {/* Step 1 — Your Info */}
              {step === 1 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-bold text-[#f9fafb] mb-6">Your Info</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                        Full Legal Name <span className="text-[#ef4444]">*</span>
                      </label>
                      <input
                        value={form.legalName}
                        onChange={(e) => set("legalName", e.target.value)}
                        placeholder="For PRO registration"
                        className={inputCls}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                        Stage / Artist Name
                      </label>
                      <input
                        value={form.stageName}
                        onChange={(e) => set("stageName", e.target.value)}
                        placeholder="Your artist name"
                        className={inputCls}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                      Email <span className="text-[#ef4444]">*</span>
                    </label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => set("email", e.target.value)}
                      placeholder="you@example.com"
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-2">
                      PRO Membership <span className="text-[#ef4444]">*</span>
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {PROS.map((p) => (
                        <button
                          key={p}
                          type="button"
                          onClick={() => set("pro", p)}
                          className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                            form.pro === p
                              ? "border-[#8b5cf6] bg-[#8b5cf6]/10 text-[#8b5cf6]"
                              : "border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50"
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                      IPI/CAE Number{" "}
                      <span className="text-[#9ca3af] text-xs">(optional)</span>
                    </label>
                    <input
                      value={form.ipi}
                      onChange={(e) => set("ipi", e.target.value)}
                      placeholder="11-digit number assigned by your PRO"
                      className={inputCls}
                    />
                    <p className="text-xs text-[#9ca3af] mt-1">
                      Your IPI/CAE is a unique identifier assigned by your performing rights
                      organization. Find it on your PRO account page.
                    </p>
                  </div>
                </div>
              )}

              {/* Step 2 — Your Songs */}
              {step === 2 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-bold text-[#f9fafb] mb-6">Your Songs</h2>
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                      Song Title <span className="text-[#ef4444]">*</span>
                    </label>
                    <input
                      value={form.songTitle}
                      onChange={(e) => set("songTitle", e.target.value)}
                      placeholder="Enter the song title"
                      className={inputCls}
                    />
                  </div>

                  {/* Co-writers */}
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-2">
                      Co-writers{" "}
                      <span className="text-[#9ca3af] text-xs">(optional)</span>
                    </label>
                    <div className="space-y-2">
                      {form.coWriters.map((cw, idx) => (
                        <div key={idx} className="flex gap-2 items-center">
                          <input
                            value={cw.name}
                            onChange={(e) => updateCoWriter(idx, "name", e.target.value)}
                            placeholder="Co-writer name"
                            className={`${inputCls} flex-1`}
                          />
                          <input
                            value={cw.split}
                            onChange={(e) => updateCoWriter(idx, "split", e.target.value)}
                            placeholder="% split"
                            className={`${inputCls} w-24`}
                          />
                          {form.coWriters.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeCoWriter(idx)}
                              className="text-[#9ca3af] hover:text-[#ef4444] transition-colors shrink-0"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={addCoWriter}
                      className="mt-2 text-xs text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
                    >
                      + Add co-writer
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                        Release Date
                      </label>
                      <input
                        type="date"
                        value={form.releaseDate}
                        onChange={(e) => set("releaseDate", e.target.value)}
                        className={inputCls}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                        ISRC{" "}
                        <span className="text-[#9ca3af] text-xs">(optional)</span>
                      </label>
                      <input
                        value={form.isrc}
                        onChange={(e) => set("isrc", e.target.value)}
                        placeholder="e.g. USABC1234567"
                        className={inputCls}
                      />
                    </div>
                  </div>

                  {/* Released toggle */}
                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-2">
                      Is this song released?
                    </label>
                    <div className="flex gap-3">
                      {["Yes", "No"].map((opt) => (
                        <button
                          key={opt}
                          type="button"
                          onClick={() => set("isReleased", opt === "Yes")}
                          className={`px-5 py-2 rounded-lg border text-sm font-medium transition-colors ${
                            (opt === "Yes") === form.isReleased
                              ? "border-[#8b5cf6] bg-[#8b5cf6]/10 text-[#8b5cf6]"
                              : "border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50"
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>

                  {form.isReleased && (
                    <div className="bg-[#10b981]/5 border border-[#10b981]/20 rounded-lg p-4 text-sm text-[#10b981]">
                      ✓ We&apos;ll pull your streaming stats automatically once you provide the URL below.
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                      Spotify / Apple Music URL{" "}
                      <span className="text-[#9ca3af] text-xs">(optional)</span>
                    </label>
                    <input
                      value={form.streamingUrl}
                      onChange={(e) => set("streamingUrl", e.target.value)}
                      placeholder="https://open.spotify.com/track/..."
                      className={inputCls}
                    />
                  </div>
                </div>
              )}

              {/* Step 3 — Publishing Services */}
              {step === 3 && (
                <div className="space-y-5">
                  <h2 className="text-lg font-bold text-[#f9fafb] mb-2">Publishing Services</h2>
                  <p className="text-sm text-[#9ca3af] mb-2">Choose what you need.</p>

                  {/* Always-on */}
                  <div className="flex items-start gap-3 bg-[#10b981]/5 border border-[#10b981]/20 rounded-xl p-5">
                    <div className="w-5 h-5 bg-[#10b981] rounded flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-white text-xs">✓</span>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#f9fafb]">
                        Worldwide Collection
                      </div>
                      <div className="text-xs text-[#9ca3af] mt-0.5">
                        ASCAP/BMI/MLC/SoundExchange + 60 territories — included with every plan
                      </div>
                    </div>
                  </div>

                  {/* Sync Pitching + YouTube toggles */}
                  {[
                    {
                      key: "syncPitching" as const,
                      label: "Sync Pitching",
                      desc: "15% commission — you only pay when placed in film, TV, or ads",
                      icon: "🎬",
                    },
                    {
                      key: "youtubeContentId" as const,
                      label: "YouTube Content ID",
                      desc: "15% of YouTube revenue — we claim your song on all YouTube uploads",
                      icon: "📺",
                    },
                  ].map((service) => (
                    <div
                      key={service.key}
                      className={`flex items-start gap-4 border rounded-xl p-5 cursor-pointer transition-colors ${
                        form[service.key]
                          ? "border-[#8b5cf6]/50 bg-[#8b5cf6]/5"
                          : "border-[#2a2a3a] hover:border-[#8b5cf6]/30"
                      }`}
                      onClick={() => set(service.key, !form[service.key])}
                    >
                      <div
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                          form[service.key]
                            ? "bg-[#8b5cf6] border-[#8b5cf6]"
                            : "border-[#2a2a3a]"
                        }`}
                      >
                        {form[service.key] && <span className="text-white text-xs">✓</span>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span>{service.icon}</span>
                          <span className="text-sm font-semibold text-[#f9fafb]">
                            {service.label}
                          </span>
                        </div>
                        <div className="text-xs text-[#9ca3af] mt-1">{service.desc}</div>
                      </div>
                    </div>
                  ))}

                  {/* Sell Publishing Points */}
                  <div
                    className={`border rounded-xl p-5 cursor-pointer transition-colors ${
                      form.sellPoints
                        ? "border-[#f59e0b]/50 bg-[#f59e0b]/5"
                        : "border-[#2a2a3a] hover:border-[#f59e0b]/30"
                    }`}
                    onClick={() => set("sellPoints", !form.sellPoints)}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                          form.sellPoints ? "bg-[#f59e0b] border-[#f59e0b]" : "border-[#2a2a3a]"
                        }`}
                      >
                        {form.sellPoints && <span className="text-white text-xs">✓</span>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span>💎</span>
                          <span className="text-sm font-semibold text-[#f9fafb]">
                            Sell Publishing Points in Deal Room
                          </span>
                        </div>
                        <div className="text-xs text-[#9ca3af] mt-1">
                          Earn upfront cash by selling fractional publishing rights to fans and
                          creators
                        </div>
                      </div>
                    </div>

                    {form.sellPoints && (
                      <div
                        className="mt-5 pt-5 border-t border-[#2a2a3a] space-y-4"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-[#e8e8f0]">
                              How many points?{" "}
                              <span className="text-[#f59e0b]">{form.pointsQty} pts</span>
                            </label>
                          </div>
                          <input
                            type="range"
                            min={1}
                            max={50}
                            value={form.pointsQty}
                            onChange={(e) => set("pointsQty", parseInt(e.target.value))}
                            className="w-full accent-[#f59e0b]"
                          />
                          <div className="flex justify-between text-xs text-[#9ca3af] mt-1">
                            <span>1 pt</span>
                            <span>50 pts</span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-[#e8e8f0] mb-1.5">
                            Price per point ($)
                          </label>
                          <input
                            value={form.pointsPrice}
                            onChange={(e) => set("pointsPrice", e.target.value)}
                            placeholder="e.g. 100"
                            className={inputCls}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-[#e8e8f0] mb-2">
                            Accept payment via
                          </label>
                          <div className="flex gap-3">
                            {[
                              { key: "acceptCash" as const, label: "Cash" },
                              { key: "acceptPoints" as const, label: "Melodio Points" },
                            ].map((opt) => (
                              <button
                                key={opt.key}
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  set(opt.key, !form[opt.key]);
                                }}
                                className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                                  form[opt.key]
                                    ? "border-[#f59e0b] bg-[#f59e0b]/10 text-[#f59e0b]"
                                    : "border-[#2a2a3a] text-[#9ca3af]"
                                }`}
                              >
                                {opt.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Step 4 — Review + Submit */}
              {step === 4 && (
                <div className="space-y-6">
                  <h2 className="text-lg font-bold text-[#f9fafb] mb-6">Review + Submit</h2>

                  {[
                    {
                      heading: "Your Info",
                      items: [
                        { label: "Name", value: form.legalName || "—" },
                        { label: "Stage name", value: form.stageName || "—" },
                        { label: "Email", value: form.email || "—" },
                        { label: "PRO", value: form.pro || "—" },
                      ],
                    },
                    {
                      heading: "Song",
                      items: [
                        { label: "Title", value: form.songTitle || "—" },
                        {
                          label: "Co-writers",
                          value:
                            form.coWriters
                              .filter((c) => c.name)
                              .map((c) => `${c.name} (${c.split}%)`)
                              .join(", ") || "None",
                        },
                        { label: "Released", value: form.isReleased ? "Yes" : "No" },
                        { label: "ISRC", value: form.isrc || "—" },
                      ],
                    },
                    {
                      heading: "Publishing Services",
                      items: [
                        { label: "Worldwide Collection", value: "✓ Included" },
                        {
                          label: "Sync Pitching",
                          value: form.syncPitching ? "✓ Enabled (15% commission)" : "—",
                        },
                        {
                          label: "YouTube Content ID",
                          value: form.youtubeContentId ? "✓ Enabled (15%)" : "—",
                        },
                        {
                          label: "Publishing Points",
                          value: form.sellPoints
                            ? `${form.pointsQty} points @ $${form.pointsPrice || "?"}/pt`
                            : "—",
                        },
                      ],
                    },
                  ].map((section) => (
                    <div key={section.heading}>
                      <div className="text-xs font-bold text-[#8b5cf6] uppercase tracking-wider mb-3">
                        {section.heading}
                      </div>
                      <div className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl overflow-hidden">
                        {section.items.map((item) => (
                          <div
                            key={item.label}
                            className="flex items-center justify-between px-4 py-3 border-b border-[#2a2a3a] last:border-0"
                          >
                            <span className="text-sm text-[#9ca3af]">{item.label}</span>
                            <span className="text-sm text-[#f9fafb]">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Pricing summary */}
                  <div className="bg-[#8b5cf6]/5 border border-[#8b5cf6]/20 rounded-xl p-4">
                    <div className="text-xs font-bold text-[#8b5cf6] uppercase tracking-wider mb-3">
                      Plan Summary
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-[#9ca3af]">Starter (up to 5 songs)</span>
                      <span className="text-sm font-bold text-[#f9fafb]">Free</span>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-sm text-[#9ca3af]">Admin fee</span>
                      <span className="text-sm text-[#f9fafb]">12%</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setSubmitted(true)}
                    className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-base py-4 rounded-xl transition-colors"
                    style={{ boxShadow: "0 0 20px rgba(139,92,246,0.3)" }}
                  >
                    Register My Songs
                  </button>
                  <p className="text-xs text-center text-[#9ca3af]">
                    By registering you agree to Melodio&apos;s publishing terms. Cancel anytime.
                  </p>

                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    className="w-full border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm py-3 rounded-lg transition-colors"
                  >
                    ← Back to Edit
                  </button>
                </div>
              )}

              {/* Navigation */}
              {step < 4 && (
                <div className="flex gap-3 mt-8">
                  {step > 1 && (
                    <button
                      type="button"
                      onClick={() => setStep((s) => (s - 1) as Step)}
                      className="flex-1 border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm py-3 rounded-lg transition-colors"
                    >
                      Back
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setStep((s) => (s + 1) as Step)}
                    className="flex-1 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm py-3 rounded-lg transition-colors"
                  >
                    {step === 3 ? "Review →" : "Continue →"}
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
