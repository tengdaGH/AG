import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: 'http://101.32.187.39:8000',
  }
};

export default nextConfig;
