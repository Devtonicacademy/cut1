/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-space-grotesk)", "Space Grotesk", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Predictive Sports Intelligence palette
        emerald: {
          50: "#ecfdf5", 100: "#d1fae5", 200: "#a7f3d0", 300: "#6ee7b7",
          400: "#4edea3", 500: "#10b981", 600: "#10b981", 700: "#059669",
          800: "#047857", 900: "#064e3b", 950: "#022c22",
        },
        amber: { 400: "#fbbf24", 500: "#f59e0b", 600: "#f59e0b" },
        blue: { 300: "#adc6ff", 400: "#71a1ff", 500: "#3b82f6", 600: "#3b82f6" },
        gold: { 400: "#fbbf24", 500: "#f59e0b", 600: "#d97706" },
        // Dark surfaces: obsidian canvas, charcoal slate, hover slate
        gray: {
          200: "#e2e8f0", 300: "#cbd5e1", 400: "#94a3b8", 500: "#64748b",
          600: "#475569", 700: "#334155", 800: "#1e293b", 900: "#111827",
        },
        dark: { 900: "#0b0f19", 800: "#111827", 700: "#1e293b", 600: "#334155" },
        surface: { glass: "rgba(17, 24, 39, 0.85)", modal: "rgba(17, 24, 39, 0.95)" },
      },
      borderColor: { glass: "rgba(255, 255, 255, 0.08)" },
      borderRadius: { chip: "0.375rem", panel: "1rem" },
      boxShadow: {
        "glow-emerald": "0 0 20px rgba(16, 185, 129, 0.18)",
        "glow-amber": "0 0 20px rgba(245, 158, 11, 0.18)",
        modal: "0 20px 40px -15px rgba(0, 0, 0, 0.7)",
      },
      backdropBlur: { glass: "16px", modal: "24px" },
      maxWidth: { app: "1440px" },
    },
  },
  plugins: [],
};
