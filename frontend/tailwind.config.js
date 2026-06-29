/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#b7122a",
        "primary-container": "#db313f",
        "on-primary": "#ffffff",
        "on-primary-container": "#fffbff",
        secondary: "#006e26",
        "on-secondary": "#ffffff",
        background: "#fcf9f8",
        surface: "#fcf9f8",
        "surface-container": "#f0eded",
        "surface-container-low": "#f6f3f2",
        "surface-container-high": "#eae7e7",
        "surface-container-lowest": "#ffffff",
        "on-surface": "#1b1b1b",
        "on-surface-variant": "#5b403f",
        "outline-variant": "#e4bebc",
        outline: "#8f6f6e",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",
      },
      spacing: {
        xs: "8px",
        sm: "12px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        "margin-desktop": "48px",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "page-title": ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }],
        "section-title": ["24px", { lineHeight: "1.3", letterSpacing: "-0.01em", fontWeight: "600" }],
        "card-title": ["18px", { lineHeight: "1.4", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "1.5", fontWeight: "500" }],
        "body-md": ["14px", { lineHeight: "1.5", fontWeight: "400" }],
        "label-sm": ["12px", { lineHeight: "1.2", letterSpacing: "0.01em", fontWeight: "400" }],
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0,0,0,0.08)",
        "rank-glow": "0 0 20px rgba(183, 18, 42, 0.15)",
      },
      borderRadius: {
        lg: "0.5rem",
        xl: "0.75rem",
      },
      animation: {
        shimmer: "shimmer 1.5s infinite",
        sparkle: "sparkle 2s ease-in-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        sparkle: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(1.1)" },
        },
      },
    },
  },
  plugins: [],
};
