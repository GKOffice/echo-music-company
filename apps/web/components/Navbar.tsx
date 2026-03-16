"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navLinks = [
  { label: "Discover", href: "/" },
  { label: "Points Store", href: "/points" },
  { label: "For Artists", href: "/dashboard" },
  { label: "Producers", href: "/#hub" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-10 py-4 bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-[#2a2a3a]">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 shrink-0">
        <span className="text-[#8b5cf6] font-black text-xl tracking-tight">🎵 Melodio</span>
      </Link>

      {/* Center links */}
      <div className="hidden md:flex items-center gap-8">
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

      {/* Right actions */}
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="hidden sm:block text-sm font-medium text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
        >
          Sign In
        </Link>
        <Link
          href="/submit"
          className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors duration-200"
        >
          Submit Demo
        </Link>
      </div>
    </nav>
  );
}
