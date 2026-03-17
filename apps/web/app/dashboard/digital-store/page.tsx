"use client";

import Link from "next/link";
import { useState } from "react";
import Navbar from "@/components/Navbar";

const PRODUCT_TYPES = [
  "track_download",
  "stems",
  "sample_pack",
  "beat_license",
  "exclusive_audio",
  "digital_art",
  "video",
  "lyric_sheet",
  "chord_chart",
  "preset_pack",
  "bundle",
];

const LICENSE_TYPES = ["personal", "commercial", "exclusive"];

const TYPE_LABELS: Record<string, string> = {
  track_download: "Track Download",
  stems: "Stems",
  sample_pack: "Sample Pack",
  beat_license: "Beat License",
  exclusive_audio: "Exclusive Audio",
  digital_art: "Digital Art",
  video: "Video",
  lyric_sheet: "Lyric Sheet",
  chord_chart: "Chord Chart",
  preset_pack: "Preset Pack",
  bundle: "Bundle",
};

const TYPE_COLORS: Record<string, string> = {
  track_download: "bg-[#8b5cf6]/20 text-[#8b5cf6]",
  stems: "bg-[#10b981]/20 text-[#10b981]",
  sample_pack: "bg-[#f59e0b]/20 text-[#f59e0b]",
  beat_license: "bg-[#ef4444]/20 text-[#ef4444]",
  exclusive_audio: "bg-[#ec4899]/20 text-[#ec4899]",
  digital_art: "bg-[#06b6d4]/20 text-[#06b6d4]",
  video: "bg-[#8b5cf6]/20 text-[#8b5cf6]",
  lyric_sheet: "bg-[#9ca3af]/20 text-[#9ca3af]",
  chord_chart: "bg-[#9ca3af]/20 text-[#9ca3af]",
  preset_pack: "bg-[#84cc16]/20 text-[#84cc16]",
  bundle: "bg-[#f97316]/20 text-[#f97316]",
};

const MOCK_STATS = {
  totalRevenue: 4820.5,
  unitsSold: 312,
  activeProducts: 7,
  avgOrderValue: 15.45,
};

const MOCK_PRODUCTS = [
  {
    id: "p1",
    title: "Vocal Stems Pack",
    type: "stems",
    price: 29.99,
    units_sold: 87,
    revenue: 2609.13,
    status: "active",
  },
  {
    id: "p2",
    title: "Full Track Download — Midnight Circuit",
    type: "track_download",
    price: 1.99,
    units_sold: 154,
    revenue: 306.46,
    status: "active",
  },
  {
    id: "p3",
    title: "Sample Pack Vol. 1",
    type: "sample_pack",
    price: 49.99,
    units_sold: 38,
    revenue: 1899.62,
    status: "active",
  },
  {
    id: "p4",
    title: "Chord Chart — Bloom EP",
    type: "chord_chart",
    price: 1.99,
    units_sold: 21,
    revenue: 41.79,
    status: "active",
  },
  {
    id: "p5",
    title: "Synth Preset Pack",
    type: "preset_pack",
    price: 24.99,
    units_sold: 12,
    revenue: 299.88,
    status: "draft",
  },
];

const MOCK_SALES = [
  { id: "s1", buyer: "Fan #2847", product: "Vocal Stems Pack", amount: 29.99, date: "2026-03-16" },
  { id: "s2", buyer: "Fan #1103", product: "Full Track Download", amount: 1.99, date: "2026-03-16" },
  { id: "s3", buyer: "Fan #5521", product: "Sample Pack Vol. 1", amount: 49.99, date: "2026-03-15" },
  { id: "s4", buyer: "Fan #0394", product: "Vocal Stems Pack", amount: 29.99, date: "2026-03-15" },
  { id: "s5", buyer: "Fan #7812", product: "Chord Chart — Bloom EP", amount: 1.99, date: "2026-03-14" },
];

interface ProductFormData {
  title: string;
  type: string;
  price: string;
  license_type: string;
  description: string;
}

