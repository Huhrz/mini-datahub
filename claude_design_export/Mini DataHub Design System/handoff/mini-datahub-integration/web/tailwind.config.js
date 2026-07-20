/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Replaced the old indigo `brand` scale with a teal/cyan "accent"
        // scale — matches the Mini DataHub design system's v2 tokens.
        accent: {
          50: "#ecfeff", 100: "#cffafe", 200: "#a5f3fc", 300: "#67e8f9",
          400: "#22d3ee", 500: "#06b6d4", 600: "#0891b2", 700: "#0e7490",
          800: "#155e75", 900: "#164e63",
        },
      },
      fontFamily: {
        // Space Grotesk for UI/display, IBM Plex Mono for ids/values/code.
        // Both loaded via Google Fonts in index.css.
        sans: ["Space Grotesk", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "PingFang SC", "Microsoft YaHei", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
