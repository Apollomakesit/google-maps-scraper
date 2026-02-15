import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow API calls to the backend in development and production
  async rewrites() {
    let apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    // Ensure the URL has a protocol
    if (!apiUrl.startsWith('http://') && !apiUrl.startsWith('https://')) {
      apiUrl = `https://${apiUrl}`;
    }
    
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
