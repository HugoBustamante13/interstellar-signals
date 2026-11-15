/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        status: {
          normal: "#22c55e",
          attention: "#f59e0b",
          critical: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};
