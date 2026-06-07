import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Trade Price Service",
  description: "AI-powered import cost calculator for Uzbekistan",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  );
}
