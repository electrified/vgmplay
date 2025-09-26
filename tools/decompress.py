#!/usr/bin/env python3
"""
vgz2vgm.py - Recursively decompress .vgz files into .vgm files

Usage:
    ./vgz2vgm.py INPUT_DIR OUTPUT_DIR

Example:
    ./vgz2vgm.py /music/vgz /music/vgm
"""

import argparse
import gzip
import logging
from pathlib import Path
from typing import Iterator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively decompress .vgz files into .vgm files."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing .vgz files")
    parser.add_argument("output_dir", type=Path, help="Directory to write .vgm files")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files if the output .vgm already exists",
    )
    return parser.parse_args()


def find_vgz_files(base_dir: Path) -> Iterator[Path]:
    """Yield all .vgz files under base_dir recursively."""
    return base_dir.rglob("*.vgz")


def decompress_vgz(vgz_path: Path, out_path: Path, skip_existing: bool = False) -> None:
    """Decompress a .vgz file into .vgm format."""
    if skip_existing and out_path.exists():
        logging.info("Skipping (exists): %s", out_path)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with gzip.open(vgz_path, "rb") as f_in, out_path.open("wb") as f_out:
            f_out.write(f_in.read())
        logging.info("Decompressed: %s -> %s", vgz_path, out_path)
    except Exception as e:
        logging.error("Failed to decompress %s: %s", vgz_path, e)


def main() -> None:
    args = parse_args()

    if not args.input_dir.is_dir():
        logging.error("Input directory does not exist: %s", args.input_dir)
        raise SystemExit(1)

    for vgz_path in find_vgz_files(args.input_dir):
        rel_path = vgz_path.relative_to(args.input_dir).with_suffix(".vgm")
        out_path = args.output_dir / rel_path
        decompress_vgz(vgz_path, out_path, skip_existing=args.skip_existing)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
