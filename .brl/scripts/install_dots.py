#!/usr/bin/env python3
"""Link dot files to the home directory."""

import logging
import os
import sys
from fnmatch import fnmatch
from glob import has_magic
from pathlib import Path

import git


_DRY_RUN = bool(str(os.getenv("_DRY_RUN", "")))
_LOG_LEVEL = logging.INFO
logging.basicConfig(level=_LOG_LEVEL)


def contains_any(string: str, substrings) -> bool:
    """Check if string contains any of the substrings."""
    for substring in substrings:
        if substring in string:
            logging.debug(f"{string} contains {substring}")
            return True
        if has_magic(substring) and fnmatch(string, substring):
            logging.debug(f"{string} matches {substring}")
            return True
    return False


def link_dots(dotfile_dir: str, dry_run: bool = _DRY_RUN) -> None:
    """Link dot files in directory."""
    if not os.path.isdir(dotfile_dir):
        print("Directory %s does not exist" % dotfile_dir)
        sys.exit(1)
    dotfile_path = Path(dotfile_dir)
    repo = git.Repo(str(dotfile_path), search_parent_directories=True)
    ignore = set()
    for file in [".ignore"]:
        ignore_file = dotfile_path / file
        if ignore_file.exists():
            ignore.add(ignore_file.read_text().split("\n"))
    ignore = set(filter(bool, ignore))
    links_file = dotfile_path / "links.local"
    links = []
    if links_file.exists():
        _links = links_file.read_text().split("\n")
        for link in sorted(set(filter(bool, _links))):
            _link = Path(link)
            if _link.is_symlink():
                src = _link.resolve()
                dst = (Path().home() / src.relative_to(dotfile_path)).resolve()
                if src == dst and not dst.exists():
                    print(f"Removing bad link: {link}")
                    if not dry_run:
                        _link.unlink(missing_ok=True)
                else:
                    if src != dst:
                        print(
                            "Source and destination do not match: "
                            f"{link} -> {src} -> {dst}",
                        )
                    links.append(link)
            else:
                print(f"Removing missing link: {link}")
    print()
    if links:
        logging.debug("Existing links:\n%s\n", "\n".join(links))
    files = set(map(str, dotfile_path.rglob("*")))
    ignored = set(repo.ignored(*files))
    logging.debug("\n\nFile count: %d", len(files))
    files = files - ignored
    logging.debug("File count: %d\n\n", len(files))
    logging.debug("Ignored files:\n%s\n", "\n".join(sorted(map(str, ignored))))
    for src in map(Path, sorted(files)):
        if src.is_file():
            dst = Path().home() / src.relative_to(dotfile_path)
            if contains_any(str(src), ignore):
                logging.debug("Ignoring: %s", dst)
            elif dst.exists() and not dst.is_symlink():
                print("Skipping existing file: %s" % dst)
            else:
                print(f"Linking {src} to {dst}")
                not_known = str(dst) not in links
                if not_known:
                    links.append(str(dst))
                if not dry_run:
                    if dst.is_symlink():
                        os.remove(dst)
                    if not dst.parent.exists():
                        os.makedirs(dst.parent)
                    if not_known:
                        links_file.write_text("\n".join([*sorted(set(links)), ""]))
                    os.symlink(src, dst)
    print()
    logging.info("\nKnown links:\n%s\n", "\n".join(links))


if __name__ == "__main__":
    dotfile_dir = str(Path.home() / "dotfiles") if len(sys.argv) < 2 else sys.argv[1]
    link_dots(dotfile_dir)
