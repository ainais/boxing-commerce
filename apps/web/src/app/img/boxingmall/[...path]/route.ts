/**
 * 복싱몰 상품 이미지 프록시.
 * 복싱몰 서버가 TLS 중간 인증서를 보내지 않아 브라우저가 이미지를 거부하므로, 서버가 대신 받아 전달한다.
 * 이미지를 저장하지 않으며 호스트(복싱몰)와 경로(/product_images/ 아래 이미지 파일)가 고정이라 열린 프록시가 아니다.
 * 인증서 검증은 끄지 않고, BOXINGMALL_CA_FILE의 PEM을 시스템 루트 CA에 더해 신뢰한다.
 *
 * Cache Components: 이 GET은 params(런타임 데이터)와 connection()을 읽으므로 빌드 중 prerender되지 않고 요청 시점에 실행된다.
 */
import { readFileSync } from "node:fs";
import https from "node:https";
import { rootCertificates } from "node:tls";
import { connection } from "next/server";
import { BOXINGMALL_HOST, validateProxyPath } from "@/lib/boxingmallProxy";

const TIMEOUT_MS = 8000;
const MAX_BYTES = 5 * 1024 * 1024;
const USER_AGENT = "boxing-commerce-web/0.1";
const SUCCESS_CACHE_CONTROL =
  "public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400";

class ProxyError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

/** 모듈 수준에서 한 번만 만든다(성공했을 때만 보관, 실패하면 다음 요청에서 다시 시도) */
let agent: https.Agent | null = null;

function getAgent(): https.Agent {
  if (agent) return agent;
  const caFile = process.env.BOXINGMALL_CA_FILE?.trim();
  if (!caFile) {
    console.error("[img-proxy] BOXINGMALL_CA_FILE 환경변수가 없습니다");
    throw new ProxyError(503, "이미지 서버 인증서 설정이 필요합니다");
  }
  let pem: string;
  try {
    pem = readFileSync(caFile, "utf8");
  } catch (e) {
    const code = (e as NodeJS.ErrnoException).code ?? "UNKNOWN";
    console.error(`[img-proxy] 인증서 파일을 읽지 못했습니다: path=${caFile} error=${code}`);
    throw new ProxyError(503, "이미지 서버 인증서 설정이 필요합니다");
  }
  agent = new https.Agent({
    ca: [...rootCertificates, pem],
    keepAlive: true,
    maxSockets: 8,
  });
  return agent;
}

interface Upstream {
  contentType: string;
  body: Buffer;
  contentLength: string | null;
}

function fetchUpstream(path: string, method: "GET" | "HEAD"): Promise<Upstream> {
  const tlsAgent = getAgent();
  return new Promise((resolve, reject) => {
    const req = https.request(
      {
        hostname: BOXINGMALL_HOST,
        port: 443,
        path,
        method,
        agent: tlsAgent,
        headers: { "User-Agent": USER_AGENT, Accept: "image/*" },
      },
      (res) => {
        const status = res.statusCode ?? 0;
        if (status === 404) {
          res.resume();
          return reject(new ProxyError(404, "이미지를 찾을 수 없습니다"));
        }
        if (status !== 200) {
          res.resume();
          return reject(new ProxyError(502, `이미지 서버 응답 오류 (${status})`));
        }
        const contentType = String(res.headers["content-type"] ?? "");
        if (!contentType.toLowerCase().startsWith("image/")) {
          res.resume();
          return reject(new ProxyError(502, "이미지가 아닌 응답입니다"));
        }
        const declared = Number(res.headers["content-length"]);
        if (Number.isFinite(declared) && declared > MAX_BYTES) {
          res.resume();
          return reject(new ProxyError(502, "이미지가 너무 큽니다"));
        }
        const contentLength = res.headers["content-length"] ?? null;
        if (method === "HEAD") {
          res.resume();
          return resolve({ contentType, body: Buffer.alloc(0), contentLength });
        }
        const chunks: Buffer[] = [];
        let size = 0;
        res.on("data", (chunk: Buffer) => {
          size += chunk.length;
          if (size > MAX_BYTES) {
            req.destroy();
            reject(new ProxyError(502, "이미지가 너무 큽니다"));
            return;
          }
          chunks.push(chunk);
        });
        res.on("end", () => resolve({ contentType, body: Buffer.concat(chunks), contentLength: null }));
        res.on("error", () => reject(new ProxyError(502, "이미지 서버 응답 오류")));
      },
    );
    // 연결·응답이 멈추면 8초 뒤 끊는다. 전체 소요 시간 상한으로도 쓴다
    req.setTimeout(TIMEOUT_MS, () => req.destroy(new Error("timeout")));
    const total = setTimeout(() => req.destroy(new Error("timeout")), TIMEOUT_MS);
    req.on("close", () => clearTimeout(total));
    req.on("error", (e) => {
      console.error(`[img-proxy] 상위 요청 실패: path=${path} error=${(e as NodeJS.ErrnoException).code ?? e.message}`);
      reject(new ProxyError(502, "이미지 서버에 연결하지 못했습니다"));
    });
    req.end();
  });
}

function errorResponse(status: number, message: string): Response {
  return new Response(message, {
    status,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

async function handle(
  method: "GET" | "HEAD",
  params: Promise<{ path: string[] }>,
): Promise<Response> {
  await connection();
  const { path: segments } = await params;
  const upstreamPath = validateProxyPath(segments);
  if (!upstreamPath) return errorResponse(404, "찾을 수 없습니다");
  try {
    const upstream = await fetchUpstream(upstreamPath, method);
    const headers: Record<string, string> = {
      "Content-Type": upstream.contentType,
      "X-Content-Type-Options": "nosniff",
      "Cache-Control": SUCCESS_CACHE_CONTROL,
    };
    if (upstream.contentLength) headers["Content-Length"] = upstream.contentLength;
    return new Response(method === "HEAD" ? null : new Uint8Array(upstream.body), {
      status: 200,
      headers,
    });
  } catch (e) {
    if (e instanceof ProxyError) return errorResponse(e.status, e.message);
    console.error("[img-proxy] 알 수 없는 오류", e);
    return errorResponse(502, "이미지를 가져오지 못했습니다");
  }
}

type Ctx = { params: Promise<{ path: string[] }> };

export function GET(_request: Request, { params }: Ctx): Promise<Response> {
  return handle("GET", params);
}

export function HEAD(_request: Request, { params }: Ctx): Promise<Response> {
  return handle("HEAD", params);
}

// GET·HEAD 외 메서드는 405
function methodNotAllowed(): Response {
  return new Response("허용되지 않는 메서드입니다", {
    status: 405,
    headers: { Allow: "GET, HEAD", "Cache-Control": "no-store" },
  });
}
export const POST = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;
