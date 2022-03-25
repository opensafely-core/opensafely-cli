import gzip
import sys
from pathlib import Path

DESCRIPTION = "Unzip a compressesd .csv.gz or .dta.gz file for local viewing"


def add_arguments(parser):
    parser.add_argument(
        "path", help="path to unzip. If a directory, unzip all .gz files in it"
    )


def main(path):
    p = Path(path)
    if p.is_dir():
        paths = p.glob("**/*.gz")
    else:
        if not p.exists():
            sys.exit(f"{p} does not exist")
        paths = [p]

    for p in paths:
        uncompressed = p.with_suffix("")  # strip .gz
        if uncompressed.exists():
            if uncompressed.stat().st_mtime > p.stat().st_mtime:
                print(f"{p} already unzipped to {uncompressed}")
                continue

        unzip(p, uncompressed)
        print(f"{p} unzipped to {uncompressed}")


def unzip(src_path, dst_path):
    try:
        tmp = dst_path.with_suffix(".tmp")
        with tmp.open("wb") as dst:
            with gzip.open(src_path) as src:
                while block := src.read(8192):
                    dst.write(block)
    except Exception:
        tmp.unlink(missing_ok=True)
    else:
        # replace works better than rename on windows
        tmp.replace(dst_path)
