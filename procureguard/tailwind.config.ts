import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        navy: "#113957",
        mist: "#f4f7f8",
        line: "#dbe4e8",
        teal: "#087f8c",
        saffron: "#c77719",
        danger: "#bd3a3a"
      },
      boxShadow: {
        panel: "0 8px 30px rgba(24, 47, 62, 0.06)"
      }
    }
  },
  plugins: []
};

export default config;
