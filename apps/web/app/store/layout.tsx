import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Melodio Store — Digital Merch & Exclusive Content",
  description:
    "Shop exclusive digital merchandise, stems, sample packs, and beat licenses from Melodio artists. 85% goes directly to the artist.",
};

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  return children;
}
