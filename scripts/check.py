from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from breakerledger.audit import compile_project  # noqa: E402
from breakerledger.io import load_project  # noqa: E402
from breakerledger.reports import REPORT_FILENAMES, write_reports  # noqa: E402

FORBIDDEN_RUNTIME_IMPORTS = {
    "http",
    "importlib",
    "requests",
    "socket",
    "subprocess",
    "urllib",
}
REQUIRED_DOCS = (
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/RESEARCH.md",
    "docs/SPEC.md",
    "docs/THREAT_MODEL.md",
    "docs/REPAIR.md",
    "docs/RELEASE.md",
)
SECRET_PATTERNS = (
    re.compile("gh" + "p_[A-Za-z0-9]{20,}"),
    re.compile("github" + "_pat_[A-Za-z0-9_]{20,}"),
    re.compile("AK" + "IA[0-9A-Z]{16}"),
    re.compile("BEGIN (?:RSA |EC |OPENSSH )?PRIVATE" + " KEY"),
)


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def check_runtime_imports() -> None:
    for path in sorted((SRC / "breakerledger").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: tuple[str, ...]
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names = (node.module or "",)
            else:
                continue
            for name in names:
                module = name.partition(".")[0]
                if module in FORBIDDEN_RUNTIME_IMPORTS:
                    raise AssertionError(f"forbidden runtime import {module}: {path}")


def check_examples() -> None:
    expected = {
        "healthy-house": {
            "confirmed": 5,
            "tentative": 0,
            "unmapped": 0,
            "conflict": 0,
        },
        "conflicting-house": {
            "confirmed": 0,
            "tentative": 1,
            "unmapped": 1,
            "conflict": 2,
        },
    }
    for name, counts in expected.items():
        project = load_project(ROOT / "examples" / name)
        audit = compile_project(project)
        if audit.status_counts != counts:
            raise AssertionError(f"{name}: {audit.status_counts} != {counts}")
        with (
            tempfile.TemporaryDirectory() as first_dir,
            tempfile.TemporaryDirectory() as second_dir,
        ):
            first = Path(first_dir)
            second = Path(second_dir)
            write_reports(project, audit, first, confirmations=2)
            write_reports(project, audit, second, confirmations=2)
            for filename in REPORT_FILENAMES:
                if (first / filename).read_bytes() != (second / filename).read_bytes():
                    raise AssertionError(f"non-deterministic report: {name}/{filename}")


def check_docs_and_secrets() -> None:
    for relative in REQUIRED_DOCS:
        path = ROOT / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"required documentation missing or empty: {relative}")

    extensions = {".csv", ".md", ".py", ".toml", ".yaml", ".yml"}
    excluded = {".git", ".mypy_cache", ".ruff_cache", ".venv", "dist"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if any(part in excluded for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise AssertionError(f"possible credential in {path.relative_to(ROOT)}")


def main() -> int:
    run(sys.executable, "-m", "ruff", "format", "--check", ".")
    run(sys.executable, "-m", "ruff", "check", ".")
    run(sys.executable, "-m", "mypy")
    run(sys.executable, "-m", "compileall", "-q", "src")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
    check_runtime_imports()
    check_examples()
    check_docs_and_secrets()
    print("BreakerLedger acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
