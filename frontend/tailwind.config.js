/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          green: "#2D6A4F",
          blue: "#168AAD",
          cream: "#FFF8E7",
        },
        ink: "#1F2937",
        muted: "#64748B",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        line: "#E5E7EB",
      },
      fontFamily: {
        sora: ["Sora", "sans-serif"],
        manrope: ["Manrope", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
