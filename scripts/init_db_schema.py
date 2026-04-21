from pathlib import Path
import os


def main() -> None:
    schema_path = Path(__file__).resolve().parent.parent / "sql" / "aia_robot_schema.sql"
    if not schema_path.exists():
        raise SystemExit(f"schema file not found: {schema_path}")

    print("[init-db] schema file ready")
    print(f"[init-db] path: {schema_path}")
    print("[init-db] import this file into your MySQL/MariaDB database.")
    print("[init-db] example:")
    print("  mysql -u root -p your_database < sql/aia_robot_schema.sql")
    print("[init-db] after import, set DB_BRIDGE_BACKEND and DB_BRIDGE_MYSQL_DSN in .env")
    if os.environ.get("DB_BRIDGE_BACKEND"):
        print(f"[init-db] current backend: {os.environ.get('DB_BRIDGE_BACKEND')}")


if __name__ == "__main__":
    main()
