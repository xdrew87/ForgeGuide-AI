/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forge: {
          navy: "#0a0e16",
          steel: "#131a27",
          mid: "#26344d",
          line: "#212a3b",
          accent: "#e2812f",
          accentDim: "#a85f22",
          warn: "#c0392b",
          safe: "#1f8a52",
          light: "#f0f4f8",
          muted: "#8492a6",
        },
      },
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
    },
  },
  plugins: [],
};
