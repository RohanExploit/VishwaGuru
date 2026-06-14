/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      colors: {
        // Dark mode specific colors
        'dark-bg': '#1a1a1a',
        'dark-card': '#2d2d2d',
        'dark-border': '#404040',
      },
    },
  },
  plugins: [],
}
