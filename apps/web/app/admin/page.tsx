"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { API_URL } from "@/lib/config";
import { getToken } from "@/lib/auth";

const AGENTS = [
  "ceo", "ar", "production", "distribution", "marketing", "social", "finance",
  "legal", "analytics", "creative", "sync", "artist_dev", "pr", "comms", "qc",
  "infrastructure", "intake", "merch", "youtube", "hub", "vault",
];

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" };
}

interface Stats {
  total_artists: number;
  total_releases: number;
  total_users: number;
  waitlist_count: number;
  pending_submissions: number;
}

interface Signup {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string | null;
}

interface PendingRelease {
  id: string;
  title: string;
  type: string;
  artist_name: string;
  created_at: string | null;
}

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [signups, setSignups] = useState<Signup[]>([]);
  const [pending, setPending] = useState<PendingRelease[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login?next=/admin");
    }
    if (!loading && user && !["admin", "super_admin", "owner"].includes(user.role)) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  const loadData = useCallback(async () => {
    setDataLoading(true);
    try {
      const [statsRes, signupsRes, pendingRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/admin/stats`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/v1/admin/recent-signups`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/v1/admin/pending`, { headers: authHeaders() }),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (signupsRes.ok) {
        const data = await signupsRes.json();
        setSignups(data.signups || []);
      }
      if (pendingRes.ok) {
        const data = await pendingRes.json();
        setPending(data.pending || []);
      }
    } catch {}
    setDataLoading(false);
  }, []);

  useEffect(() => {
    if (user && ["admin", "super_admin", "owner"].includes(user.role)) {
      loadData();
    }
  }, [user, loadData]);

  async function handleApprove(releaseId: string) {
    setActionLoading(releaseId);
    try {
      await fetch(`${API_URL}/api/v1/admin/approve/${releaseId}`, {
        method: "POST",
        headers: authHeaders(),
      });
      setPending(pending.filter((p) => p.id !== releaseId));
      if (stats) setStats({ ...stats, pending_submissions: stats.pending_submissions - 1 });
    } catch {}
    setActionLoading(null);
  }

  async function handleReject(releaseId: string) {
    setActionLoading(releaseId);
    try {
      await fetch(`${API_URL}/api/v1/admin/reject/${releaseId}`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ reason: "Does not meet quality standards" }),
      });
      setPending(pending.filter((p) => p.id !== releaseId));
      if (stats) setStats({ ...stats, pending_submissions: stats.pending_submissions - 1 });
    } catch {}
    setActionLoading(null);
  }

  async function exportWaitlist() {
    try {
      const res = await fetch(`${API_URL}/api/v1/admin/waitlist`, { headers: authHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      const entries = data.waitlist || [];
      if (entries.length === 0) { alert("Waitlist is empty"); return; }
      const cols = Object.keys(entries[0]);
      const csv = [cols.join(","), ...entries.map((e: Record<string, string>) => cols.map((c) => `"${(e[c] || "").toString().replace(/"/g, '""')}"`).join(","))].join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `melodio-waitlist-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {}
  }

  if (loading || (!user && !loading)) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <p className="text-[#a1a1aa] mt-1">Melodio platform overview</p>
          </div>
          <button
            onClick={exportWaitlist}
            className="px-4 py-2 bg-[#13131a] border border-[#2a2a3a] rounded-lg text-sm hover:bg-[#1a1a2e] transition-colors"
          >
            Export Waitlist CSV
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {[
            { label: "Total Artists", value: stats?.total_artists ?? "—", color: "text-purple-400" },
            { label: "Total Releases", value: stats?.total_releases ?? "—", color: "text-blue-400" },
            { label: "Total Users", value: stats?.total_users ?? "—", color: "text-emerald-400" },
            { label: "Waitlist", value: stats?.waitlist_count ?? "—", color: "text-amber-400" },
            { label: "Pending Review", value: stats?.pending_submissions ?? "—", color: "text-red-400" },
          ].map((card) => (
            <div key={card.label} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <p className="text-sm text-[#a1a1aa] mb-1">{card.label}</p>
              <p className={`text-2xl font-bold ${card.color}`}>{dataLoading ? "..." : card.value}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Recent Signups */}
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Signups</h2>
            {signups.length === 0 && !dataLoading && (
              <p className="text-[#52525b] text-sm">No signups yet</p>
            )}
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {signups.map((s) => (
                <div key={s.id} className="flex items-center justify-between py-2 border-b border-[#1a1a2e] last:border-0">
                  <div>
                    <p className="text-sm font-medium">{s.email || "—"}</p>
                    <p className="text-xs text-[#52525b]">{s.created_at ? new Date(s.created_at).toLocaleDateString() : ""}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    s.role === "artist" ? "bg-purple-600/20 text-purple-400"
                    : s.role === "admin" || s.role === "owner" ? "bg-red-600/20 text-red-400"
                    : "bg-blue-600/20 text-blue-400"
                  }`}>
                    {s.role}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Pending Submissions */}
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Pending Submissions</h2>
            {pending.length === 0 && !dataLoading && (
              <p className="text-[#52525b] text-sm">No pending submissions</p>
            )}
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {pending.map((r) => (
                <div key={r.id} className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg p-3">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium">{r.title}</p>
                      <p className="text-xs text-[#52525b]">{r.artist_name} &middot; {r.type}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(r.id)}
                      disabled={actionLoading === r.id}
                      className="flex-1 py-1.5 bg-emerald-600/20 text-emerald-400 text-sm rounded-lg hover:bg-emerald-600/30 disabled:opacity-50 transition-colors"
                    >
                      {actionLoading === r.id ? "..." : "Approve"}
                    </button>
                    <button
                      onClick={() => handleReject(r.id)}
                      disabled={actionLoading === r.id}
                      className="flex-1 py-1.5 bg-red-600/20 text-red-400 text-sm rounded-lg hover:bg-red-600/30 disabled:opacity-50 transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Agent Status */}
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Agent Status Overview</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {AGENTS.map((agent) => (
              <div key={agent} className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg p-3 text-center">
                <div className="w-2 h-2 rounded-full bg-emerald-400 mx-auto mb-2" />
                <p className="text-xs font-medium capitalize">{agent.replace("_", " ")}</p>
                <p className="text-[10px] text-emerald-400 mt-0.5">Online</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
