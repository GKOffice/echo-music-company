"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";

const API_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://api-production-14b6.up.railway.app" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

// ─── Types ────────────────────────────────────────────────────────────────────

type NotificationType =
  | "royalty_payout"
  | "new_release"
  | "point_price_change"
  | "system_announcement";

type TabFilter = "all" | "unread" | "royalties" | "releases" | "announcements";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  description: string;
  time: string;
  read: boolean;
}

interface NotificationsData {
  notifications: Notification[];
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_NOTIFICATIONS: Notification[] = [
  { id: "n1", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $124.50 from Nova Vex quarterly royalties.", time: "2026-03-10T14:30:00Z", read: false },
  { id: "n2", type: "new_release", title: "New Release: Dark Matter EP", description: "Nova Vex just dropped 'Dark Matter EP' — available on all streaming platforms.", time: "2026-03-09T10:00:00Z", read: false },
  { id: "n3", type: "point_price_change", title: "Point Value Update", description: "Nova Vex point value increased to $320 (+28% from your purchase price).", time: "2026-03-08T09:15:00Z", read: true },
  { id: "n4", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $67.25 from Lyra Bloom monthly royalties.", time: "2026-03-01T12:00:00Z", read: true },
  { id: "n5", type: "system_announcement", title: "New Feature: Leaderboards", description: "Check out the new Melodio Leaderboards — see top artists and supporters!", time: "2026-02-28T16:00:00Z", read: true },
  { id: "n6", type: "new_release", title: "New Release: Golden Hour", description: "Zara Sol released 'Golden Hour' — now live on Spotify, Apple Music, and more.", time: "2026-02-25T11:30:00Z", read: true },
  { id: "n7", type: "point_price_change", title: "Point Value Update", description: "Lyra Bloom point value increased to $178 (+19% from your purchase price).", time: "2026-02-20T08:00:00Z", read: true },
  { id: "n8", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $45.00 from Melo Cipher royalties.", time: "2026-02-20T07:45:00Z", read: true },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function notificationIcon(type: NotificationType): string {
  switch (type) {
    case "royalty_payout": return "💰";
    case "new_release": return "🎵";
    case "point_price_change": return "📊";
    case "system_announcement": return "📢";
  }
}

function typeColor(type: NotificationType): string {
  switch (type) {
    case "royalty_payout": return "#10b981";
    case "new_release": return "#8b5cf6";
    case "point_price_change": return "#f59e0b";
    case "system_announcement": return "#3b82f6";
  }
}

function timeAgo(isoString: string): string {
  const now = new Date();
  const then = new Date(isoString);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getDateGroup(isoString: string): string {
  const now = new Date();
  const then = new Date(isoString);
  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const thenDate = new Date(then.getFullYear(), then.getMonth(), then.getDate());
  const diffDays = Math.round(
    (nowDate.getTime() - thenDate.getTime()) / (1000 * 60 * 60 * 24)
  );
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return "Earlier";
}

const TAB_FILTERS: {
  key: TabFilter;
  label: string;
  filter: (n: Notification) => boolean;
}[] = [
  { key: "all", label: "All", filter: () => true },
  { key: "unread", label: "Unread", filter: (n) => !n.read },
  { key: "royalties", label: "Royalties", filter: (n) => n.type === "royalty_payout" },
  { key: "releases", label: "Releases", filter: (n) => n.type === "new_release" },
  {
    key: "announcements",
    label: "Announcements",
    filter: (n) =>
      n.type === "system_announcement" || n.type === "point_price_change",
  },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function NotificationsPage() {
  const { user, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<TabFilter>("all");
  const [visibleCount, setVisibleCount] = useState(8);
  const [localRead, setLocalRead] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<NotificationsData>({
    queryKey: ["notifications"],
    enabled: !!user,
    queryFn: async () => {
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
        const res = await fetch(`${API_URL}/api/v1/notifications`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          credentials: "include",
        });
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return { notifications: MOCK_NOTIFICATIONS };
      }
    },
  });

  const markAllMutation = useMutation({
    mutationFn: async () => {
      const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
      await fetch(`${API_URL}/api/v1/notifications/read-all`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
      });
    },
    onSuccess: () => {
      const allIds = notifications.map((n) => n.id);
      setLocalRead(new Set(allIds));
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const rawNotifications = data?.notifications ?? MOCK_NOTIFICATIONS;
  const notifications = rawNotifications.map((n) => ({
    ...n,
    read: n.read || localRead.has(n.id),
  }));

  const tabDef = TAB_FILTERS.find((t) => t.key === activeTab)!;
  const filtered = useMemo(
    () => notifications.filter(tabDef.filter),
    [notifications, activeTab, localRead] // eslint-disable-line
  );
  const visible = filtered.slice(0, visibleCount);
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Group by date
  const groups = useMemo(() => {
    const map: Record<string, Notification[]> = {};
    const order: string[] = [];
    visible.forEach((n) => {
      const g = getDateGroup(n.time);
      if (!map[g]) {
        map[g] = [];
        order.push(g);
      }
      map[g].push(n);
    });
    return order.map((g) => ({ label: g, items: map[g] }));
  }, [visible]);

  // Auth guard
  if (!authLoading && !user) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-4 text-center">
          <div className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-8 max-w-sm w-full">
            <div className="text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-bold text-[#f9fafb] mb-2">Sign in to view notifications</h2>
            <p className="text-[#9ca3af] text-sm mb-6">
              Stay updated on royalty payouts, new releases, and platform announcements.
            </p>
            <Link
              href="/auth/login"
              className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="block mt-3 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
            >
              New to Melodio? Create an account
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-2xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#f9fafb]">Notifications</h1>
            {unreadCount > 0 && (
              <p className="text-sm text-[#9ca3af] mt-1">
                {unreadCount} unread
              </p>
            )}
          </div>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllMutation.mutate()}
              disabled={markAllMutation.isPending}
              className="text-sm font-medium text-[#8b5cf6] hover:text-[#a78bfa] transition-colors disabled:opacity-50"
            >
              {markAllMutation.isPending ? "Marking..." : "Mark all as read"}
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-1 mb-6 bg-[#13131a] border border-[#2a2a38] rounded-xl p-1">
          {TAB_FILTERS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => { setActiveTab(tab.key); setVisibleCount(8); }}
              className={`flex-1 min-w-fit px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-[#8b5cf6] text-white shadow"
                  : "text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#2a2a38]"
              }`}
            >
              {tab.label}
              {tab.key === "unread" && unreadCount > 0 && (
                <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold rounded-full bg-[#8b5cf6] text-white">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notification Groups */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="bg-[#13131a] border border-[#2a2a38] rounded-xl p-4 flex gap-4"
              >
                <Skeleton className="w-10 h-10 rounded-xl shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="text-5xl mb-4">🔔</div>
            <p className="text-[#f9fafb] font-semibold mb-1">No notifications</p>
            <p className="text-sm text-[#6b7280]">
              {activeTab === "unread"
                ? "You're all caught up!"
                : "Nothing to show in this category yet."}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group.label}>
                {/* Date group label */}
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xs font-semibold text-[#6b7280] uppercase tracking-wider">
                    {group.label}
                  </span>
                  <div className="flex-1 h-px bg-[#2a2a38]" />
                </div>

                {/* Notification Items */}
                <div className="space-y-2">
                  {group.items.map((notif) => {
                    const icon = notificationIcon(notif.type);
                    const color = typeColor(notif.type);
                    const isUnread = !notif.read;
                    return (
                      <div
                        key={notif.id}
                        className={`relative flex gap-4 p-4 rounded-xl border transition-colors ${
                          isUnread
                            ? "bg-[#13131a] border-[#8b5cf6]/20 border-l-2 border-l-[#8b5cf6]"
                            : "bg-[#13131a] border-[#2a2a38]"
                        }`}
                      >
                        {/* Icon */}
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
                          style={{ background: color + "15" }}
                        >
                          {icon}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p
                              className={`text-sm font-semibold leading-snug ${
                                isUnread ? "text-[#f9fafb]" : "text-[#d1d5db]"
                              }`}
                            >
                              {notif.title}
                            </p>
                            {isUnread && (
                              <div
                                className="w-2 h-2 rounded-full mt-1 shrink-0"
                                style={{ background: color }}
                              />
                            )}
                          </div>
                          <p className="text-sm text-[#9ca3af] mt-0.5 leading-snug">
                            {notif.description}
                          </p>
                          <p className="text-xs text-[#6b7280] mt-1.5">
                            {timeAgo(notif.time)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Load More */}
            {visibleCount < filtered.length && (
              <div className="text-center pt-2">
                <button
                  onClick={() => setVisibleCount((v) => v + 8)}
                  className="text-sm font-medium text-[#8b5cf6] hover:text-[#a78bfa] bg-[#13131a] border border-[#2a2a38] hover:border-[#8b5cf6]/40 px-6 py-2.5 rounded-xl transition-colors"
                >
                  Load more ({filtered.length - visibleCount} remaining)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
