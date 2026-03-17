"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchNotifications, markAllNotificationsRead, type AppNotification } from "@/lib/api";

const navLinks = [
  { label: "Home", href: "/" },
  { label: "Discover", href: "/discover" },
  { label: "Points", href: "/points" },
  { label: "Store", href: "/store" },
  { label: "Deal Room", href: "/dealroom" },
  { label: "For Artists", href: "/submit" },
  { label: "Songwriters", href: "/songwriters" },
  { label: "Intelligence", href: "/intelligence" },
  { label: "How It Works", href: "/how-it-works" },
];

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function notifIcon(type: AppNotification["type"]) {
  if (type === "royalty_payout") return "💰";
  if (type === "new_release") return "🎵";
  if (type === "point_price_change") return "📊";
  return "📢";
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const qc = useQueryClient();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [bellOpen, setBellOpen] = useState(false);
  const [localRead, setLocalRead] = useState<Set<string>>(new Set());

  const dropdownRef = useRef<HTMLDivElement>(null);
  const bellRef = useRef<HTMLDivElement>(null);

  const { data: notifications = [] } = useQuery<AppNotification[]>({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
    enabled: !!user,
    staleTime: 30_000,
  });

  const markReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      setLocalRead(new Set(notifications.map((n) => n.id)));
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const unreadCount = notifications.filter((n) => !n.read && !localRead.has(n.id)).length;
  const recentNotifs = notifications.slice(0, 5);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
      if (bellRef.current && !bellRef.current.contains(e.target as Node)) {
        setBellOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleLogout() {
    logout();
    setDropdownOpen(false);
    router.push("/");
  }

  const userInitial = user?.name?.[0]?.toUpperCase() ?? "?";

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-xl border-b border-border">
        <div className="flex items-center justify-between px-4 md:px-10 py-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0" onClick={() => setMobileOpen(false)}>
            <span className="text-[#8b5cf6] font-black text-xl tracking-tight">🎵 Melodio</span>
          </Link>

          {/* Center links — desktop */}
          <div className="hidden md:flex items-center gap-6 lg:gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors duration-200 ${
                  pathname === link.href
                    ? "text-[#8b5cf6]"
                    : "text-text-muted hover:text-text-primary"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right — desktop */}
          <div className="hidden md:flex items-center gap-2">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="w-9 h-9 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-all"
            >
              {theme === "dark" ? (
                // Sun icon
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5"/>
                  <line x1="12" y1="1" x2="12" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="23"/>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                  <line x1="1" y1="12" x2="3" y2="12"/>
                  <line x1="21" y1="12" x2="23" y2="12"/>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
              ) : (
                // Moon icon
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
              )}
            </button>

            {/* Notification Bell — only when logged in */}
            {user && (
              <div className="relative" ref={bellRef}>
                <button
                  onClick={() => { setBellOpen((v) => !v); setDropdownOpen(false); }}
                  aria-label="Notifications"
                  className="relative w-9 h-9 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-all"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                  </svg>
                  {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#8b5cf6] text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </button>

                {bellOpen && (
                  <div className="absolute right-0 top-12 w-80 bg-surface border border-border rounded-xl shadow-2xl overflow-hidden z-50">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                      <span className="text-sm font-semibold text-text-primary">Notifications</span>
                      <button
                        onClick={() => markReadMutation.mutate()}
                        className="text-xs text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
                      >
                        Mark all read
                      </button>
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {recentNotifs.length === 0 ? (
                        <div className="px-4 py-6 text-center text-sm text-text-muted">No notifications</div>
                      ) : (
                        recentNotifs.map((n) => {
                          const isUnread = !n.read && !localRead.has(n.id);
                          return (
                            <div
                              key={n.id}
                              className={`px-4 py-3 border-b border-border last:border-0 transition-colors ${
                                isUnread ? "bg-[#8b5cf6]/5 border-l-2 border-l-[#8b5cf6]" : ""
                              }`}
                            >
                              <div className="flex gap-3">
                                <span className="text-lg shrink-0 mt-0.5">{notifIcon(n.type)}</span>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between gap-2">
                                    <p className="text-xs font-semibold text-text-primary leading-snug">{n.title}</p>
                                    {isUnread && <span className="w-2 h-2 bg-[#8b5cf6] rounded-full shrink-0 mt-1" />}
                                  </div>
                                  <p className="text-xs text-text-muted mt-0.5 leading-snug line-clamp-2">{n.description}</p>
                                  <p className="text-[10px] text-text-muted mt-1">{timeAgo(n.time)}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                    <div className="px-4 py-2.5 border-t border-border bg-surface-2">
                      <Link
                        href="/notifications"
                        onClick={() => setBellOpen(false)}
                        className="block text-center text-xs text-[#8b5cf6] hover:text-[#a78bfa] transition-colors font-medium"
                      >
                        See all notifications →
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}

            {!loading && !user ? (
              <>
                <Link
                  href="/auth/login"
                  className="text-sm font-medium text-text-muted hover:text-text-primary transition-colors ml-1"
                >
                  Sign In
                </Link>
                <Link
                  href="/submit"
                  className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors duration-200"
                >
                  Submit Demo
                </Link>
              </>
            ) : !loading && user ? (
              <div className="relative ml-1" ref={dropdownRef}>
                <button
                  onClick={() => { setDropdownOpen((v) => !v); setBellOpen(false); }}
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                  <div className="w-8 h-8 rounded-full bg-[#8b5cf6] flex items-center justify-center text-white font-bold text-sm">
                    {userInitial}
                  </div>
                  <span className="text-sm text-text-primary hidden lg:block">{user.name}</span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className={`text-text-muted transition-transform ${dropdownOpen ? "rotate-180" : ""}`}>
                    <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                {dropdownOpen && (
                  <div className="absolute right-0 top-12 w-52 bg-surface border border-border rounded-xl shadow-xl overflow-hidden z-50">
                    <div className="px-4 py-3 border-b border-border">
                      <div className="text-sm font-semibold text-text-primary truncate">{user.name}</div>
                      <div className="text-xs text-text-muted truncate">{user.email}</div>
                    </div>
                    {[
                      { label: "Dashboard", href: "/dashboard" },
                      { label: "Fan Dashboard", href: "/fan/dashboard" },
                      { label: "Notifications", href: "/notifications" },
                      { label: "Settings", href: "/settings/notifications" },
                    ].map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setDropdownOpen(false)}
                        className="flex items-center px-4 py-2.5 text-sm text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
                      >
                        {item.label}
                      </Link>
                    ))}
                    <div className="border-t border-border">
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2.5 text-sm text-[#ef4444] hover:bg-surface-2 transition-colors"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Mobile right: theme toggle + hamburger */}
          <div className="md:hidden flex items-center gap-1">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="w-9 h-9 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary transition-all"
            >
              {theme === "dark" ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5"/>
                  <line x1="12" y1="1" x2="12" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="23"/>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                  <line x1="1" y1="12" x2="3" y2="12"/>
                  <line x1="21" y1="12" x2="23" y2="12"/>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
              )}
            </button>
            <button
              className="flex flex-col gap-1.5 p-2"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <span className={`block w-5 h-0.5 bg-text-primary transition-all duration-200 ${mobileOpen ? "rotate-45 translate-y-2" : ""}`} />
              <span className={`block w-5 h-0.5 bg-text-primary transition-all duration-200 ${mobileOpen ? "opacity-0" : ""}`} />
              <span className={`block w-5 h-0.5 bg-text-primary transition-all duration-200 ${mobileOpen ? "-rotate-45 -translate-y-2" : ""}`} />
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-border bg-background px-4 py-4 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  pathname === link.href
                    ? "bg-[#8b5cf6]/20 text-[#8b5cf6]"
                    : "text-text-muted hover:text-text-primary hover:bg-surface"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-3 border-t border-border space-y-2">
              {!loading && !user ? (
                <>
                  <Link
                    href="/auth/login"
                    onClick={() => setMobileOpen(false)}
                    className="block w-full text-center border border-border text-text-muted hover:text-text-primary font-semibold text-sm px-4 py-3 rounded-lg transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/submit"
                    onClick={() => setMobileOpen(false)}
                    className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-3 rounded-lg transition-colors"
                  >
                    Submit Demo
                  </Link>
                </>
              ) : user ? (
                <>
                  <div className="px-4 py-2 text-sm text-text-muted">
                    Signed in as <span className="text-text-primary">{user.name}</span>
                  </div>
                  <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="block px-4 py-3 text-sm text-text-muted hover:text-text-primary hover:bg-surface rounded-lg transition-colors">Dashboard</Link>
                  <Link href="/fan/dashboard" onClick={() => setMobileOpen(false)} className="block px-4 py-3 text-sm text-text-muted hover:text-text-primary hover:bg-surface rounded-lg transition-colors">Fan Dashboard</Link>
                  <Link href="/notifications" onClick={() => setMobileOpen(false)} className="block px-4 py-3 text-sm text-text-muted hover:text-text-primary hover:bg-surface rounded-lg transition-colors">
                    Notifications {unreadCount > 0 && <span className="ml-1 bg-[#8b5cf6] text-white text-[10px] px-1.5 py-0.5 rounded-full">{unreadCount}</span>}
                  </Link>
                  <button onClick={() => { handleLogout(); setMobileOpen(false); }} className="block w-full text-left px-4 py-3 text-sm text-[#ef4444] hover:bg-surface rounded-lg transition-colors">Sign Out</button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
