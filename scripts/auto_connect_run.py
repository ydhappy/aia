import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"
RUNTIME_DIRS = [
    ROOT / "runtime",
    ROOT / "runtime" / "learning_journal",
]


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, cwd=str(ROOT))


def python_in_venv() -> str:
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def ensure_env() -> None:
    if ENV_EXAMPLE.exists() and not ENV_FILE.exists():
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)


def ensure_runtime_dirs() -> None:
    for target in RUNTIME_DIRS:
        target.mkdir(parents=True, exist_ok=True)


def main() -> None:
    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    py = python_in_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", "requirements.txt"])

    ensure_env()
    ensure_runtime_dirs()

    os.environ.setdefault("APP_HOST", "127.0.0.1")
    os.environ.setdefault("APP_PORT", "8000")

    print("[auto-connect-run] bootstrap complete")
    print("[auto-connect-run] AIA will run on 127.0.0.1:8000")
    print("[auto-connect-run] if you use MySQL/MariaDB, import sql/aia_robot_schema.sql first")
    run([py, "scripts/run_local_aia.py"])


if __name__ == "__main__":
    main()
