"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

const navLinks = [
  { label: "Home", href: "/" },
  { label: "Discover", href: "/discover" },
  { label: "Points", href: "/points" },
  { label: "Store", href: "/store" },
  { label: "Deal Room", href: "/dealroom" },
  { label: "For Artists", href: "/submit" },
  { label: "Songwriters", href: "/songwriters" },
  { label: "How It Works", href: "/how-it-works" },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
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
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-[#2a2a3a]">
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
                    : "text-[#9ca3af] hover:text-[#f9fafb]"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right — desktop */}
          <div className="hidden md:flex items-center gap-3">
            {!loading && !user ? (
              <>
                <Link
                  href="/auth/login"
                  className="text-sm font-medium text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
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
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen((v) => !v)}
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                  <div className="w-8 h-8 rounded-full bg-[#8b5cf6] flex items-center justify-center text-white font-bold text-sm">
                    {userInitial}
                  </div>
                  <span className="text-sm text-[#f9fafb] hidden lg:block">{user.name}</span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className={`text-[#9ca3af] transition-transform ${dropdownOpen ? "rotate-180" : ""}`}>
                    <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                {dropdownOpen && (
                  <div className="absolute right-0 top-12 w-52 bg-[#13131a] border border-[#2a2a3a] rounded-xl shadow-xl overflow-hidden z-50">
                    <div className="px-4 py-3 border-b border-[#2a2a3a]">
                      <div className="text-sm font-semibold text-[#f9fafb] truncate">{user.name}</div>
                      <div className="text-xs text-[#9ca3af] truncate">{user.email}</div>
                    </div>
                    {[
                      { label: "Dashboard", href: "/dashboard" },
                      { label: "Settings", href: "/settings/notifications" },
                    ].map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setDropdownOpen(false)}
                        className="flex items-center px-4 py-2.5 text-sm text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#1a1a24] transition-colors"
                      >
                        {item.label}
                      </Link>
                    ))}
                    <div className="border-t border-[#2a2a3a]">
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2.5 text-sm text-[#ef4444] hover:bg-[#1a1a24] transition-colors"
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Hamburger — mobile */}
          <button
            className="md:hidden flex flex-col gap-1.5 p-2"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            <span className={`block w-5 h-0.5 bg-[#f9fafb] transition-all duration-200 ${mobileOpen ? "rotate-45 translate-y-2" : ""}`} />
            <span className={`block w-5 h-0.5 bg-[#f9fafb] transition-all duration-200 ${mobileOpen ? "opacity-0" : ""}`} />
            <span className={`block w-5 h-0.5 bg-[#f9fafb] transition-all duration-200 ${mobileOpen ? "-rotate-45 -translate-y-2" : ""}`} />
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-[#2a2a3a] bg-[#0a0a0f] px-4 py-4 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  pathname === link.href
                    ? "bg-[#8b5cf6]/20 text-[#8b5cf6]"
                    : "text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#13131a]"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-3 border-t border-[#2a2a3a] space-y-2">
              {!loading && !user ? (
                <>
                  <Link
                    href="/auth/login"
                    onClick={() => setMobileOpen(false)}
                    className="block w-full text-center border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-4 py-3 rounded-lg transition-colors"
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
                  <div className="px-4 py-2 text-sm text-[#9ca3af]">
                    Signed in as <span className="text-[#f9fafb]">{user.name}</span>
                  </div>
                  <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="block px-4 py-3 text-sm text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#13131a] rounded-lg transition-colors">Dashboard</Link>
                  <button onClick={() => { handleLogout(); setMobileOpen(false); }} className="block w-full text-left px-4 py-3 text-sm text-[#ef4444] hover:bg-[#13131a] rounded-lg transition-colors">Sign Out</button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
