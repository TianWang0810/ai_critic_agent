/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#FAFAF8',
          card: '#FFFFFF',
          secondary: '#F2F1ED',
          muted: '#EBEBEB',
        },
        red: {
          primary: '#E8143A',
          mid: '#FF3B5C',
          soft: '#FF6B6B',
          tint: '#FFF0F2',
        },
        ink: {
          primary: '#111111',
          secondary: '#444444',
          muted: '#888888',
          faint: '#BBBBBB',
        },
        risk: {
          critical: '#E8143A',
          high: '#FF6B35',
          medium: '#F59E0B',
          low: '#059669',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-red': 'pulse-red 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        'pulse-red': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(232,20,58,0.5)' },
          '50%':      { opacity: '.7', boxShadow: '0 0 0 6px rgba(232,20,58,0)' },
        },
        'fade-in-up': {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 20px rgba(0,0,0,0.10)',
        'red-sm': '0 4px 20px rgba(232,20,58,0.18)',
      },
    },
  },
  plugins: [],
}
