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
          navy: "#0f2235",
          steel: "#1a3a5c",
          mid: "#2c5282",
          accent: "#e07b2a",
          warn: "#c0392b",
          safe: "#1a7a4a",
          light: "#f0f4f8",
          muted: "#6b7c93",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
