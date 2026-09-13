// Root layout — HTML shell, font loading, and metadata boilerplate only.
// No visual/theme design here (homepage color/style direction is still
// under review on a separate design canvas — see the Frontend Dev task
// notes). Inter is a neutral placeholder font wired through next/font so
// the loading mechanism exists; swap the family once a design direction
// is picked, this file's job is just the plumbing.
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Indian Restaurant Discovery — Dallas-Fort Worth",
    template: "%s | Indian Restaurant Discovery",
  },
  description:
    "Find verified Indian restaurants across Dallas-Fort Worth, filter by regional cuisine and dietary needs, and see deals from registered restaurants.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
