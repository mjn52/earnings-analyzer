/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#1A56DB',
        'primary-dark': '#1446C0',
        surface: '#FFFFFF',
        border: '#E4E8F0',
        bg: '#F8F9FC',
        'text-main': '#111827',
        'text-muted': '#6B7280',
        success: '#059669',
        warning: '#D97706',
        danger: '#DC2626',
      },
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        dm: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
