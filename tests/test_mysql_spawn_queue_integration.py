import os
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
import pymysql

from app.core.config import settings
from app.models.request_models import RobotSpawnRequestCreateRequest
from app.services.robot_spawn_request_service import robot_spawn_request_service
from app.services.spawn_request_dashboard_service import spawn_request_dashboard_service


MYSQL_DSN = os.environ.get("AIA_TEST_MYSQL_DSN", "")


def _connect(dsn: str):
    parsed = urlparse(dsn.replace("mysql+pymysql://", "mysql://"))
    return pymysql.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 3306,
        user=parsed.username or "root",
        password=parsed.password or "",
        database=(parsed.path or "/aia").lstrip("/"),
        autocommit=True,
        charset="utf8",
        cursorclass=pymysql.cursors.DictCursor,
    )


@pytest.mark.skipif(not MYSQL_DSN, reason="AIA_TEST_MYSQL_DSN is not configured")
def test_mysql_spawn_queue_create_retry_and_recover() -> None:
    old_backend = settings.db_bridge_backend
    old_dsn = settings.db_bridge_mysql_dsn
    settings.db_bridge_backend = "mysql"
    settings.db_bridge_mysql_dsn = MYSQL_DSN
    prefix = "ci-%d" % int(time.time() * 1000)
    agent_prefix = "ci_robot_%d" % int(time.time())
    try:
        with _connect(MYSQL_DSN) as conn:
            sql = Path("sql/aia_robot_spawn_request_mysql55.sql").read_text(encoding="utf-8")
            with conn.cursor() as cur:
                for stmt in [item.strip() for item in sql.split(";") if item.strip() and not item.strip().startswith("-- Example")]:
                    cur.execute(stmt)
                cur.execute("DELETE FROM aia_robot_spawn_request WHERE request_id LIKE %s", (prefix + "%",))

        create_result = robot_spawn_request_service.create_requests(
            RobotSpawnRequestCreateRequest(
                server_name="ci",
                count=2,
                request_prefix=prefix,
                agent_prefix=agent_prefix,
                classes=["knight", "elf"],
                level_min=1,
                level_max=10,
            )
        )
        assert create_result["accepted"] is True
        assert create_result["submitted"] == 2
        assert create_result["affected"] >= 2

        summary = spawn_request_dashboard_service.summary(limit=10, status="pending")
        assert summary["enabled"] is True
        assert summary["counts"]["pending"] >= 2

        with _connect(MYSQL_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE aia_robot_spawn_request SET status = 'failed', last_error = 'ci failure' WHERE request_id LIKE %s",
                    (prefix + "%",),
                )

        retry_result = spawn_request_dashboard_service.retry_failed(server_name="ci", limit=10)
        assert retry_result["accepted"] is True
        assert retry_result["updated"] >= 2

        with _connect(MYSQL_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE aia_robot_spawn_request SET status = 'claimed', claimed_at = DATE_SUB(NOW(), INTERVAL 30 MINUTE) WHERE request_id LIKE %s",
                    (prefix + "%",),
                )

        recover_result = spawn_request_dashboard_service.recover_stale_claimed(server_name="ci", older_than_minutes=10, limit=10)
        assert recover_result["accepted"] is True
        assert recover_result["updated"] >= 2
    finally:
        try:
            with _connect(MYSQL_DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM aia_robot_spawn_request WHERE request_id LIKE %s", (prefix + "%",))
        finally:
            settings.db_bridge_backend = old_backend
            settings.db_bridge_mysql_dsn = old_dsn
