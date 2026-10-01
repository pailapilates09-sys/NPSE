import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "NPSE Investment Decision Engine",
  description: "Evidence-based Nepal stock research: company quality, valuation, entry and thesis invalidation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><nav className="main-nav" aria-label="Main navigation"><Link className="brand" href="/">NPSE <span>RESEARCH</span></Link><div><Link href="/">Decision Board</Link><Link href="/candidates">Candidates</Link><Link href="/sectors">Sectors</Link><Link href="/methodology">Methodology</Link><Link href="/backtests">Backtests</Link><Link href="/sources">Sources</Link><Link href="/diagnostics">Diagnostics</Link></div></nav>{children}</body>
    </html>
  );
}
