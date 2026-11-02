"""DB 연결·advisory lock·SQL 헬퍼 (psycopg)."""

import os
from collections.abc import Sequence
from typing import Any

import psycopg

# crawler 동시 실행 방지용 advisory lock 키(고정)
ADVISORY_LOCK_KEY = 7302024001


class ConfigError(RuntimeError):
    pass


def connect_from_env() -> psycopg.Connection:
    """환경변수 CRAWLER_DB_*로 개별 파라미터 연결한다(URL 조합 없음). autocommit은 끈다."""
    env = os.environ
    missing = [k for k in ("CRAWLER_DB_NAME", "CRAWLER_DB_USER") if not env.get(k)]
    if missing:
        raise ConfigError(f"필수 환경변수가 없습니다: {', '.join(missing)}")
    try:
        port = int(env.get("CRAWLER_DB_PORT", "5432"))
    except ValueError as e:
        raise ConfigError("CRAWLER_DB_PORT는 정수여야 합니다") from e
    return psycopg.connect(
        host=env.get("CRAWLER_DB_HOST", "localhost"),
        port=port,
        dbname=env["CRAWLER_DB_NAME"],
        user=env["CRAWLER_DB_USER"],
        password=env.get("CRAWLER_DB_PASSWORD") or None,
        application_name="boxing-crawler",
        autocommit=False,
    )


def try_lock(conn: psycopg.Connection) -> bool:
    row = conn.execute("SELECT pg_try_advisory_lock(%s)", (ADVISORY_LOCK_KEY,)).fetchone()
    conn.commit()
    return bool(row and row[0])


def unlock(conn: psycopg.Connection) -> None:
    conn.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK_KEY,))
    conn.commit()


def insert_returning_ids(cur: psycopg.Cursor, sql: str, rows: Sequence[Sequence[Any]]) -> list[int]:
    """executemany로 배치 INSERT ... RETURNING id 를 실행해 행 순서대로 id를 돌려준다."""
    if not rows:
        return []
    cur.executemany(sql, rows, returning=True)
    ids: list[int] = []
    while True:
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("RETURNING 결과가 없습니다")
        ids.append(row[0])
        if not cur.nextset():
            break
    return ids
