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


def main() -> None:
    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    py = python_in_venv()
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", "requirements.txt"])

    if ENV_EXAMPLE.exists() and not ENV_FILE.exists():
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)

    for target in RUNTIME_DIRS:
        target.mkdir(parents=True, exist_ok=True)

    print("[bootstrap] completed")
    print(f"[bootstrap] venv: {VENV_DIR}")
    print(f"[bootstrap] env : {ENV_FILE}")
    print("[bootstrap] next:")
    print(f"  {py} scripts/run_local_aia.py")


if __name__ == "__main__":
    main()
