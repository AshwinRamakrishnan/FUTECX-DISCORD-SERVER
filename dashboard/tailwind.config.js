/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#09090b", // Deep Black
        surface: "#18181b", // Dark Slate
        primary: "#3b82f6", // Electric accent
        text: "#fafafa"
      },
    },
  },
  plugins: [],
}
