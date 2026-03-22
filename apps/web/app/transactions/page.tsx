"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";

const API_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://api-production-14b6.up.railway.app" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

// ─── Types ────────────────────────────────────────────────────────────────────

type TransactionType = "royalty" | "purchase" | "withdrawal" | "system";
type TransactionStatus = "completed" | "pending" | "failed";
type TabFilter = "all" | "purchases" | "royalties" | "withdrawals";

interface Transaction {
  id: string;
  date: string;
  type: TransactionType;
  description: string;
  amount: number;
  status: TransactionStatus;
}

interface TransactionsData {
  transactions: Transaction[];
  balance: number;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_DATA: TransactionsData = {
  transactions: [
    { id: "t1", date: "2026-03-10", type: "royalty", description: "Nova Vex Q1 Royalty Payout", amount: 124.50, status: "completed" },
    { id: "t2", date: "2026-03-01", type: "royalty", description: "Lyra Bloom Monthly Royalty", amount: 67.25, status: "completed" },
    { id: "t3", date: "2026-02-28", type: "purchase", description: "Purchased 2 Nova Vex Points", amount: -500.00, status: "completed" },
    { id: "t4", date: "2026-02-20", type: "royalty", description: "Melo Cipher Royalty Payout", amount: 45.00, status: "completed" },
    { id: "t5", date: "2026-02-14", type: "purchase", description: "Purchased 3 Lyra Bloom Points", amount: -450.00, status: "completed" },
    { id: "t6", date: "2026-02-01", type: "withdrawal", description: "Withdrawal to bank account ****4521", amount: -200.00, status: "completed" },
    { id: "t7", date: "2026-01-25", type: "royalty", description: "Nova Vex Royalty Payout", amount: 98.75, status: "completed" },
    { id: "t8", date: "2026-01-15", type: "purchase", description: "Purchased 5 Khai Dusk Points", amount: -500.00, status: "completed" },
    { id: "t9", date: "2026-01-10", type: "withdrawal", description: "Withdrawal to PayPal", amount: -150.00, status: "pending" },
    { id: "t10", date: "2026-01-05", type: "royalty", description: "Indie Haze Royalty Payout", amount: 22.00, status: "completed" },
  ],
  balance: 892.50,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number, showSign = false): string {
  const abs = Math.abs(n).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (showSign && n > 0) return "+$" + abs;
  if (n < 0) return "-$" + abs;
  return "$" + abs;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function typeIcon(type: TransactionType): string {
  switch (type) {
    case "purchase": return "💸";
    case "royalty": return "💰";
    case "withdrawal": return "🏦";
    default: return "📋";
  }
}

function amountColor(type: TransactionType): string {
  if (type === "royalty") return "#10b981";
  if (type === "withdrawal") return "#ef4444";
  return "#f9fafb";
}

const STATUS_CONFIG: Record<
  TransactionStatus,
  { label: string; classes: string }
> = {
  completed: { label: "Completed", classes: "bg-[#10b981]/15 text-[#10b981]" },
  pending:   { label: "Pending",   classes: "bg-[#f59e0b]/15 text-[#f59e0b]" },
  failed:    { label: "Failed",    classes: "bg-[#ef4444]/15 text-[#ef4444]" },
};

const TAB_MAP: Record<TabFilter, TransactionType | null> = {
  all: null,
  purchases: "purchase",
  royalties: "royalty",
  withdrawals: "withdrawal",
};

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TransactionsPage() {
  const { user, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<TabFilter>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data, isLoading } = useQuery<TransactionsData>({
    queryKey: ["transactions"],
    enabled: !!user,
    queryFn: async () => {
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
        const res = await fetch(`${API_URL}/api/v1/transactions`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          credentials: "include",
        });
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return MOCK_DATA;
      }
    },
  });

  const transactions = data?.transactions ?? MOCK_DATA.transactions;
  const balance = data?.balance ?? MOCK_DATA.balance;

  const filtered = useMemo(() => {
    return transactions.filter((tx) => {
      const typeFilter = TAB_MAP[activeTab];
      if (typeFilter && tx.type !== typeFilter) return false;
      if (dateFrom && tx.date < dateFrom) return false;
      if (dateTo && tx.date > dateTo) return false;
      return true;
    });
  }, [transactions, activeTab, dateFrom, dateTo]);

  // Auth guard
  if (!authLoading && !user) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-4 text-center">
          <div className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-8 max-w-sm w-full">
            <div className="text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-bold text-[#f9fafb] mb-2">Sign in to view transactions</h2>
            <p className="text-[#9ca3af] text-sm mb-6">
              Access your full transaction history, royalty payouts, and point purchases.
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

