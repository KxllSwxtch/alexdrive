import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  turbopack: {
    root: import.meta.dirname,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "photo5.autosale.co.kr",
      },
      {
        protocol: "http",
        hostname: "photo5.autosale.co.kr",
      },
      {
        protocol: "https",
        hostname: "m.jenya.co.kr",
      },
    ],
    minimumCacheTTL: 86400,
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [128, 256, 384],
  },
};

export default nextConfig;
