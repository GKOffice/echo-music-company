// TODO: Wire Stripe.js — publishable key needed (pk_test_...)
// Payment flow: create-intent → Stripe.js confirmPayment → /payments/confirm
"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { SkeletonCard } from "@/components/Skeleton";
import { fetchDigitalMerch } from "@/lib/api";
import type { MerchItem } from "@/lib/api";

const PRODUCT_TYPES = [
  { label: "All", value: "all" },
  { label: "Downloads", value: "track_download" },
  { label: "Stems", value: "stems" },
  { label: "Sample Packs", value: "sample_pack" },
  { label: "Beat Licenses", value: "beat_license" },
  { label: "Exclusives", value: "exclusive_audio" },
  { label: "Art", value: "digital_art" },
];

const TYPE_COLORS: Record<string, string> = {
  track_download: "bg-[#8b5cf6]/20 text-[#8b5cf6]",
  download: "bg-[#8b5cf6]/20 text-[#8b5cf6]",
  stems: "bg-[#10b981]/20 text-[#10b981]",
  sample_pack: "bg-[#f59e0b]/20 text-[#f59e0b]",
  beat_license: "bg-[#ef4444]/20 text-[#ef4444]",
  exclusive_audio: "bg-[#ec4899]/20 text-[#ec4899]",
  exclusive: "bg-[#ec4899]/20 text-[#ec4899]",
  digital_art: "bg-[#06b6d4]/20 text-[#06b6d4]",
  preset_pack: "bg-[#84cc16]/20 text-[#84cc16]",
  preset: "bg-[#84cc16]/20 text-[#84cc16]",
  bundle: "bg-[#f97316]/20 text-[#f97316]",
};

const TYPE_LABELS: Record<string, string> = {
  track_download: "Download",
  download: "Download",
  stems: "Stems",
  sample_pack: "Sample Pack",
  beat_license: "Beat License",
  exclusive_audio: "Exclusive",
  exclusive: "Exclusive",
  digital_art: "Digital Art",
  preset_pack: "Preset Pack",
  preset: "Preset Pack",
  bundle: "Bundle",
};

// Filter key normalizes MerchItem.type to match PRODUCT_TYPES filter values
function normalizeType(type: string): string {
  const map: Record<string, string> = {
    download: "track_download",
    exclusive: "exclusive_audio",
    preset: "preset_pack",
  };
  return map[type] ?? type;
}

