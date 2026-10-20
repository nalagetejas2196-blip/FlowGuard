/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: "#F4F0E8",
        graphite: "#292A28",
        vermilion: "#C84A35",
        "vermilion-hover": "#B33E2B",
        limestone: "#EAE5DA",
        "limestone-light": "#F0ECE2",
        stone: {
          border: "#DCD6C8",
          subtle: "#B5AFA2",
          dim: "#888277"
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
