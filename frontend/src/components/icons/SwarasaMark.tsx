// The "Fork-E" brand mark: fork tines + neck curve rotated on its side,
// with a knife on the top arm and a spoon on the bottom arm. Uses
// currentColor so it inherits whatever text color it's placed in.
export default function SwarasaMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="2 12 47 22.4"
      className={className}
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M2 22 L16 22"
        stroke="currentColor"
        strokeWidth="4.4"
        strokeLinecap="round"
      />
      <g transform="rotate(90 24 22)">
        <g
          stroke="currentColor"
          strokeWidth="4.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M17 12 L17 24 M31 12 L31 24" />
          <path d="M17 24 Q17 31 24 31 Q31 31 31 24" />
        </g>
      </g>
      <path
        d="M34 12 L44 12 C 47.5 12, 49 13.5, 48.4 15.5 C 47.5 17.5, 38 18.5, 34 16.5 Z"
        fill="currentColor"
      />
      <ellipse cx="41" cy="29" rx="7.4" ry="5.4" fill="currentColor" />
    </svg>
  );
}
