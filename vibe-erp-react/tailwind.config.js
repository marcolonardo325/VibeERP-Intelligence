/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Aggiungiamo i colori personalizzati per il tuo VIBE ERP
        slate: {
          950: '#020617',
        }
      }
    },
  },
  plugins: [],
}