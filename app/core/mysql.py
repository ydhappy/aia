from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote, urlparse

try:
    import pymysql
except Exception:  # pragma: no cover
    pymysql = None


@dataclass(frozen=True)
class MysqlDsn:
    host: str
    port: int
    user: str
    password: str
    database: str


def parse_mysql_dsn(dsn: str, default_database: str = "aia") -> MysqlDsn:
    normalized = str(dsn or "").replace("mysql+pymysql://", "mysql://")
    parsed = urlparse(normalized)
    return MysqlDsn(
        host=parsed.hostname or "localhost",
        port=parsed.port or 3306,
        user=unquote(parsed.username or "root"),
        password=unquote(parsed.password or ""),
        database=(parsed.path or "/%s" % default_database).lstrip("/") or default_database,
    )


def connect_mysql(dsn: str, *, autocommit: bool = True, default_database: str = "aia"):
    if pymysql is None:
        raise RuntimeError("pymysql_not_installed")
    parsed = parse_mysql_dsn(dsn, default_database=default_database)
    return pymysql.connect(
        host=parsed.host,
        port=parsed.port,
        user=parsed.user,
        password=parsed.password,
        database=parsed.database,
        autocommit=autocommit,
        charset="utf8",
        cursorclass=pymysql.cursors.DictCursor,
    )