const MOCK_PRODUCTS: MerchItem[] = [
  { id: "1", title: "Vocal Stems Pack", artist: "Nova Vex", type: "stems", price: 29.99, description: "Isolated vocal layers from the debut EP — raw, processed, and harmonies.", artwork: "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400&h=400&fit=crop" },
  { id: "2", title: "Full Track Download — Midnight Circuit", artist: "Lyra Bloom", type: "download", price: 1.99, description: "High-quality WAV + MP3 download with cover art.", artwork: "https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c6e?w=400&h=400&fit=crop" },
  { id: "3", title: "Sample Pack Vol. 1", artist: "Melo Cipher", type: "sample_pack", price: 49.99, description: "80+ loops and one-shots. Hip-hop, trap, and R&B textures.", artwork: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop" },
  { id: "4", title: "Non-Exclusive Beat License", artist: "Cipher Beats", type: "beat_license", price: 49.99, description: "Non-exclusive commercial license. Tagged WAV + MP3 included.", artwork: "https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=400&fit=crop" },
  { id: "5", title: "Unreleased Session — Studio Raw", artist: "Nova Vex", type: "exclusive", price: 14.99, description: "Exclusive studio session audio — never released publicly.", artwork: "https://images.unsplash.com/photo-1453738773917-9c3eff1db985?w=400&h=400&fit=crop" },
  { id: "6", title: "Cover Art Print Pack", artist: "Lyra Bloom", type: "download", price: 9.99, description: "3 high-res album art variants (4000×4000px PNG). Desktop + mobile wallpapers.", artwork: "https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=400&h=400&fit=crop" },
  { id: "7", title: "Synth Preset Pack — Neon Series", artist: "Melo Cipher", type: "preset", price: 24.99, description: "40 Serum presets used across the catalog. Leads, pads, and basses.", artwork: "https://images.unsplash.com/photo-1558865869-c93f6f8482af?w=400&h=400&fit=crop" },
  { id: "8", title: "Ultimate Creator Bundle", artist: "Cipher Beats", type: "bundle", price: 89.99, description: "Stems + Sample Pack + Preset Pack — everything you need. Save 40%.", artwork: "https://images.unsplash.com/photo-1571330735066-03aaa9429d89?w=400&h=400&fit=crop" },
];

const HOW_IT_WORKS = [
  { step: "01", title: "Buy", description: "Checkout securely. Instant access — no waiting.", icon: "💳" },
  { step: "02", title: "Instant Download", description: "Get a private download link immediately after purchase. Valid for 30 days.", icon: "⚡" },
  { step: "03", title: "License Included", description: "Every purchase includes a license key for personal or commercial use.", icon: "📄" },
];

const API_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://api-production-14b6.up.railway.app" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

export default function StorePage() {
  const [selectedProduct, setSelectedProduct] = useState<MerchItem | null>(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [testLoading, setTestLoading] = useState(false);

  const { data: apiProducts, isLoading } = useQuery({
    queryKey: ["digital-merch"],
    queryFn: fetchDigitalMerch,
  });

  // Use API data if returned, else fall back to mock
  const allProducts = apiProducts && apiProducts.length > 0 ? apiProducts : MOCK_PRODUCTS;

  const filtered = allProducts.filter((p) => {
    if (activeFilter === "all") return true;
    return normalizeType(p.type) === activeFilter;
  });

  const handleTestPurchase = async (product: MerchItem) => {
    setTestLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/payments/create-intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_cents: Math.round(product.price * 100),
          currency: "usd",
          product_type: "digital_merch",
          product_id: product.id,
          metadata: { product_title: product.title },
        }),
      });
      const data = await res.json();
      console.log("[Melodio] PaymentIntent client_secret:", data.client_secret);
      console.log("[Melodio] PaymentIntent ID:", data.payment_intent_id);
      alert(`Test intent created!\nPI: ${data.payment_intent_id}\nCheck console for client_secret.`);
    } catch (err) {
      console.error("[Melodio] create-intent error:", err);
      alert("Error creating payment intent — check console.");
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 md:px-10 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#8b5cf6]/5 to-transparent pointer-events-none" />
        <div className="relative max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/30 rounded-full px-4 py-1.5 text-sm text-[#8b5cf6] font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            Artist Store — Live
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight mb-4">
            Artist Store
          </h1>
          <p className="text-2xl font-bold text-[#8b5cf6] mb-4">
            Own the Music. Own the Art.
          </p>
          <p className="text-[#9ca3af] text-lg max-w-2xl mx-auto leading-relaxed">
            Buy directly from artists — downloads, stems, sample packs, beat licenses, and exclusive audio. Every purchase pays the artist 85%. No middlemen.
          </p>
        </div>
      </section>

      {/* Filter Tabs */}
      <section className="px-6 md:px-10 pb-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap gap-2">
            {PRODUCT_TYPES.map((t) => (
              <button
                key={t.value}
                onClick={() => setActiveFilter(t.value)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                  activeFilter === t.value
                    ? "bg-[#8b5cf6] border-[#8b5cf6] text-white"
                    : "bg-transparent border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50 hover:text-[#f9fafb]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Products Grid */}
      <section className="px-6 md:px-10 pb-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">
            {activeFilter === "all" ? "Featured Products" : PRODUCT_TYPES.find(t => t.value === activeFilter)?.label}
            {!isLoading && (
              <span className="ml-3 text-sm font-normal text-[#6b7280]">
                {filtered.length} {filtered.length === 1 ? "item" : "items"}
              </span>
            )}
          </h2>

          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-4xl mb-4">🎵</div>
              <div className="text-[#9ca3af] text-lg mb-2">No products in this category yet.</div>
              <button onClick={() => setActiveFilter("all")} className="text-sm text-[#8b5cf6] hover:underline">Show all</button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filtered.map((product, i) => (
                <div
                  key={product.id}
                  className={`bg-[#13131a] border rounded-2xl overflow-hidden group hover:border-[#8b5cf6]/50 transition-all duration-300 ${
                    i === 7 ? "border-[#8b5cf6]/40 ring-1 ring-[#8b5cf6]/20" : "border-[#2a2a3a]"
                  }`}
                >
                  {/* Cover art */}
                  <div className="relative aspect-square overflow-hidden bg-[#1a1a27]">
                    {product.artwork ? (
                      <img
                        src={product.artwork}
                        alt={product.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-6xl">🎵</div>
                    )}
                    {i === 7 && (
                      <div className="absolute top-3 left-3 bg-[#8b5cf6] text-white text-xs font-bold px-2 py-1 rounded-full">
                        Featured
                      </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0f]/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span
                        className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${
                          TYPE_COLORS[product.type] || "bg-[#2a2a3a] text-[#9ca3af]"
                        }`}
                      >
                        {TYPE_LABELS[product.type] || product.type}
                      </span>
                    </div>
                    <h3 className="font-bold text-sm leading-snug mb-1 text-[#f9fafb] line-clamp-2">
                      {product.title}
                    </h3>
                    <p className="text-[#8b5cf6] text-xs font-medium mb-2">{product.artist}</p>
                    <p className="text-[#6b7280] text-xs leading-relaxed line-clamp-2 mb-4">
                      {product.description}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-[#f9fafb] font-black text-lg">
                        ${product.price.toFixed(2)}
                      </span>
                      <button
                        onClick={() => setSelectedProduct(product)}
                        className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors"
                      >
                        Buy Now
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* How It Works */}
      <section className="px-6 md:px-10 py-20 bg-[#13131a] border-y border-[#2a2a3a]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((step) => (
              <div key={step.step} className="text-center">
                <div className="text-4xl mb-4">{step.icon}</div>
                <div className="text-[#8b5cf6] font-black text-sm tracking-widest mb-2">
                  STEP {step.step}
                </div>
                <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                <p className="text-[#9ca3af] text-sm leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>

          {/* Trust indicators */}
          <div className="mt-12 flex flex-wrap justify-center gap-6 text-sm text-[#6b7280]">
            <span className="flex items-center gap-2"><span className="text-[#10b981]">✓</span> 85% goes to artists</span>
            <span className="flex items-center gap-2"><span className="text-[#10b981]">✓</span> Instant download after payment</span>
            <span className="flex items-center gap-2"><span className="text-[#10b981]">✓</span> License key included</span>
            <span className="flex items-center gap-2"><span className="text-[#10b981]">✓</span> Secure token-based delivery</span>
          </div>
        </div>
      </section>

      {/* Artist CTA */}
      <section className="px-6 md:px-10 py-24 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Sell Your Music Directly</h2>
          <p className="text-[#9ca3af] mb-8 leading-relaxed">
            List your stems, samples, beats, and exclusives. Keep 85% of every sale. No approval needed — go live instantly.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-[#10b981] hover:bg-[#059669] text-white font-bold px-8 py-4 rounded-xl text-lg transition-colors"
          >
            Open Your Store <span>→</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 md:px-10 py-8 border-t border-[#2a2a3a] text-center text-[#4b5563] text-sm">
        <p>© 2026 Melodio — melodio.io</p>
      </footer>

      {/* Purchase Modal */}
      {selectedProduct && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
          onClick={(e) => e.target === e.currentTarget && setSelectedProduct(null)}
        >
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold">Complete Purchase</h3>
              <button
                onClick={() => setSelectedProduct(null)}
                className="text-[#6b7280] hover:text-[#f9fafb] text-xl leading-none"
              >
                ×
              </button>
            </div>

            {/* Product summary */}
            <div className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-xl mb-5">
              {selectedProduct.artwork ? (
                <img src={selectedProduct.artwork} alt={selectedProduct.title} className="w-16 h-16 rounded-lg object-cover shrink-0" />
              ) : (
                <div className="w-16 h-16 rounded-lg bg-[#2a2a3a] flex items-center justify-center text-2xl shrink-0">🎵</div>
              )}
              <div className="min-w-0">
                <p className="font-bold text-sm leading-snug truncate">{selectedProduct.title}</p>
                <p className="text-[#8b5cf6] text-xs mt-0.5">{selectedProduct.artist}</p>
                <p className="text-[#10b981] font-black text-lg mt-1">${selectedProduct.price.toFixed(2)}</p>
              </div>
            </div>

            <div className="space-y-3">
              {/* Pay with Card — disabled until Stripe.js is wired */}
              <div className="relative group">
                <button
                  disabled
                  className="w-full bg-[#8b5cf6]/30 text-[#8b5cf6]/60 font-semibold py-3 rounded-xl text-sm cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  Pay with Card
                </button>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-[#2a2a3a] text-[#9ca3af] text-xs rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  Enter card details — Stripe.js pending publishable key
                </div>
              </div>

              {/* Test Purchase */}
              <button
                onClick={() => handleTestPurchase(selectedProduct)}
                disabled={testLoading}
                className="w-full bg-[#10b981] hover:bg-[#059669] disabled:bg-[#10b981]/40 text-white font-semibold py-3 rounded-xl text-sm transition-colors flex items-center justify-center gap-2"
              >
                {testLoading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating intent...
                  </>
                ) : (
                  "Test Purchase (dev)"
                )}
              </button>
            </div>

            <p className="text-center text-[#4b5563] text-xs mt-4 flex items-center justify-center gap-1.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Secure payments powered by Stripe
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
