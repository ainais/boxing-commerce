import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 검증 빌드 등에서 dev 서버의 .next와 분리하기 위해 환경변수로 지정 가능
  distDir: process.env.NEXT_DIST_DIR || ".next",
  cacheComponents: true,
  // Docker 배포용: .next/standalone에 실행에 필요한 파일만 모은다(node server.js로 실행)
  output: "standalone",
  images: {
    // 상품 이미지는 판매처 외부 주소. 복싱몰 이미지는 최적화를 거치지 않으므로(ProductImage 참고) 여기에 두지 않는다
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
