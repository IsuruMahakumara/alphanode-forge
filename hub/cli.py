"""Headless entrypoint — no charts, no desktop UI."""

import argparse
import sys

from forge.execution.state import init_db


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alpha-forge",
        description="AlphaNode Forge: headless quant research factory",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=("status", "init-db"),
        help="init-db: create systematic state schema; status: print mode",
    )
    args = parser.parse_args(argv)

    if args.command == "init-db":
        init_db()
        print("systematic state DB initialized")
        return 0

    print("mode: headless (Simons — no charts, no PyQt)")
    print("packages: forge (features, signals, execution) · hub (cli only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
