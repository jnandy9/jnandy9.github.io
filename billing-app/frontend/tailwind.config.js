/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#FAFAF7',
        card: '#FFFFFF',
        ink: '#1C2B3A',
        'ink-soft': '#4A5A68',
        hairline: '#E2DED4',
        brass: '#9C6B3E',
        'brass-soft': '#F1E4D5',
        green: '#2F6B4F',
        red: '#A6432F',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
