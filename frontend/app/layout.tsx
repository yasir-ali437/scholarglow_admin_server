import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ScholarGlow Admin — Content Pipeline",
  description: "Generate and publish scholarship posts to scholarglow.com",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ position: "relative", zIndex: 1 }}>
        {children}
      </body>
    </html>
  );
}
