import argparse
import os
import sys
import time
from typing import Iterable, Tuple


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def _file_type(path: str) -> str:
    try:
        if os.path.islink(path):
            return "link"
        if os.path.isdir(path):
            return "dir"
        if os.path.isfile(path):
            return "file"
    except OSError:
        return "other"
    return "other"


def _format_mtime(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _birth_time_epoch(st: os.stat_result) -> int:
    return int(getattr(st, "st_birthtime", 0) or 0)


def _walk_entries(
    root: str,
    include_dirs: bool,
    exclude_hidden: bool,
) -> Iterable[Tuple[str, os.stat_result, str]]:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        if exclude_hidden:
            dirnames[:] = [d for d in dirnames if not _is_hidden(d)]
            filenames = [f for f in filenames if not _is_hidden(f)]

        if include_dirs:
            try:
                st = os.lstat(dirpath)
                yield dirpath, st, "dir"
            except OSError:
                pass

        # Capture symlinked directories (not walked into)
        for d in dirnames:
            path = os.path.join(dirpath, d)
            if os.path.islink(path):
                try:
                    st = os.lstat(path)
                    yield path, st, "link"
                except OSError:
                    pass

        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                st = os.lstat(path)
            except OSError:
                continue
            yield path, st, _file_type(path)


def _count_entries(root: str, include_dirs: bool, exclude_hidden: bool) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        if exclude_hidden:
            dirnames[:] = [d for d in dirnames if not _is_hidden(d)]
            filenames = [f for f in filenames if not _is_hidden(f)]

        if include_dirs:
            total += 1

        for d in dirnames:
            path = os.path.join(dirpath, d)
            if os.path.islink(path):
                total += 1

        total += len(filenames)

    return total


def _print_progress(done: int, total: int) -> None:
    if total <= 0:
        return
    width = 30
    filled = int(width * done / total)
    bar = "#" * filled + "-" * (width - filled)
    percent = done * 100 / total
    sys.stderr.write(f"\r[{bar}] {percent:6.2f}% ({done}/{total})")
    sys.stderr.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dump a recursive file listing with timestamps to a TSV file."
    )
    parser.add_argument("root", help="Root folder to scan")
    parser.add_argument("output", help="Output TSV file path")
    parser.add_argument(
        "--no-dirs",
        action="store_true",
        help="Exclude directories from the output",
    )
    parser.add_argument(
        "--exclude-hidden",
        action="store_true",
        help="Exclude hidden files and directories",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show a progress bar with ETA (extra count pass)",
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=200,
        help="Update progress every N entries (default: 200)",
    )

    args = parser.parse_args()
    root = os.path.abspath(args.root)
    output = os.path.abspath(args.output)
    include_dirs = not args.no_dirs
    exclude_hidden = args.exclude_hidden

    total = 0
    if args.progress:
        total = _count_entries(root, include_dirs, exclude_hidden)

    os.makedirs(os.path.dirname(output), exist_ok=True)

    done = 0
    with open(output, "w", encoding="utf-8") as f:
        f.write("type\tbirth_time_epoch\tmodified_time\tsize_bytes\tpath\n")
        for path, st, ftype in _walk_entries(root, include_dirs, exclude_hidden):
            rel = path
            btime = _birth_time_epoch(st)
            mtime = _format_mtime(st.st_mtime)
            f.write(f"{ftype}\t{btime}\t{mtime}\t{st.st_size}\t{rel}\n")
            done += 1
            if args.progress and (
                done % args.progress_interval == 0 or done == total
            ):
                _print_progress(done, total)

    if args.progress:
        _print_progress(total, total)
        sys.stderr.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
