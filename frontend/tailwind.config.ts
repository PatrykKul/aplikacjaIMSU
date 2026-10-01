import type { Config } from "tailwindcss";

/** Neon Blue / Cyber Blue (EdTech) — primary sky, secondary cyan. */
const config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0ea5e9",
          foreground: "#f0f9ff",
        },
        secondary: {
          DEFAULT: "#06b6d4",
          foreground: "#ecfeff",
        },
      },
      backgroundImage: {
        "glow-purple":
          "radial-gradient(ellipse 90% 70% at 50% -25%, rgba(14,165,233,0.45), transparent 55%)",
        "glow-magenta":
          "radial-gradient(ellipse 55% 45% at 100% 15%, rgba(6,182,212,0.38), transparent 52%)",
        "glow-orchid":
          "radial-gradient(circle at 0% 90%, rgba(56,189,248,0.28), transparent 48%)",
        "grid-faint":
          "linear-gradient(rgba(14,165,233,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(14,165,233,0.07) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "48px 48px",
      },
      boxShadow: {
        neon: "0 0 28px rgba(14, 165, 233, 0.45), 0 0 56px rgba(6, 182, 212, 0.22)",
        "neon-sm": "0 0 18px rgba(14, 165, 233, 0.4)",
        card: "0 25px 50px -12px rgba(0, 0, 0, 0.65)",
      },
    },
  },
} satisfies Config;

export default config;
