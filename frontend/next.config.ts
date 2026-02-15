import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow API calls to the backend in development and production
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
