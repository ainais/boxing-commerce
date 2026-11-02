# 운영 배포 (api + web)

`docker-compose.prod.yml`은 이미 만들어진 이미지(`boxing-api`, `boxing-web`)를 띄우기만 합니다. compose에서 빌드하지 않습니다.
이미지 빌드·배포를 자동화하는 Jenkins 파이프라인은 다음 단계입니다.

## 구성

```
인터넷 ─ (터널) ─▶ 127.0.0.1:4100 ─▶ [web :4000] ──▶ [api :4001] ──▶ [pg-local :5432]
                    └ 호스트에 열린 유일한 포트        └ 포트 미공개      └ postgres_default 네트워크
```

- 외부에 공개되는 것은 web뿐입니다. api와 DB는 포트를 열지 않습니다.
- `4100`은 터널이 연결할 로컬 포트입니다(호스트의 `127.0.0.1`에만 바인딩). 컨테이너 안에서 web은 `4000`을 씁니다.
- api는 compose 기본 네트워크(web과 통신)와 외부 네트워크 `postgres_default`(DB 접근)에 붙습니다. web은 `postgres_default`에 붙이지 않습니다. 이 네트워크는 Postgres 컨테이너 쪽에서 미리 만들어져 있어야 합니다(`external: true`).

## 환경변수

`deploy/.env.example`을 `deploy/.env`로 복사해 채웁니다(`.env`는 git에서 제외).

| 이름 | 설명 | 기본값 |
| --- | --- | --- |
| `DB_PASSWORD` | DB 비밀번호. 없으면 compose가 오류를 냅니다 | 없음(필수) |
| `API_TAG` | `boxing-api` 이미지 태그 | `latest` |
| `WEB_TAG` | `boxing-web` 이미지 태그 | `latest` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare 터널 토큰. 없으면 compose가 오류를 냅니다 | 없음(필수) |
| `CLOUDFLARED_TAG` | `cloudflare/cloudflared` 이미지 태그 | `latest` |

compose 안에 고정된 값: api는 `SPRING_PROFILES_ACTIVE=prod`, `DB_URL=jdbc:postgresql://pg-local:5432/boxing_commerce`, `DB_USERNAME=boxing`, `TZ=Asia/Seoul`이고, web은 `API_BASE_URL=http://api:4001`입니다. `API_BASE_URL`은 이미지에 들어 있지 않고 실행 시에만 주입됩니다. 메모리 제한은 api 768m, web 512m입니다.

## Cloudflare 터널

`tunnel` 서비스(`boxing-tunnel`, `cloudflare/cloudflared`)가 `boxingeverything.site`로 들어온 요청을 web으로 전달합니다.

```
boxingeverything.site ─▶ Cloudflare ─▶ 터널(boxing-tunnel) ─▶ web:4000
```

- 원칙: 외부에 공개하는 것은 web 하나뿐입니다. api, DB, Jenkins는 터널에 연결하지 않습니다. 터널 컨테이너는 compose 기본 네트워크만 쓰고 `postgres_default`에는 붙지 않으므로 DB 네트워크에 닿지 않습니다. 포트도 열지 않습니다.
- 토큰(`CLOUDFLARE_TUNNEL_TOKEN`)은 `deploy/.env`에만 둡니다. 레포, 이미지, 로그에 넣지 마세요.
- Cloudflare 대시보드(Zero Trust → Networks → Tunnels → 해당 터널 → Public Hostname)에서 다음과 같이 설정합니다.
  - Hostname: `boxingeverything.site`
  - Service Type: `HTTP`
  - URL: `web:4000`
- 헬스체크는 없습니다(cloudflared 이미지에 셸이 없을 수 있음). 상태는 `docker logs boxing-tunnel`과 대시보드의 터널 상태로 확인합니다.
- 이미지 태그는 기본이 `latest`입니다. 운영 안정화 후 버전 태그를 고정하는 것을 권장하며, 사용 가능한 태그는 Docker Hub의 `cloudflare/cloudflared`에서 확인합니다(`CLOUDFLARED_TAG`).
- 터널만 재시작/반영:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d tunnel
```

## 로컬에서 직접 빌드해 실행

```bash
docker build -t boxing-api:local apps/api
docker build -t boxing-web:local apps/web

cp deploy/.env.example deploy/.env   # DB_PASSWORD 채우기
API_TAG=local WEB_TAG=local docker compose -f deploy/docker-compose.prod.yml up -d
```

compose 파일 문법만 확인하려면(컨테이너를 만들지 않음):

```bash
DB_PASSWORD=x docker compose -f deploy/docker-compose.prod.yml config
```

web 이미지는 빌드 중에 API를 호출하지 않으므로 API 없이도 빌드됩니다.

## 롤백

이전 태그로 바꿔 다시 `up -d` 합니다.

```bash
API_TAG=<이전 태그> WEB_TAG=<이전 태그> docker compose -f deploy/docker-compose.prod.yml up -d
```

`deploy/.env`의 `API_TAG`, `WEB_TAG`를 고쳐도 됩니다. 이전 태그의 이미지가 호스트에 남아 있어야 합니다.

## 참고

- api는 prod 프로파일에서 Flyway가 `db/migration`만 적용합니다. 기존 DB에 dev 시드 이력이 있어도 `repeatable:missing`을 무시하도록 설정돼 있습니다.
- api 헬스체크는 `GET /api/health`(시작 유예 60초), web은 이미지의 HEALTHCHECK가 `/`를 확인합니다. web은 api가 healthy가 된 뒤에 시작합니다.
