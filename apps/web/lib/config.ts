// Centralized API URL config
// NEXT_PUBLIC_ env vars must be available at build time. When they're not,
// fall back to production URL based on hostname detection.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://api-production-14b6.up.railway.app"
    : "http://localhost:8000");
