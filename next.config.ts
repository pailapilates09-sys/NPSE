import type { NextConfig } from "next";

const board = "https://pailapilates09-sys.github.io/NPSE/";
const legacyPages = [
  "/", "/workspace/:path*", "/how-to/:path*", "/guide/:path*", "/daily/:path*",
  "/candidates/:path*", "/company/:path*", "/sectors/:path*", "/methodology/:path*",
  "/sources/:path*", "/diagnostics/:path*", "/technical/:path*", "/backtests/:path*",
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The separate GitHub Pages source also lives under pages/.
  pageExtensions: ["ts", "tsx"],
  async redirects() {
    return legacyPages.map((source) => ({ source, destination: board, permanent: false }));
  },
  async rewrites() {
    return process.env.DEV_PYTHON_API ? [{source:"/api/:path*",destination:"http://127.0.0.1:8000/api/:path*"}] : [];
  },
};

export default nextConfig;
