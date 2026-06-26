"""Convert a datalake JSONL file to Parquet."""

import argparse
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATALAKE = REPO_ROOT / "datalake"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="JSONL → Parquet in datalake/")
    parser.add_argument(
        "input",
        nargs="?",
        default=str(DEFAULT_DATALAKE / "execution.jsonl"),
        help="Path to JSONL file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output Parquet path (default: same stem .parquet next to input)",
    )
    args = parser.parse_args(argv)

    src = Path(args.input)
    dst = Path(args.output) if args.output else src.with_suffix(".parquet")
    dst.parent.mkdir(parents=True, exist_ok=True)

    df = pl.read_ndjson(src)
    df.write_parquet(dst, compression="zstd")
    print(f"wrote {dst} ({df.height} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
