# syntax=docker/dockerfile:1

# pnpm 버전은 package.json의 packageManager 값을 corepack이 읽어 맞춘다
# sharp(next/image 최적화)는 glibc용 사전 빌드 바이너리를 쓰므로 alpine이 아닌 slim(Debian) 이미지를 쓴다
ARG NODE_IMAGE=node:24-slim

# ---- deps ----
FROM ${NODE_IMAGE} AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# ---- build ----
FROM ${NODE_IMAGE} AS build
RUN corepack enable
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# 빌드 중에는 API를 호출하지 않는다(src/lib/api.ts의 deferToRequest). API_BASE_URL도 이미지에 넣지 않는다
RUN pnpm build

# ---- run ----
FROM ${NODE_IMAGE} AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=4000 \
    TZ=Asia/Seoul

# standalone 산출물에는 public/·.next/static이 없어 따로 복사해야 한다
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 4000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD node -e "fetch('http://127.0.0.1:4000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.js"]
