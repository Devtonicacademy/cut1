import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="en">
      <body className="antialiased min-h-screen flex flex-col bg-[#090d16] text-gray-100">
        {children}
      </body>
    </html>
  );
}
