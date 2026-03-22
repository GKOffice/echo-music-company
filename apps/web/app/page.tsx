"use client";

import { redirect } from "next/navigation";

const COMING_SOON = process.env.NEXT_PUBLIC_COMING_SOON !== "false";

export default function HomePage() {
  if (!COMING_SOON) {
    redirect("/platform");
  }
  return <ComingSoonPage />;
}

function ComingSoonPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#0a0a0a",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <h1
        style={{
          fontSize: "clamp(4rem, 15vw, 12rem)",
          fontWeight: 900,
          letterSpacing: "-0.03em",
          lineHeight: 1,
          margin: 0,
          background: "linear-gradient(135deg, #ffffff 0%, #c4b5fd 40%, #818cf8 70%, #60a5fa 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          filter: "drop-shadow(0 0 80px rgba(139,92,246,0.5))",
          userSelect: "none",
        }}
      >
        Melodio
      </h1>
    </main>
  );
}
