import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
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
    if ENV_FILE.exists():
        text = ENV_FILE.read_text(encoding="utf-8")
        if "DB_BRIDGE_BACKEND=sqlite" not in text and "DB_BRIDGE_BACKEND=" in text:
            text = text.replace("DB_BRIDGE_BACKEND=mysql", "DB_BRIDGE_BACKEND=sqlite")
            text = text.replace("DB_BRIDGE_BACKEND=postgresql", "DB_BRIDGE_BACKEND=sqlite")
        if "STATE_STORE_MODE=memory" not in text and "STATE_STORE_MODE=" in text:
            text = text.replace("STATE_STORE_MODE=redis", "STATE_STORE_MODE=memory")
        if "ENABLE_API_KEY_AUTH=false" not in text and "ENABLE_API_KEY_AUTH=" in text:
            text = text.replace("ENABLE_API_KEY_AUTH=true", "ENABLE_API_KEY_AUTH=false")
        ENV_FILE.write_text(text, encoding="utf-8")


def ensure_runtime_dirs() -> None:
    for target in RUNTIME_DIRS:
        target.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("[one-click] preparing environment")
    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    py = python_in_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", "requirements.txt"])

    ensure_env()
    ensure_runtime_dirs()

    os.environ.setdefault("APP_HOST", "127.0.0.1")
    os.environ.setdefault("APP_PORT", "8000")
    os.environ.setdefault("DB_BRIDGE_BACKEND", "sqlite")
    os.environ.setdefault("STATE_STORE_MODE", "memory")
    os.environ.setdefault("ENABLE_API_KEY_AUTH", "false")

    print("[one-click] startup summary")
    print("[one-click] mode : local single-host")
    print("[one-click] db   : sqlite (default one-click mode)")
    print("[one-click] store: memory (safe one-click mode)")
    print("[one-click] auth : disabled (safe beginner mode)")
    print("[one-click] host : 127.0.0.1:8000")
    print("[one-click] next : use Java 8 adapter under integration/java8/")
    run([py, "scripts/run_local_aia.py"])


if __name__ == "__main__":
    main()
