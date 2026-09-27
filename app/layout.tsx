import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NPSE Control Tower",
  description: "Source-traceable Nepal Stock Exchange market research dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
