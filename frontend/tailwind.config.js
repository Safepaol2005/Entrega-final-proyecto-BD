/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07131a",
          900: "#0c1f2b",
          800: "#143447",
          700: "#1c4a63",
          600: "#256381",
        },
        campus: {
          50: "#f3faf7",
          100: "#d8f0e6",
          200: "#a8ddc7",
          300: "#6fc4a5",
          400: "#3aa882",
          500: "#1f8f6b",
          600: "#157356",
          700: "#125b45",
        },
        ember: {
          400: "#f0b429",
          500: "#e09b13",
          600: "#c47d0a",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 18px 40px -24px rgba(7, 19, 26, 0.45)",
      },
    },
  },
  plugins: [],
};
