import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        panel: "#f8fafc",
        line: "#d7dee8",
        accent: "#0f766e",
        amber: "#b45309",
      },
    },
  },
  plugins: [],
};

export default config;
