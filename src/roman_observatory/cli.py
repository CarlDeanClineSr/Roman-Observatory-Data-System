"""Command-line interface for the Roman metadata-first bootstrap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .contracts import ContractError, validate_all
from .exporter import build_export
from .mast_catalog import run_mast_catalog
from .mast_client import MastError
from .source_watch import run_source_watch


def _root(value: str | None) -> Path:
    return Path(value or ".").resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roman-watch",
        description="Roman Observatory Data System metadata and provenance tools",
    )
    parser.add_argument("--project-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="validate every frozen v0.1 contract")

    source = sub.add_parser("source-watch", help="capture approved public pages")
    source.add_argument("--outdir", type=Path, required=True)
    source.add_argument("--previous-manifest", type=Path, default=None)

    mast = sub.add_parser("mast-catalog", help="query bounded MAST metadata only")
    mast.add_argument("--outdir", type=Path, required=True)

    export = sub.add_parser("export", help="build a small NVCPP astronomical export")
    export.add_argument("--source-manifest", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    root = _root(args.project_root)
    try:
        if args.command == "validate":
            result = validate_all(root)
        elif args.command == "source-watch":
            result = run_source_watch(
                sources_path=root / "config/sources.v1.json",
                policy_path=root / "config/download_policy.v1.json",
                outdir=args.outdir,
                previous_manifest=args.previous_manifest,
            )
        elif args.command == "mast-catalog":
            result = run_mast_catalog(
                config_path=root / "config/mast_metadata.v1.json",
                outdir=args.outdir,
            )
        elif args.command == "export":
            result = build_export(
                source_manifest=args.source_manifest,
                contract_path=root / "config/nvcpp_export_contract.v1.json",
                out_path=args.out,
            )
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except (ContractError, MastError, ValueError, OSError) as exc:
        print(f"[ROMAN-SYSTEM-ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    if isinstance(result, dict) and result.get("status") == "FAILED":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
