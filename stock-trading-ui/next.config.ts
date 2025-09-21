import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  turbopack: {
    // WSL 환경에서 올바른 루트 디렉토리 설정
    root: __dirname
  },
  // 포트 9000 고정 설정
  env: {
    PORT: '9000'
  }
};

export default nextConfig;
