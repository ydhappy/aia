import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
JAVA_OUT = ROOT / "build" / "java8-classes"


def run(cmd: list[str]) -> None:
    print("[quality]", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))


def compile_python() -> None:
    run([PYTHON, "-m", "compileall", "-q", "app", "runners", "tests"])


def run_pytest() -> None:
    focused = [
        "tests/test_health_details.py",
        "tests/test_mysql_helper.py",
        "tests/test_robot_crud_api.py",
        "tests/test_robot_spawn_request_api.py",
        "tests/test_spawn_request_dashboard.py",
        "tests/test_spawn_request_dashboard_renderer.py",
        "tests/test_mysql55_schema_compat.py",
    ]
    for target in focused:
        run([PYTHON, "-m", "pytest", target])
    run([PYTHON, "-m", "pytest"])


def pip_check() -> None:
    run([PYTHON, "-m", "pip", "check"])


def compile_java() -> None:
    javac = os.environ.get("JAVAC", "javac")
    if shutil.which(javac) is None:
        print("[quality] JAVA8_COMPILE=SKIPPED_JAVAC_NOT_FOUND")
        return
    java_files = [str(path) for path in (ROOT / "integration" / "java8").glob("*.java")]
    examples_dir = ROOT / "examples" / "java8"
    if examples_dir.exists():
        java_files.extend(str(path) for path in examples_dir.glob("*.java"))
    if not java_files:
        print("[quality] JAVA8_COMPILE=SKIPPED_NO_JAVA_FILES")
        return
    if JAVA_OUT.exists():
        shutil.rmtree(JAVA_OUT)
    JAVA_OUT.mkdir(parents=True, exist_ok=True)
    run([javac, "-encoding", "UTF-8", "-d", str(JAVA_OUT)] + java_files)
    print("[quality] JAVA8_COMPILE=0")


def main() -> None:
    compile_python()
    print("[quality] COMPILEALL_EXIT=0")
    run_pytest()
    print("[quality] PYTEST_EXIT=0")
    pip_check()
    print("[quality] PIP_CHECK_EXIT=0")
    compile_java()
    print("[quality] AIA_QUALITY_GATES=PASS")


if __name__ == "__main__":
    main()
