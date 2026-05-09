from app.services import db_bridge_service


def test_mysql_bridge_schema_does_not_use_text_defaults() -> None:
    ddl = db_bridge_service.MYSQL_BRIDGE_SCHEMA_SQL.upper()
    assert "TEXT NOT NULL DEFAULT" not in ddl
    assert "LONGTEXT NOT NULL DEFAULT" not in ddl
    assert "JSON" not in ddl
    assert "GENERATED" not in ddl


def test_mysql_bridge_schema_uses_utf8_and_innodb() -> None:
    ddl = db_bridge_service.MYSQL_BRIDGE_SCHEMA_SQL
    assert "ENGINE=InnoDB DEFAULT CHARSET=utf8" in ddl


def test_spawn_request_schema_is_mysql55_style() -> None:
    with open("sql/aia_robot_spawn_request_mysql55.sql", "r", encoding="utf-8") as fp:
        ddl = fp.read().upper()
    assert "ENGINE=INNODB DEFAULT CHARSET=UTF8" in ddl
    assert " TEXT NOT NULL DEFAULT" not in ddl
    assert " JSON" not in ddl
    assert " GENERATED" not in ddl
