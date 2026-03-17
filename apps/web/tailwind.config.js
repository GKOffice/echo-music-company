/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./contexts/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        surface: "#13131a",
        "surface-2": "#1a1a24",
        border: "#2a2a38",
        primary: {
          DEFAULT: "#8b5cf6",
          hover: "#7c3aed",
          light: "#a78bfa",
        },
        accent: {
          DEFAULT: "#10b981",
          hover: "#059669",
          light: "#34d399",
        },
        muted: "#6b7280",
        "text-primary": "#f9fafb",
        "text-secondary": "#d1d5db",
        "text-muted": "#6b7280",
        danger: "#ef4444",
        warning: "#f59e0b",
        info: "#3b82f6",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-echo":
          "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
        "gradient-dark":
          "linear-gradient(180deg, #0a0a0f 0%, #13131a 100%)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px #8b5cf6, 0 0 10px #8b5cf6" },
          "100%": { boxShadow: "0 0 20px #8b5cf6, 0 0 40px #8b5cf6" },
        },
      },
    },
  },
  plugins: [],
};
