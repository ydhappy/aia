import os
import time
from pathlib import Path

import pytest

from app.api.routes_health import health_details
from app.core.config import settings
from app.core.mysql import connect_mysql
from app.models.request_models import RobotSpawnRequestCreateRequest
from app.services.robot_spawn_request_service import robot_spawn_request_service
from app.services.spawn_request_dashboard_service import spawn_request_dashboard_service


MYSQL_DSN = os.environ.get("AIA_TEST_MYSQL_DSN", "")
REQUIRED_TABLES = [
    "aia_robot_spawn_request",
    "aia_robot_state",
    "aia_robot_event",
    "aia_robot_feedback",
    "aia_robot_decision",
    "aia_robot_trace_summary",
]


def _apply_sql_file(cur, path: str) -> None:
    sql = Path(path).read_text(encoding="utf-8")
    for stmt in [item.strip() for item in sql.split(";") if item.strip() and not item.strip().startswith("-- Example")]:
        cur.execute(stmt)


@pytest.mark.skipif(not MYSQL_DSN, reason="AIA_TEST_MYSQL_DSN is not configured")
def test_mysql_spawn_queue_create_retry_recover_and_health() -> None:
    old_backend = settings.db_bridge_backend
    old_dsn = settings.db_bridge_mysql_dsn
    settings.db_bridge_backend = "mysql"
    settings.db_bridge_mysql_dsn = MYSQL_DSN
    prefix = "ci-%d" % int(time.time() * 1000)
    agent_prefix = "ci_robot_%d" % int(time.time())
    other_prefix = prefix + "-other"
    try:
        with connect_mysql(MYSQL_DSN) as conn:
            with conn.cursor() as cur:
                _apply_sql_file(cur, "sql/aia_robot_schema.sql")
                _apply_sql_file(cur, "sql/aia_robot_spawn_request_mysql55.sql")
                cur.execute("DELETE FROM aia_robot_spawn_request WHERE request_id LIKE %s", (prefix + "%",))

        health = health_details()
        assert health["mysql"]["status"] == "ok"
        assert health["mysql"]["missing_tables"] == []
        for table_name in REQUIRED_TABLES:
            assert health["mysql"]["tables"][table_name]["exists"] is True

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

        other_result = robot_spawn_request_service.create_requests(
            RobotSpawnRequestCreateRequest(
                server_name="other-ci",
                count=1,
                request_prefix=other_prefix,
                agent_prefix=agent_prefix + "_other",
                classes=["wizard"],
                level_min=1,
                level_max=10,
            )
        )
        assert other_result["accepted"] is True

        summary = spawn_request_dashboard_service.summary(limit=10, status="pending", server_name="ci")
        assert summary["enabled"] is True
        assert summary["server_name_filter"] == "ci"
        assert summary["counts"]["pending"] == 2
        assert all(row["server_name"] == "ci" for row in summary["recent"])

        unfiltered_summary = spawn_request_dashboard_service.summary(limit=10, status="pending")
        assert unfiltered_summary["counts"]["pending"] >= 3

        with connect_mysql(MYSQL_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE aia_robot_spawn_request SET status = 'failed', last_error = 'ci failure' WHERE request_id LIKE %s",
                    (prefix + "%",),
                )

        retry_result = spawn_request_dashboard_service.retry_failed(server_name="ci", limit=10)
        assert retry_result["accepted"] is True
        assert retry_result["updated"] >= 2

        with connect_mysql(MYSQL_DSN) as conn:
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
            with connect_mysql(MYSQL_DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM aia_robot_spawn_request WHERE request_id LIKE %s", (prefix + "%",))
        finally:
            settings.db_bridge_backend = old_backend
            settings.db_bridge_mysql_dsn = old_dsn
