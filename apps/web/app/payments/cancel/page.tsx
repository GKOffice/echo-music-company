"use client";

import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function PaymentCancelPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f] flex flex-col">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4 pt-24 pb-12">
        <div className="w-full max-w-md text-center">
          <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-10">
            <div className="text-6xl mb-5">😔</div>
            <h1 className="text-2xl font-black text-[#f9fafb] mb-3">Purchase Cancelled</h1>
            <p className="text-[#9ca3af] mb-8">
              No worries — your purchase was cancelled and you were not charged. Head back and try again whenever you&apos;re ready.
            </p>
            <div className="space-y-3">
              <Link
                href="/points"
                className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold py-3.5 rounded-xl transition-colors"
              >
                Return to Points Store
              </Link>
              <Link
                href="/"
                className="block w-full text-center border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] font-semibold py-3 rounded-xl transition-colors"
              >
                Go Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