export default function DigitalStoreDashboard() {
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<ProductFormData>({
    title: "",
    type: "track_download",
    price: "",
    license_type: "personal",
    description: "",
  });

  const handleFormChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      <div className="pt-24 pb-20 px-6 md:px-10">
        <div className="max-w-7xl mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-black">Digital Store</h1>
              <p className="text-[#9ca3af] mt-1">Manage your digital products and track sales</p>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/store"
                className="text-sm text-[#9ca3af] hover:text-[#f9fafb] border border-[#2a2a3a] px-4 py-2 rounded-lg transition-colors"
              >
                View Store →
              </Link>
              <button
                onClick={() => setShowModal(true)}
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors"
              >
                + Add Product
              </button>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              {
                label: "Total Revenue",
                value: `$${MOCK_STATS.totalRevenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}`,
                sub: "after Melodio 15% fee",
                color: "text-[#10b981]",
              },
              {
                label: "Units Sold",
                value: MOCK_STATS.unitsSold.toLocaleString(),
                sub: "all time",
                color: "text-[#8b5cf6]",
              },
              {
                label: "Active Products",
                value: MOCK_STATS.activeProducts,
                sub: "listed in store",
                color: "text-[#f9fafb]",
              },
              {
                label: "Avg Order Value",
                value: `$${MOCK_STATS.avgOrderValue.toFixed(2)}`,
                sub: "per transaction",
                color: "text-[#f59e0b]",
              },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5"
              >
                <p className="text-[#6b7280] text-xs font-medium uppercase tracking-wider mb-1">
                  {stat.label}
                </p>
                <p className={`text-2xl font-black ${stat.color}`}>{stat.value}</p>
                <p className="text-[#4b5563] text-xs mt-1">{stat.sub}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Products Table */}
            <div className="lg:col-span-2 bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-[#2a2a3a] flex items-center justify-between">
                <h2 className="font-bold">My Products</h2>
                <span className="text-[#6b7280] text-sm">{MOCK_PRODUCTS.length} total</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#2a2a3a]">
                      {["Product", "Type", "Price", "Sold", "Revenue", "Status", ""].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-[#6b7280] text-xs font-medium uppercase tracking-wider"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {MOCK_PRODUCTS.map((p) => (
                      <tr
                        key={p.id}
                        className="border-b border-[#1e1e2a] hover:bg-[#1a1a27] transition-colors"
                      >
                        <td className="px-4 py-3 font-medium max-w-[180px]">
                          <span className="truncate block">{p.title}</span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                              TYPE_COLORS[p.type] || "bg-[#2a2a3a] text-[#9ca3af]"
                            }`}
                          >
                            {TYPE_LABELS[p.type] || p.type}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono">${p.price.toFixed(2)}</td>
                        <td className="px-4 py-3 text-[#9ca3af]">{p.units_sold}</td>
                        <td className="px-4 py-3 text-[#10b981] font-medium">
                          ${p.revenue.toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              p.status === "active"
                                ? "bg-[#10b981]/20 text-[#10b981]"
                                : "bg-[#2a2a3a] text-[#6b7280]"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button className="text-xs text-[#8b5cf6] hover:underline">
                              Edit
                            </button>
                            <button className="text-xs text-[#6b7280] hover:text-[#ef4444] transition-colors">
                              Deactivate
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Sales */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-[#2a2a3a]">
                <h2 className="font-bold">Recent Sales</h2>
              </div>
              <div className="divide-y divide-[#1e1e2a]">
                {MOCK_SALES.map((sale) => (
                  <div key={sale.id} className="px-5 py-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-[#8b5cf6] mb-0.5">
                          {sale.buyer}
                        </p>
                        <p className="text-sm font-medium truncate">{sale.product}</p>
                        <p className="text-[#4b5563] text-xs mt-0.5">{sale.date}</p>
                      </div>
                      <span className="text-[#10b981] font-bold text-sm shrink-0">
                        +${sale.amount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-5 py-3 border-t border-[#2a2a3a]">
                <button className="text-sm text-[#8b5cf6] hover:underline w-full text-center">
                  View all sales →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add Product Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4"
          onClick={(e) => e.target === e.currentTarget && setShowModal(false)}
        >
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-6 w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold">New Digital Product</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-[#6b7280] hover:text-[#f9fafb] text-xl leading-none"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#9ca3af] mb-1">Title</label>
                <input
                  name="title"
                  value={form.title}
                  onChange={handleFormChange}
                  placeholder="e.g. Vocal Stems Pack Vol. 2"
                  className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                    Product Type
                  </label>
                  <select
                    name="type"
                    value={form.type}
                    onChange={handleFormChange}
                    className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] transition-colors"
                  >
                    {PRODUCT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {TYPE_LABELS[t]}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                    Price (USD)
                  </label>
                  <input
                    name="price"
                    value={form.price}
                    onChange={handleFormChange}
                    placeholder="29.99"
                    type="number"
                    step="0.01"
                    min="0.99"
                    className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                  License Type
                </label>
                <select
                  name="license_type"
                  value={form.license_type}
                  onChange={handleFormChange}
                  className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] transition-colors"
                >
                  {LICENSE_TYPES.map((lt) => (
                    <option key={lt} value={lt}>
                      {lt.charAt(0).toUpperCase() + lt.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleFormChange}
                  placeholder="Describe what's included..."
                  rows={3}
                  className="w-full bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                    Upload File
                  </label>
                  <div className="w-full bg-[#0a0a0f] border border-dashed border-[#2a2a3a] rounded-lg px-3 py-4 text-center text-[#4b5563] text-sm cursor-pointer hover:border-[#8b5cf6]/50 transition-colors">
                    <span>Drop file or click</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#9ca3af] mb-1">
                    Preview
                  </label>
                  <div className="w-full bg-[#0a0a0f] border border-dashed border-[#2a2a3a] rounded-lg px-3 py-4 text-center text-[#4b5563] text-sm cursor-pointer hover:border-[#8b5cf6]/50 transition-colors">
                    <span>Cover art / clip</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] hover:border-[#8b5cf6]/50 font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
              >
                Create Product
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
