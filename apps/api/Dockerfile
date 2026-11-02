# syntax=docker/dockerfile:1

# ---- build: bootJar ----
FROM eclipse-temurin:21-jdk AS build
WORKDIR /workspace

# 빌드 설정만 먼저 복사해 의존성 다운로드 레이어를 캐시한다(소스만 바뀌면 재사용)
COPY gradlew settings.gradle build.gradle ./
COPY gradle gradle
RUN chmod +x gradlew && ./gradlew --no-daemon dependencies > /dev/null

COPY src src
RUN ./gradlew --no-daemon bootJar -x test \
    && cp build/libs/*-SNAPSHOT.jar /workspace/app.jar

# ---- run ----
FROM eclipse-temurin:21-jre
ENV TZ=Asia/Seoul \
    JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=70

# 헬스체크용 curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home app

WORKDIR /app
COPY --from=build --chown=app:app /workspace/app.jar /app/app.jar

USER app
# 서버 포트는 application.yml의 4001. 프로파일(SPRING_PROFILES_ACTIVE)과 DB 접속 정보는 실행 시 환경변수로 받는다
EXPOSE 4001
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
