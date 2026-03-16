"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../../components/Navbar";

const LISTING_TYPES = [
  {
    key: "sell_master_points",
    icon: "💎",
    label: "Sell Master Points",
    desc: "Sell % of your master recording royalties",
    color: "border-purple-500/40 bg-purple-500/5",
    activeColor: "border-purple-500 bg-purple-500/10",
  },
  {
    key: "sell_publishing_points",
    icon: "📝",
    label: "Sell Publishing Points",
    desc: "Sell % of your composition royalties",
    color: "border-violet-500/40 bg-violet-500/5",
    activeColor: "border-violet-500 bg-violet-500/10",
  },
  {
    key: "seek_cowriter",
    icon: "🎤",
    label: "Seeking Co-writer",
    desc: "Find a songwriter for your next project",
    color: "border-emerald-500/40 bg-emerald-500/5",
    activeColor: "border-emerald-500 bg-emerald-500/10",
  },
  {
    key: "seek_producer",
    icon: "🎹",
    label: "Seeking Producer",
    desc: "Find the right beat or producer",
    color: "border-blue-500/40 bg-blue-500/5",
    activeColor: "border-blue-500 bg-blue-500/10",
  },
  {
    key: "offer_beat",
    icon: "🎵",
    label: "Offering a Beat",
    desc: "List your beat for artists to license",
    color: "border-orange-500/40 bg-orange-500/5",
    activeColor: "border-orange-500 bg-orange-500/10",
  },
];

const CREATOR_TYPES = ["Artist", "Producer", "Songwriter"];

