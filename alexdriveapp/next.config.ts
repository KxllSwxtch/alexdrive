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
        hostname: "www.carmodoo.com",
      },
      {
        protocol: "https",
        hostname: "code2.car2b.com",
      },
      {
        protocol: "https",
        hostname: "www.carmanager.co.kr",
      },
    ],
    minimumCacheTTL: 86400,
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [128, 256, 384],
  },
};

export default nextConfig;
