/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: '#F8F9FA',
        foreground: '#1F2937',
        card: {
          DEFAULT: '#FFFFFF',
          foreground: '#1F2937'
        },
        popover: {
          DEFAULT: '#FFFFFF',
          foreground: '#1F2937'
        },
        primary: {
          DEFAULT: '#007BFF',
          foreground: '#FFFFFF'
        },
        secondary: {
          DEFAULT: '#F1F5F9',
          foreground: '#1F2937'
        },
        muted: {
          DEFAULT: '#F1F5F9',
          foreground: '#64748B'
        },
        accent: {
          DEFAULT: '#E9ECEF',
          foreground: '#1F2937'
        },
        destructive: {
          DEFAULT: '#EF4444',
          foreground: '#FFFFFF'
        },
        border: '#E5E7EB',
        input: '#E5E7EB',
        ring: '#007BFF',
        physics: {
          DEFAULT: '#E3F2FD',
          text: '#0288D1',
          border: '#B3E5FC'
        },
        chemistry: {
          DEFAULT: '#E8F5E9',
          text: '#388E3C',
          border: '#C8E6C9'
        },
        math: {
          DEFAULT: '#FFEBEE',
          text: '#D32F2F',
          border: '#FFCDD2'
        },
        pyq: '#E0DFFB',
        mytests: '#E8F5E9',
        assigned: '#FFF8DC',
        classes: '#FFE0E6',
        analytics: '#E3F2FD'
      },
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.375rem'
      },
      fontFamily: {
        heading: ['Plus Jakarta Sans', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      boxShadow: {
        'card': '0 2px 12px rgba(0,0,0,0.04)',
        'hover': '0 4px 20px rgba(0,0,0,0.08)',
        'floating': '0 8px 30px rgba(0,0,0,0.12)'
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
}