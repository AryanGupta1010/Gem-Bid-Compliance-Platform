import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        gem: {
          navy: "#0F2C59",
          dark: "#08182B",
          blue: "#1E3A8A",
          primary: "#1D4ED8",
          light: "#F0F4F8",
          gold: "#D97706",
          green: "#059669",
          red: "#DC2626",
          amber: "#D97706"
        },
      },
    },
  },
  plugins: [],
};
export default config;
