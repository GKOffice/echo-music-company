import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Melodio Points — Own a Piece of the Music",
  description:
    "Buy fractional royalty ownership in rising artists. Earn streaming royalties quarterly. Trade after 12 months. Melodio Points let fans invest in music.",
};

export default function PointsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
