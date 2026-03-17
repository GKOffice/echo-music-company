"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import { updateNotificationPrefs } from "@/lib/api";

interface Pref { key: string; label: string; desc: string; default: boolean }

const PREFS: Pref[] = [
  { key: "signup_confirmation", label: "Account activity", desc: "Sign-in alerts, password changes, security notices", default: true },
  { key: "purchase_receipts", label: "Purchase receipts", desc: "Confirmation when you buy Melodio Points or merchandise", default: true },
  { key: "royalty_payouts", label: "Royalty payouts", desc: "Notification when monthly royalties are distributed to your account", default: true },
  { key: "new_releases", label: "New releases", desc: "Artists you follow drop new music or point offerings", default: true },
  { key: "deal_room", label: "Deal Room activity", desc: "New bids, accepted offers, and expiring listings", default: false },
  { key: "marketing", label: "Marketing & promotions", desc: "Platform news, feature announcements, and special offers", default: false },
  { key: "weekly_digest", label: "Weekly digest", desc: "Top trending artists and your earnings summary every Monday", default: true },
];

export default function NotificationsPage() {
  const [prefs, setPrefs] = useState<Record<string, boolean>>(
    Object.fromEntries(PREFS.map((p) => [p.key, p.default]))
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggle(key: string) {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaved(false);
  }

  async function handleSave() {
    setSaving(true);
    await updateNotificationPrefs(prefs);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 pt-28 pb-16">
        {/* Header */}
        <div className="mb-10">
          <h1 className="text-3xl font-black text-[#f9fafb] mb-2">Notification Settings</h1>
          <p className="text-[#9ca3af]">Choose what Melodio sends you and when.</p>
        </div>

        {/* Preferences */}
        <div className="space-y-3">
          {PREFS.map((pref) => (
            <div
              key={pref.key}
              className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-5 flex items-center justify-between gap-4"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-[#f9fafb]">{pref.label}</div>
                <div className="text-xs text-[#9ca3af] mt-0.5">{pref.desc}</div>
              </div>
              {/* Toggle switch */}
              <button
                onClick={() => toggle(pref.key)}
                className={`relative shrink-0 w-11 h-6 rounded-full transition-colors duration-200 focus:outline-none ${
                  prefs[pref.key] ? "bg-[#8b5cf6]" : "bg-[#2a2a3a]"
                }`}
                aria-label={`Toggle ${pref.label}`}
              >
                <span
                  className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-sm transition-transform duration-200 ${
                    prefs[pref.key] ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>

        {/* Save button */}
        <div className="mt-8 flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 text-white font-bold px-8 py-3 rounded-xl transition-colors"
          >
            {saving ? "Saving…" : "Save Preferences"}
          </button>
          {saved && (
            <span className="text-[#10b981] text-sm font-medium flex items-center gap-1.5">
              <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><path d="M3 8l4 4 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              Saved!
            </span>
          )}
        </div>
      </div>
    </main>
  );
}
