import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Security headers for Mapbox
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' api.mapbox.com",
              "style-src 'self' 'unsafe-inline' api.mapbox.com",
              "img-src 'self' data: blob: *.mapbox.com api.mapbox.com *.tiles.mapbox.com",
              "connect-src 'self' api.mapbox.com *.tiles.mapbox.com events.mapbox.com localhost:8000",
              "worker-src 'self' blob:",
              "child-src blob:",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
