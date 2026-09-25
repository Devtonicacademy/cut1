import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#090d16" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export const metadata: Metadata = {
  title: "LivelyBorg AI | Football Betting Intelligence Lagos",
  description: "Next-gen AI sports prediction, +EV value finder, and Fractional Kelly bankroll manager for SportyBet & Bet9ja punters.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-[#090d16] dark:text-gray-100 transition-colors duration-150">
        {children}
      </body>
    </html>
  );
}
