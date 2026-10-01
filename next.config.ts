import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return process.env.DEV_PYTHON_API ? [{source:"/api/:path*",destination:"http://127.0.0.1:8000/api/:path*"}] : [];
  },
};

export default nextConfig;
