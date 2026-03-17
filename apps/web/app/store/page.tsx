import Link from "next/link";
import Navbar from "@/components/Navbar";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Artist Store — Digital Downloads, Stems & More",
  description:
    "Buy exclusive music, stems, sample packs, beat licenses, and digital art directly from artists on Melodio.",
};

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
  stems: "bg-[#10b981]/20 text-[#10b981]",
  sample_pack: "bg-[#f59e0b]/20 text-[#f59e0b]",
  beat_license: "bg-[#ef4444]/20 text-[#ef4444]",
  exclusive_audio: "bg-[#ec4899]/20 text-[#ec4899]",
  digital_art: "bg-[#06b6d4]/20 text-[#06b6d4]",
  preset_pack: "bg-[#84cc16]/20 text-[#84cc16]",
  bundle: "bg-[#f97316]/20 text-[#f97316]",
};

const TYPE_LABELS: Record<string, string> = {
  track_download: "Download",
  stems: "Stems",
  sample_pack: "Sample Pack",
  beat_license: "Beat License",
  exclusive_audio: "Exclusive",
  digital_art: "Digital Art",
  preset_pack: "Preset Pack",
  bundle: "Bundle",
};

const MOCK_PRODUCTS = [
  {
    id: "1",
    title: "Vocal Stems Pack",
    artist: "Nova Vex",
    product_type: "stems",
    price: 29.99,
    cover: "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400&h=400&fit=crop",
    preview: "Isolated vocal layers from the debut EP — raw, processed, and harmonies.",
  },
  {
    id: "2",
    title: "Full Track Download — Midnight Circuit",
    artist: "Lyra Bloom",
    product_type: "track_download",
    price: 1.99,
    cover: "https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c6e?w=400&h=400&fit=crop",
    preview: "High-quality WAV + MP3 download with cover art.",
  },
  {
    id: "3",
    title: "Sample Pack Vol. 1",
    artist: "Melo Cipher",
    product_type: "sample_pack",
    price: 49.99,
    cover: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
    preview: "80+ loops and one-shots. Hip-hop, trap, and R&B textures.",
  },
  {
    id: "4",
    title: "Non-Exclusive Beat License",
    artist: "Cipher Beats",
    product_type: "beat_license",
    price: 49.99,
    cover: "https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=400&h=400&fit=crop",
    preview: "Non-exclusive commercial license. Tagged WAV + MP3 included.",
  },
  {
    id: "5",
    title: "Unreleased Session — Studio Raw",
    artist: "Nova Vex",
    product_type: "exclusive_audio",
    price: 14.99,
    cover: "https://images.unsplash.com/photo-1453738773917-9c3eff1db985?w=400&h=400&fit=crop",
    preview: "Exclusive studio session audio — never released publicly.",
  },
  {
    id: "6",
    title: "Cover Art Print Pack",
    artist: "Lyra Bloom",
    product_type: "digital_art",
    price: 9.99,
    cover: "https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=400&h=400&fit=crop",
    preview: "3 high-res album art variants (4000×4000px PNG). Desktop + mobile wallpapers.",
  },
  {
    id: "7",
    title: "Synth Preset Pack — Neon Series",
    artist: "Melo Cipher",
    product_type: "preset_pack",
    price: 24.99,
    cover: "https://images.unsplash.com/photo-1558865869-c93f6f8482af?w=400&h=400&fit=crop",
    preview: "40 Serum presets used across the catalog. Leads, pads, and basses.",
  },
  {
    id: "8",
    title: "Ultimate Creator Bundle",
    artist: "Cipher Beats",
    product_type: "bundle",
    price: 89.99,
    cover: "https://images.unsplash.com/photo-1571330735066-03aaa9429d89?w=400&h=400&fit=crop",
    preview: "Stems + Sample Pack + Preset Pack — everything you need. Save 40%.",
    featured: true,
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Buy",
    description: "Checkout securely. Instant access — no waiting.",
    icon: "💳",
  },
  {
    step: "02",
    title: "Instant Download",
    description: "Get a private download link immediately after purchase. Valid for 30 days.",
    icon: "⚡",
  },
  {
    step: "03",
    title: "License Included",
    description: "Every purchase includes a license key for personal or commercial use.",
    icon: "📄",
  },
];

export default function StorePage() {
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
          <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-4">
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
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                  t.value === "all"
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

      {/* Featured Products Grid */}
      <section className="px-6 md:px-10 pb-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Featured Products</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {MOCK_PRODUCTS.map((product) => (
              <div
                key={product.id}
                className={`bg-[#13131a] border rounded-2xl overflow-hidden group hover:border-[#8b5cf6]/50 transition-all duration-300 ${
                  (product as { featured?: boolean }).featured
                    ? "border-[#8b5cf6]/40 ring-1 ring-[#8b5cf6]/20"
                    : "border-[#2a2a3a]"
                }`}
              >
                {/* Cover art */}
                <div className="relative aspect-square overflow-hidden bg-[#1a1a27]">
                  <img
                    src={product.cover}
                    alt={product.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  {(product as { featured?: boolean }).featured && (
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
                        TYPE_COLORS[product.product_type] || "bg-[#2a2a3a] text-[#9ca3af]"
                      }`}
                    >
                      {TYPE_LABELS[product.product_type] || product.product_type}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm leading-snug mb-1 text-[#f9fafb] line-clamp-2">
                    {product.title}
                  </h3>
                  <p className="text-[#8b5cf6] text-xs font-medium mb-2">{product.artist}</p>
                  <p className="text-[#6b7280] text-xs leading-relaxed line-clamp-2 mb-4">
                    {product.preview}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[#f9fafb] font-black text-lg">
                      ${product.price.toFixed(2)}
                    </span>
                    <button className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors">
                      Buy Now
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
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
            <span className="flex items-center gap-2">
              <span className="text-[#10b981]">✓</span> 85% goes to artists
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[#10b981]">✓</span> Instant download after payment
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[#10b981]">✓</span> License key included
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[#10b981]">✓</span> Secure token-based delivery
            </span>
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
            Open Your Store
            <span>→</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 md:px-10 py-8 border-t border-[#2a2a3a] text-center text-[#4b5563] text-sm">
        <p>© 2026 Melodio — melodio.io</p>
      </footer>
    </div>
  );
}
