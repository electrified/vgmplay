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
import re
from typing import Optional


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
    parser.add_argument(
        "--max-size",
        type=str,
        default=None,
        help=("Only keep decompressed files smaller than this size. "
              "Accepts bytes or suffixes like 40K, 2M. Example: 40K"),
    )
    parser.add_argument(
        "--flat-output",
        action="store_true",
        help="Write all output files into a single directory instead of preserving tree structure",
    )
    return parser.parse_args()


def parse_size(size_str: Optional[str]) -> Optional[int]:
    """Parse human readable size like '40K', '2M' into integer bytes.

    Returns None if size_str is falsy.
    """
    if not size_str:
        return None
    s = str(size_str).strip()
    m = re.fullmatch(r"(?i)\s*(\d+(?:\.\d+)?)\s*([kmgtp]?b?)?\s*", s)
    if not m:
        raise argparse.ArgumentTypeError(f"Invalid size: {size_str}")
    num = float(m.group(1))
    unit = (m.group(2) or "").upper()
    if unit.startswith("K"):
        num *= 1024
    elif unit.startswith("M"):
        num *= 1024 ** 2
    elif unit.startswith("G"):
        num *= 1024 ** 3
    elif unit.startswith("T"):
        num *= 1024 ** 4
    return int(num)


def find_vgz_files(base_dir: Path) -> Iterator[Path]:
    """Yield all .vgz files under base_dir recursively."""
    return base_dir.rglob("*.vgz")



def _get_unique_flat_path(output_dir: Path, name: str) -> Path:
    """Return a unique path in output_dir for filename `name`.

    If a file with the same name exists, append `-1`, `-2`, etc before the
    extension until a free name is found.
    """
    candidate = output_dir / name
    if not candidate.exists():
        return candidate
    # split name and ext
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = name, ""
    i = 1
    while True:
        candidate = output_dir / f"{stem}-{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1


def decompress_vgz(
    vgz_path: Path,
    out_path: Path,
    skip_existing: bool = False,
    max_size: Optional[int] = None,
) -> bool:
    """Decompress a .vgz file into .vgm format.

    Writes to a temporary '.part' file and only moves it into place if
    successful and within `max_size` (if provided).

    Returns True if the output file was created/kept, False otherwise.
    """
    # Basic skip-existing behaviour
    if skip_existing and out_path.exists():
        logging.info("Skipping (exists): %s", out_path)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = out_path.with_name(out_path.name + ".part")
    try:
        total = 0
        with gzip.open(vgz_path, "rb") as f_in, temp_path.open("wb") as f_temp:
            while True:
                chunk = f_in.read(65536)
                if not chunk:
                    break
                f_temp.write(chunk)
                total += len(chunk)
                if max_size is not None and total > max_size:
                    # exceeded allowed size; clean up and skip
                    logging.info(
                        "Discarding %s: decompressed size %d exceeds max %d",
                        vgz_path,
                        total,
                        max_size,
                    )
                    f_temp.close()
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                    return False

        # Move temp into final location (replace if needed)
        try:
            temp_path.replace(out_path)
        except Exception:
            # fallback to rename
            temp_path.rename(out_path)

        logging.info("Decompressed: %s -> %s (size=%d)", vgz_path, out_path, total)
        return True
    except Exception as e:
        logging.error("Failed to decompress %s: %s", vgz_path, e)
        try:
            temp_path.unlink()
        except Exception:
            pass
        return False


def main() -> None:
    args = parse_args()
    max_size = None
    try:
        max_size = parse_size(args.max_size)
    except Exception as e:
        logging.error("Invalid --max-size value: %s", e)
        raise SystemExit(2)

    if not args.input_dir.is_dir():
        logging.error("Input directory does not exist: %s", args.input_dir)
        raise SystemExit(1)

    for vgz_path in find_vgz_files(args.input_dir):
        if args.flat_output:
            # use only the filename in the output directory
            args.output_dir.mkdir(parents=True, exist_ok=True)
            dest_name = vgz_path.with_suffix(".vgm").name
            dest_path = args.output_dir / dest_name
            if args.skip_existing and dest_path.exists():
                logging.info("Skipping (exists): %s", dest_path)
                continue
            out_path = _get_unique_flat_path(args.output_dir, dest_name)
        else:
            rel_path = vgz_path.relative_to(args.input_dir).with_suffix(".vgm")
            out_path = args.output_dir / rel_path

        decompress_vgz(
            vgz_path,
            out_path,
            skip_existing=args.skip_existing,
            max_size=max_size,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