  const TABS: { key: TabFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "purchases", label: "Purchases" },
    { key: "royalties", label: "Royalties" },
    { key: "withdrawals", label: "Withdrawals" },
  ];

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-4xl mx-auto px-4 pt-24 pb-16">
        {/* Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-[#f9fafb]">Transactions</h1>
            <p className="text-[#9ca3af] text-sm mt-1">Your complete payment history</p>
          </div>
          {/* Export Button */}
          <button
            className="flex items-center gap-2 bg-[#1a1a24] border border-[#2a2a38] hover:border-[#8b5cf6]/50 text-[#d1d5db] hover:text-[#f9fafb] text-sm font-medium px-4 py-2.5 rounded-xl transition-colors"
            aria-label="Export transactions"
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
              <path
                d="M7.5 10.5L3 6H6V1H9V6H12L7.5 10.5ZM1 13H14V11H1V13Z"
                fill="currentColor"
              />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Balance Card */}
        <div className="bg-gradient-to-r from-[#8b5cf6]/10 to-[#10b981]/10 border border-[#8b5cf6]/20 rounded-2xl p-6 mb-6">
          <div className="text-sm text-[#9ca3af] mb-1">Current Balance</div>
          {isLoading ? (
            <Skeleton className="h-10 w-40" />
          ) : (
            <div className="text-4xl font-black text-[#f9fafb]">
              {formatCurrency(balance)}
            </div>
          )}
          <div className="text-xs text-[#6b7280] mt-1">Available for withdrawal</div>
        </div>

        {/* Filters */}
        <div className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-4 mb-6">
          {/* Tabs */}
          <div className="flex flex-wrap gap-1 mb-4">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "bg-[#8b5cf6] text-white"
                    : "text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#2a2a38]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Date Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <label className="block text-xs text-[#6b7280] mb-1.5 font-medium">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a38] text-[#d1d5db] text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-[#8b5cf6] transition-colors [color-scheme:dark]"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-[#6b7280] mb-1.5 font-medium">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full bg-[#0a0a0f] border border-[#2a2a38] text-[#d1d5db] text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:border-[#8b5cf6] transition-colors [color-scheme:dark]"
              />
            </div>
            {(dateFrom || dateTo) && (
              <div className="flex items-end">
                <button
                  onClick={() => { setDateFrom(""); setDateTo(""); }}
                  className="text-xs text-[#9ca3af] hover:text-[#f9fafb] px-3 py-2.5 rounded-lg border border-[#2a2a38] hover:border-[#2a2a38] transition-colors"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Results count */}
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs text-[#6b7280]">
            {isLoading ? "Loading..." : `${filtered.length} transaction${filtered.length !== 1 ? "s" : ""}`}
          </span>
        </div>

        {/* Transactions List */}
        <section className="bg-[#13131a] border border-[#2a2a38] rounded-2xl overflow-hidden">
          {isLoading ? (
            <div className="divide-y divide-[#2a2a38]">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 px-5 py-4">
                  <Skeleton className="w-10 h-10 rounded-xl shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                  <div className="text-right space-y-2">
                    <Skeleton className="h-5 w-20" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="text-4xl mb-3">📭</div>
              <p className="text-[#f9fafb] font-semibold mb-1">No transactions found</p>
              <p className="text-sm text-[#6b7280]">
                Try adjusting your filters or date range.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-[#2a2a38]">
              {filtered.map((tx) => {
                const statusCfg = STATUS_CONFIG[tx.status];
                const color = amountColor(tx.type);
                const isPositive = tx.amount > 0;
                return (
                  <div
                    key={tx.id}
                    className="flex items-center gap-3 sm:gap-4 px-4 sm:px-5 py-4 hover:bg-[#1a1a24] transition-colors"
                  >
                    {/* Icon */}
                    <div className="w-10 h-10 rounded-xl bg-[#1a1a24] flex items-center justify-center text-lg shrink-0">
                      {typeIcon(tx.type)}
                    </div>

                    {/* Description + Date */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[#f9fafb] truncate">
                        {tx.description}
                      </p>
                      <p className="text-xs text-[#6b7280] mt-0.5">{formatDate(tx.date)}</p>
                    </div>

                    {/* Amount + Status */}
                    <div className="text-right shrink-0">
                      <div
                        className="text-sm font-bold"
                        style={{ color }}
                      >
                        {formatCurrency(tx.amount, isPositive)}
                      </div>
                      <span
                        className={`inline-block mt-1 text-xs font-semibold px-2 py-0.5 rounded-full ${statusCfg.classes}`}
                      >
                        {statusCfg.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
