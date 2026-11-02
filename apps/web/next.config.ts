import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 검증 빌드 등에서 dev 서버의 .next와 분리하기 위해 환경변수로 지정 가능
  distDir: process.env.NEXT_DIST_DIR || ".next",
  cacheComponents: true,
  images: {
    // 상품 이미지는 판매처(골든챔스) 외부 주소
    remotePatterns: [
      { protocol: "https", hostname: "goldenchamps.co.kr", pathname: "/web/product/**" },
    ],
  },
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
