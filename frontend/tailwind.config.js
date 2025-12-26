/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          700: '#40414f',
          800: '#343541',
          900: '#202123',
        }
      }
    },
  },
  plugins: [],
}
