/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#080a10',
          panel: '#101422',
          card: '#161b30',
          border: '#222944',
          textMuted: '#8b9bb4',
          accent: '#6366f1',
          accentGlow: '#d16b4a',
          violet: '#8b5cf6',
          teal: '#14b8a6',
          success: '#10b981',
          danger: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
