from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path

from breakerledger import __version__ as VERSION

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"expected exit {expected}, got {result.returncode}: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def main() -> int:
    dist = ROOT / "dist"
    wheel = dist / f"breakerledger-{VERSION}-py3-none-any.whl"
    source = dist / f"breakerledger-{VERSION}.tar.gz"
    if not wheel.is_file() or not source.is_file():
        raise FileNotFoundError("release artifacts missing; run `uv build` first")

    with tempfile.TemporaryDirectory() as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        if sys.platform == "win32":
            python = environment / "Scripts" / "python.exe"
            command = environment / "Scripts" / "breakerledger.exe"
        else:
            python = environment / "bin" / "python"
            command = environment / "bin" / "breakerledger"

        run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)])
        version = run([str(command), "--version"])
        if version.stdout.strip() != f"breakerledger {VERSION}":
            raise AssertionError(
                f"unexpected installed version: {version.stdout.strip()}"
            )

        healthy = ROOT / "examples" / "healthy-house"
        conflict = ROOT / "examples" / "conflicting-house"
        output = Path(temporary) / "healthy-output"
        conflict_output = Path(temporary) / "conflict-output"
        run([str(command), "validate", str(healthy)])
        run([str(command), "audit", str(healthy), "--output", str(output)])
        run(
            [str(command), "audit", str(conflict), "--output", str(conflict_output)],
            expected=2,
        )
        for directory in (output, conflict_output):
            for filename in (
                "mapping.csv",
                "directory.csv",
                "retest.csv",
                "summary.json",
                "report.html",
            ):
                if not (directory / filename).is_file():
                    raise AssertionError(f"installed command did not write {filename}")

    print("Built wheel and sdist passed isolated package verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
