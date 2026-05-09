from app.core.mysql import parse_mysql_dsn


def test_parse_mysql_pymysql_dsn() -> None:
    parsed = parse_mysql_dsn("mysql+pymysql://user:pass@127.0.0.1:3307/game_db")
    assert parsed.host == "127.0.0.1"
    assert parsed.port == 3307
    assert parsed.user == "user"
    assert parsed.password == "pass"
    assert parsed.database == "game_db"


def test_parse_mysql_dsn_defaults() -> None:
    parsed = parse_mysql_dsn("mysql+pymysql://localhost")
    assert parsed.host == "localhost"
    assert parsed.port == 3306
    assert parsed.user == "root"
    assert parsed.password == ""
    assert parsed.database == "aia"


def test_parse_mysql_dsn_unquotes_credentials() -> None:
    parsed = parse_mysql_dsn("mysql+pymysql://root:p%40ss%3Aword@localhost/aia_ci")
    assert parsed.user == "root"
    assert parsed.password == "p@ss:word"
    assert parsed.database == "aia_ci"
