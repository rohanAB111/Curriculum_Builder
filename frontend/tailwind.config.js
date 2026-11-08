/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        nba: {
          navy: "#163669",
          slate: "#46505f",
          accent: "#dc4b2d",
          light: "#ebf2fa",
          dark: "#0b1d3a",
        },
      },
    },
  },
  plugins: [],
};
