import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Submit Your Demo to Melodio — AI Reviews in 60 Seconds",
  description:
    "Submit your music demo to Melodio. Our A&R Agent reviews every submission with AI — no gatekeepers, no politics. Get feedback within 24 hours.",
};

export default function SubmitLayout({ children }: { children: React.ReactNode }) {
  return children;
}
