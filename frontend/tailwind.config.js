/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50:  '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
      },
      backgroundImage: {
        'page': 'linear-gradient(135deg, #f4f6fb 0%, #eef0f8 100%)',
      },
      boxShadow: {
        card:        '0 1px 3px rgba(0,0,0,.05), 0 1px 2px rgba(0,0,0,.04)',
        'card-hover':'0 8px 24px rgba(124,58,237,.08), 0 2px 8px rgba(0,0,0,.06)',
        'glow':      '0 0 20px rgba(124,58,237,.3)',
      },
      animation: {
        'fade-in':  'fadeIn .25s ease-out',
        'slide-up': 'slideUp .3s ease-out',
        'scale-in': 'scaleIn .2s ease-out',
        'shimmer':  'shimmer 1.4s infinite linear',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 },                              to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(14px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        scaleIn: { from: { opacity: 0, transform: 'scale(.95)' },     to: { opacity: 1, transform: 'scale(1)' } },
        shimmer: { from: { backgroundPosition: '-200px 0' },          to: { backgroundPosition: 'calc(200px + 100%) 0' } },
      },
    },
  },
  plugins: [],
}
