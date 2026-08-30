from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .audit import compile_project
from .io import InputError, load_project
from .reports import ReportError, write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="breakerledger",
        description=(
            "Compile breaker test observations into an evidence-backed directory "
            "and retest queue."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"breakerledger {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="validate the three project CSV files"
    )
    validate.add_argument("project_dir", help="directory containing the input CSV files")

    audit = subparsers.add_parser(
        "audit", help="validate, compile, and write the five audit reports"
    )
    audit.add_argument("project_dir", help="directory containing the input CSV files")
    audit.add_argument("--output", required=True, help="report output directory")
    audit.add_argument(
        "--confirmations",
        type=_positive_int,
        default=2,
        help="lost-power observations required for confirmed status (default: 2)",
    )
    audit.add_argument(
        "--fail-on",
        choices=("unresolved", "conflict", "never"),
        default="unresolved",
        help="finding threshold that returns exit 2 (default: unresolved)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        project = load_project(args.project_dir)
        if args.command == "validate":
            print(
                "Valid project: "
                f"{len(project.breakers)} breakers, "
                f"{len(project.endpoints)} endpoints, "
                f"{len(project.observations)} observations"
            )
            return 0

        audit = compile_project(project, confirmations=args.confirmations)
        paths = write_reports(project, audit, args.output, args.confirmations)
    except (InputError, ReportError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    counts = " ".join(
        f"{status}={audit.status_counts[status]}"
        for status in ("confirmed", "tentative", "unmapped", "conflict")
    )
    print(f"Wrote {len(paths)} reports to {args.output}")
    if _fails_threshold(audit.status_counts, args.fail_on):
        print(f"Audit findings (--fail-on {args.fail_on}): {counts}", file=sys.stderr)
        return 2
    print(f"Audit clean for --fail-on {args.fail_on}: {counts}")
    return 0


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _fails_threshold(counts: dict[str, int], fail_on: str) -> bool:
    if fail_on == "never":
        return False
    if fail_on == "conflict":
        return counts["conflict"] > 0
    return counts["tentative"] + counts["unmapped"] + counts["conflict"] > 0
