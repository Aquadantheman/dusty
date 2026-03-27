import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dusty - Vintage & Antique Shop Finder",
  description: "Discover vintage shops, antique stores, and thrift finds in NYC. Track sales and never miss a deal.",
  keywords: ["vintage", "antique", "thrift", "NYC", "shopping", "sales", "secondhand"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
