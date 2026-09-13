import type { Config } from "tailwindcss";

/**
 * Base Tailwind config — plumbing only. No theme/color/font decisions here
 * yet: the homepage/search visual direction is still under review (5
 * candidate designs on a separate design canvas, not yet picked). Adding
 * a color palette or type scale here now would mean redoing it once a
 * direction is chosen — leave `theme.extend` empty until then.
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
