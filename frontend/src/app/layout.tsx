import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Trade AI - Import Business Advisor",
  description: "AI-powered import cost calculator and business advisor for Uzbekistan. Find profitable products from China.",
  openGraph: {
    title: "Trade AI",
    description: "Import biznes uchun AI maslahatchi",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz" className="dark">
      <body className="min-h-screen bg-surface-900 antialiased">
        {children}
      </body>
    </html>
  );
}
