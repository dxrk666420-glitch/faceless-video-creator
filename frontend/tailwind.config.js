/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fef3ee',
          100: '#fde4d6',
          200: '#fac5ad',
          300: '#f69d78',
          400: '#f17042',
          500: '#ed4e1e',
          600: '#de3514',
          700: '#b82513',
          800: '#932018',
          900: '#771d16',
        },
      },
    },
  },
  plugins: [],
};