const MODES = [
  { key: "fixed", label: "Fixed Price", desc: "Set a firm asking price" },
  { key: "offer", label: "Open to Offers", desc: "Accept offers from buyers" },
  { key: "auction", label: "Auction", desc: "Time-limited bidding" },
];

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
              i + 1 < current
                ? "bg-[#10b981] text-white"
                : i + 1 === current
                ? "bg-[#8b5cf6] text-white"
                : "bg-[#1e1e2e] text-[#6b7280] border border-[#2a2a3a]"
            }`}
          >
            {i + 1 < current ? "✓" : i + 1}
          </div>
          {i < total - 1 && (
            <div className={`h-0.5 w-8 ${i + 1 < current ? "bg-[#10b981]" : "bg-[#2a2a3a]"}`} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function CreateListingPage() {
  const [step, setStep] = useState(1);
  const [creatorType, setCreatorType] = useState("");
  const [listingType, setListingType] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [mode, setMode] = useState("offer");
  const [reservePrice, setReservePrice] = useState("");
  const [auctionDays, setAuctionDays] = useState("7");
  const [acceptCash, setAcceptCash] = useState(true);
  const [acceptPoints, setAcceptPoints] = useState(false);
  const [isrc, setIsrc] = useState("");
  const [spotifyUrl, setSpotifyUrl] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const isSelling = listingType === "sell_master_points" || listingType === "sell_publishing_points";
  const totalSteps = 5;

  function handleNext() {
    if (step < totalSteps) setStep(step + 1);
  }
  function handleBack() {
    if (step > 1) setStep(step - 1);
  }
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
        <Navbar />
        <div className="max-w-lg mx-auto px-4 pt-28 text-center">
          <div className="text-6xl mb-6">🎉</div>
          <h1 className="text-3xl font-black mb-4">Listing Live!</h1>
          <p className="text-[#9ca3af] mb-8">
            Your Deal Room listing is now active. We&apos;ll notify you when offers come in.
          </p>
          <div className="flex flex-col gap-3">
            <Link
              href="/dealroom"
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold py-3 rounded-xl transition-colors"
            >
              Browse Marketplace
            </Link>
            <button
              onClick={() => { setSubmitted(false); setStep(1); }}
              className="bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:text-white font-semibold py-3 rounded-xl transition-colors"
            >
              Post Another Listing
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      <div className="max-w-2xl mx-auto px-4 pt-24 pb-20">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dealroom" className="text-xs text-[#6b7280] hover:text-[#9ca3af] transition-colors">
            ← Back to Deal Room
          </Link>
          <h1 className="text-2xl font-black mt-3 mb-1">Post a Listing</h1>
          <p className="text-[#6b7280] text-sm">Create your Deal Room listing in a few steps.</p>
        </div>

        <StepIndicator current={step} total={totalSteps} />

        <form onSubmit={handleSubmit}>
          {/* Step 1: Creator type */}
          {step === 1 && (
            <div>
              <h2 className="text-lg font-bold mb-6">I am a...</h2>
              <div className="grid grid-cols-3 gap-3">
                {CREATOR_TYPES.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setCreatorType(t.toLowerCase())}
                    className={`p-5 rounded-xl border text-center font-semibold transition-all ${
                      creatorType === t.toLowerCase()
                        ? "border-[#8b5cf6] bg-[#8b5cf6]/10 text-[#f9fafb]"
                        : "border-[#2a2a3a] bg-[#13131a] text-[#9ca3af] hover:border-[#8b5cf6]/40"
                    }`}
                  >
                    <div className="text-2xl mb-2">
                      {t === "Artist" ? "🎤" : t === "Producer" ? "🎹" : "✍️"}
                    </div>
                    {t}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Listing type */}
          {step === 2 && (
            <div>
              <h2 className="text-lg font-bold mb-6">What are you listing?</h2>
              <div className="flex flex-col gap-3">
                {LISTING_TYPES.map((t) => (
                  <button
                    key={t.key}
                    type="button"
                    onClick={() => setListingType(t.key)}
                    className={`flex items-center gap-4 p-4 rounded-xl border text-left transition-all ${
                      listingType === t.key ? t.activeColor : t.color
                    }`}
                  >
                    <span className="text-2xl shrink-0">{t.icon}</span>
                    <div>
                      <p className={`font-semibold text-sm ${listingType === t.key ? "text-[#f9fafb]" : "text-[#d1d5db]"}`}>
                        {t.label}
                      </p>
                      <p className="text-xs text-[#6b7280] mt-0.5">{t.desc}</p>
                    </div>
                    {listingType === t.key && (
                      <span className="ml-auto text-[#10b981] text-lg">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Track / catalog info */}
          {step === 3 && (
            <div>
              <h2 className="text-lg font-bold mb-6">
                {isSelling ? "Track Details" : "Listing Info"}
              </h2>
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-xs text-[#6b7280] block mb-1.5">Listing Title *</label>
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder={isSelling ? "e.g. 5% Master Points — 'Song Name'" : "Describe what you're looking for"}
                    className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2.5 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#6b7280] block mb-1.5">Description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
                    placeholder="Tell buyers about the opportunity, your goals, and any terms..."
                    className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2.5 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563] resize-none"
                  />
                </div>
                {isSelling && (
                  <>
                    <div className="border-t border-[#2a2a3a] pt-4">
                      <p className="text-xs text-[#6b7280] mb-3">
                        Add an external track (Spotify ISRC) to display streaming stats:
                      </p>
                      <div className="flex flex-col gap-3">
                        <div>
                          <label className="text-xs text-[#6b7280] block mb-1.5">ISRC</label>
                          <input
                            value={isrc}
                            onChange={(e) => setIsrc(e.target.value)}
                            placeholder="e.g. USXYZ2410042"
                            className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2.5 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563] font-mono"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-[#6b7280] block mb-1.5">Spotify URL</label>
                          <input
                            value={spotifyUrl}
                            onChange={(e) => setSpotifyUrl(e.target.value)}
                            placeholder="https://open.spotify.com/track/..."
                            className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2.5 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                          />
                        </div>
                        {(isrc || spotifyUrl) && (
                          <div className="bg-[#10b981]/10 border border-[#10b981]/20 rounded-lg p-3 text-xs text-[#10b981]">
                            ✓ Track data will be fetched and displayed on your listing.
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Step 4: Price and mode */}
          {step === 4 && (
            <div>
              <h2 className="text-lg font-bold mb-6">Pricing & Mode</h2>
              <div className="flex flex-col gap-5">
                {/* Listing mode */}
                <div>
                  <p className="text-xs text-[#6b7280] mb-3">Listing mode</p>
                  <div className="grid grid-cols-3 gap-3">
                    {MODES.map((m) => (
                      <button
                        key={m.key}
                        type="button"
                        onClick={() => setMode(m.key)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          mode === m.key
                            ? "border-[#8b5cf6] bg-[#8b5cf6]/10"
                            : "border-[#2a2a3a] bg-[#13131a] hover:border-[#8b5cf6]/40"
                        }`}
                      >
                        <p className={`text-xs font-bold ${mode === m.key ? "text-[#f9fafb]" : "text-[#d1d5db]"}`}>
                          {m.label}
                        </p>
                        <p className="text-xs text-[#6b7280] mt-1">{m.desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Price */}
                {mode !== "offer" && (
                  <div>
                    <label className="text-xs text-[#6b7280] block mb-1.5">
                      {mode === "auction" ? "Reserve price ($)" : "Asking price ($)"}
                    </label>
                    <input
                      type="number"
                      value={mode === "auction" ? reservePrice : price}
                      onChange={(e) =>
                        mode === "auction" ? setReservePrice(e.target.value) : setPrice(e.target.value)
                      }
                      placeholder="e.g. 5000"
                      className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2.5 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                    />
                  </div>
                )}

                {mode === "auction" && (
                  <div>
                    <label className="text-xs text-[#6b7280] block mb-1.5">Auction duration (days)</label>
                    <div className="flex gap-2">
                      {["3", "7", "14"].map((d) => (
                        <button
                          key={d}
                          type="button"
                          onClick={() => setAuctionDays(d)}
                          className={`flex-1 py-2 rounded-lg border text-sm font-semibold transition-all ${
                            auctionDays === d
                              ? "bg-[#8b5cf6] border-[#8b5cf6] text-white"
                              : "bg-[#13131a] border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/40"
                          }`}
                        >
                          {d} days
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Payment options */}
                <div>
                  <p className="text-xs text-[#6b7280] mb-3">Accept payment via</p>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setAcceptCash(!acceptCash)}
                      className={`flex-1 py-2.5 rounded-lg border text-sm font-semibold transition-all ${
                        acceptCash
                          ? "bg-[#10b981]/10 border-[#10b981]/40 text-[#10b981]"
                          : "bg-[#13131a] border-[#2a2a3a] text-[#9ca3af]"
                      }`}
                    >
                      💵 Cash {acceptCash && "✓"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAcceptPoints(!acceptPoints)}
                      className={`flex-1 py-2.5 rounded-lg border text-sm font-semibold transition-all ${
                        acceptPoints
                          ? "bg-[#8b5cf6]/10 border-[#8b5cf6]/40 text-[#8b5cf6]"
                          : "bg-[#13131a] border-[#2a2a3a] text-[#9ca3af]"
                      }`}
                    >
                      ♦ Points {acceptPoints && "✓"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 5: Preview & Submit */}
          {step === 5 && (
            <div>
              <h2 className="text-lg font-bold mb-6">Preview & Submit</h2>
              <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 flex flex-col gap-3 mb-6">
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full font-semibold">
                    {LISTING_TYPES.find((t) => t.key === listingType)?.label || listingType}
                  </span>
                  <span className="text-xs text-[#6b7280] capitalize">{creatorType}</span>
                </div>
                <h3 className="text-[#f9fafb] font-bold">{title || "(No title)"}</h3>
                {description && <p className="text-[#9ca3af] text-xs">{description}</p>}
                <div className="flex gap-3 text-xs text-[#9ca3af] flex-wrap pt-1">
                  <span className="capitalize">Mode: {mode}</span>
                  {price && <span>Price: ${price}</span>}
                  {mode === "auction" && reservePrice && <span>Reserve: ${reservePrice}</span>}
                  {mode === "auction" && <span>Duration: {auctionDays} days</span>}
                  {acceptCash && <span>Accepts cash</span>}
                  {acceptPoints && <span>Accepts points</span>}
                </div>
                {(isrc || spotifyUrl) && (
                  <div className="text-xs text-[#10b981] bg-[#10b981]/5 border border-[#10b981]/20 rounded px-3 py-2">
                    External track linked: {isrc || spotifyUrl}
                  </div>
                )}
              </div>
              <p className="text-xs text-[#6b7280] mb-4 text-center">
                By submitting, you confirm you own or have rights to list these assets on Melodio.
              </p>
              <button
                type="submit"
                disabled={!creatorType || !listingType || !title}
                className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:bg-[#8b5cf6]/30 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-colors text-sm"
              >
                Post Listing
              </button>
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-3 mt-8">
            {step > 1 && (
              <button
                type="button"
                onClick={handleBack}
                className="flex-1 bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:text-white font-semibold py-2.5 rounded-xl transition-colors"
              >
                Back
              </button>
            )}
            {step < totalSteps && (
              <button
                type="button"
                onClick={handleNext}
                disabled={
                  (step === 1 && !creatorType) ||
                  (step === 2 && !listingType)
                }
                className="flex-1 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:bg-[#8b5cf6]/30 disabled:cursor-not-allowed text-white font-bold py-2.5 rounded-xl transition-colors"
              >
                Continue
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
