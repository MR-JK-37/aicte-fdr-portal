/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#050505',
        'purple-deep': '#3b0a6b',
        'purple-glow': '#701a75',
        'cyan-neon': '#00eeff',
        'cyan-glow': '#38bdf8',
        slate: {
          950: '#050505',
          900: '#0b0614',
          800: '#190e2b',
          700: '#2d184a',
          600: '#4c267a',
          500: '#7e3eb8',
          400: '#a87fd1',
          300: '#d0baea',
          200: '#ede4f9',
          100: '#f8f4fe',
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        display: ['"Outfit"', 'sans-serif'],
        sans: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 25px rgba(0, 238, 255, 0.35)',
        'glow-purple': '0 0 35px rgba(59, 10, 107, 0.6)',
        'glow-cyan': '0 0 30px rgba(0, 238, 255, 0.45)',
        card: '0 8px 32px 0 rgba(0, 0, 0, 0.7), 0 0 20px rgba(59, 10, 107, 0.3)',
      },
    },
  },
  plugins: [],
};
