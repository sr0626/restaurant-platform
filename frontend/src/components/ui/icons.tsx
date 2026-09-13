// Shared stroke-based SVG icons — "Spice Market" direction calls for inline
// SVG (never emoji) for search, location, and star-rating glyphs, all drawn
// at the same visual weight (round caps/joins, 1.75 stroke on a 24x24 grid).
// Color always comes from the caller's `className` (e.g. `text-brand-ink`,
// `text-brand-accent`) via `currentColor` — never a hardcoded fill/stroke.
import type { SVGProps } from "react";

export type IconProps = SVGProps<SVGSVGElement>;

const baseProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export function SearchIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4.5-4.5" />
    </svg>
  );
}

export function LocationPinIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M12 21s-7-6.29-7-11.5A7 7 0 0 1 19 9.5C19 14.71 12 21 12 21z" />
      <circle cx="12" cy="9.5" r="2.25" />
    </svg>
  );
}

export function StarIcon(props: IconProps) {
  return (
    <svg {...baseProps} strokeLinejoin="round" fill="currentColor" stroke="none" {...props}>
      <path d="M12 3.5l2.47 5.13 5.53.82-4 4.02.94 5.53L12 16.6l-4.94 2.4.94-5.53-4-4.02 5.53-.82L12 3.5z" />
    </svg>
  );
}

/** Added for the restaurant detail page's weekly hours section. */
export function ClockIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.25V12l3.25 2" />
    </svg>
  );
}

/** Added for the restaurant detail page's contact/phone line. */
export function PhoneIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M6.5 4h3l1.5 4-2 1.5a11 11 0 0 0 5.5 5.5l1.5-2 4 1.5v3a2 2 0 0 1-2 2A16 16 0 0 1 4.5 6a2 2 0 0 1 2-2z" />
    </svg>
  );
}

/** Added for the restaurant detail page's photo gallery section. */
export function ImageIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="3.5" y="4.5" width="17" height="15" rx="2" />
      <circle cx="8.5" cy="9.5" r="1.5" />
      <path d="M3.5 16l5-5 4 4 3-3 4.5 4.5" />
    </svg>
  );
}
