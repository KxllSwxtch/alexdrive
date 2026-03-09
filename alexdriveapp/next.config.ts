import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "img.carmanager.co.kr",
      },
      {
        protocol: "http",
        hostname: "img.carmanager.co.kr",
      },
    ],
    minimumCacheTTL: 86400,
    formats: ["image/avif", "image/webp"],
  },
};

export default nextConfig;
