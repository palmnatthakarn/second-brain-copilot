import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI AP & GL Copilot",
  description: "Trace AP vendor balances back to GL documents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
