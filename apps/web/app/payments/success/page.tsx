"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  color: string;
  size: number;
  rotation: number;
  rotationSpeed: number;
}

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [show, setShow] = useState(false);

  // searchParams used for potential session_id param from Stripe
  void searchParams;

  useEffect(() => {
    setShow(true);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ["#8b5cf6", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#f9fafb"];
    const particles: Particle[] = Array.from({ length: 120 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      vx: (Math.random() - 0.5) * 3,
      vy: Math.random() * 3 + 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 8 + 4,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 5,
    }));

    let animId: number;
    function animate() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let active = false;
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;
        p.vy += 0.05;
        if (p.y < canvas.height + 20) active = true;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.5);
        ctx.restore();
      }
      if (active) animId = requestAnimationFrame(animate);
    }
    animate();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <main className="min-h-screen bg-[#0a0a0f] flex flex-col relative overflow-hidden">
      <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0" />
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4 pt-24 pb-12 relative z-10">
        <div
          className={`w-full max-w-md text-center transition-all duration-700 ${show ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <div className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-10" style={{ boxShadow: "0 0 40px rgba(16,185,129,0.2)" }}>
            <div className="text-6xl mb-5">🎉</div>
            <h1 className="text-3xl font-black text-[#f9fafb] mb-3">Points Secured!</h1>
            <p className="text-[#9ca3af] mb-8">
              Your purchase is confirmed. You now own Melodio Points and will earn royalties every month as streams roll in.
            </p>

            <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-5 mb-8 space-y-3 text-left">
              <div className="flex justify-between text-sm">
                <span className="text-[#9ca3af]">Status</span>
                <span className="text-[#10b981] font-semibold">✓ Confirmed</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#9ca3af]">First payout</span>
                <span className="text-[#f9fafb] font-semibold">Next month</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#9ca3af]">Payout schedule</span>
                <span className="text-[#f9fafb] font-semibold">Monthly, 1st</span>
              </div>
            </div>

            <div className="space-y-3">
              <Link
                href="/dashboard"
                className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold py-3.5 rounded-xl transition-colors"
              >
                Go to Dashboard
              </Link>
              <Link
                href="/points"
                className="block w-full text-center border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] font-semibold py-3 rounded-xl transition-colors"
              >
                Browse More Drops
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
