import type { Metadata } from "next";
import "./globals.css";
// Serve fresh HTML so a rollout cannot strand visitors on retired asset URLs.
export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  authors: [{ name: "Hiten Arora", url: "https://github.com/Hiten41" }],
  title: "CareerGraph AI — Find your next direction",
  description: "Explainable job discovery powered by hybrid retrieval.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
