#!/usr/bin/env python3
"""Link dotfiles from a specified directory to the home directory."""

import logging
import os
import sys
from fnmatch import fnmatch
from glob import has_magic
from pathlib import Path
from collections.abc import Iterable

import git

_DRY_RUN = bool(str(os.getenv("_DRY_RUN", "")))
_LOG_LEVEL = logging.INFO
logging.basicConfig(level=_LOG_LEVEL)


def contains_any(string: str, substrings: Iterable[str]) -> bool:
    """Check if the string contains any of the substrings.

    Args:
        string: The string to check.
        substrings: An iterable of substrings to look for.

    Returns:
        True if any substring is found in the string; False otherwise.

    """
    for substring in substrings:
        if substring in string:
            logging.debug("%s contains %s", string, substring)
            return True
        if has_magic(substring) and fnmatch(string, substring):
            logging.debug("%s matches %s", string, substring)
            return True
    return False


def parse_arguments() -> str:
    """Parse command-line arguments to get the dotfile directory.

    Returns:
        The path to the dotfile directory.

    """
    default_path = Path.home() / "dotfiles"
    if len(sys.argv) > 1:
        return sys.argv[1]
    return str(default_path)


def verify_directory(dotfile_dir: str) -> Path:
    """Verify that the provided dotfile directory exists.

    Args:
        dotfile_dir: The path to the dotfile directory as a string.

    Returns:
        The dotfile directory path as a Path object.

    Raises:
        SystemExit: If the directory does not exist.

    """
    path = Path(dotfile_dir)
    if not path.is_dir():
        print(f"Directory {dotfile_dir} does not exist")
        sys.exit(1)
    return path


def load_ignore_patterns(dotfile_path: Path) -> set:
    """Load ignore patterns from specified ignore files.

    Args:
        dotfile_path: The path to the dotfile directory.

    Returns:
        A set of ignore patterns.

    """
    ignore_patterns = set()
    ignore_files = [".files/config/.ignore"]
    for ignore_file in ignore_files:
        path = dotfile_path / ignore_file
        if path.exists():
            with path.open() as f:
                ignore_patterns.update(filter(bool, f.read().splitlines()))
        else:
            print(f"Missing ignore file: {path}")
    return ignore_patterns


def load_existing_links(links_file: Path) -> list:
    """Load existing symlink paths from the links file.

    Args:
        links_file: The path to the links file.

    Returns:
        A list of existing link paths.

    """
    links = []
    if links_file.exists():
        with links_file.open() as f:
            links = [line.strip() for line in f if line.strip()]
    return links


def clean_up_links(links: list, dotfile_path: Path, *, dry_run: bool) -> list:
    """Remove invalid or outdated symlinks and update the links list.

    Args:
        links: A list of existing link paths.
        dotfile_path: The path to the dotfile directory.
        dry_run: If True, no changes will be made.

    Returns:
        An updated list of valid link paths.

    """
    valid_links = []
    for link in sorted(set(links)):
        link_path = Path(link)
        if link_path.is_symlink():
            src = link_path.resolve()
            dst = (Path.home() / src.relative_to(dotfile_path)).resolve()
            if src == dst and not dst.exists():
                print(f"Removing bad link: {link}")
                if not dry_run:
                    link_path.unlink(missing_ok=True)
            else:
                if src != dst:
                    print(
                        f"Source and destination do not match: {link} -> {src} -> {dst}"
                    )
                valid_links.append(link)
        else:
            print(f"Removing missing link: {link}")
    return valid_links


def get_files_to_link(dotfile_path: Path, repo) -> set:
    """Retrieve the set of files to be linked, excluding ignored files.

    Args:
        dotfile_path: The path to the dotfile directory.
        repo: The git repository object.

    Returns:
        A set of file paths to be linked.

    """
    all_files = set(str(p) for p in dotfile_path.rglob("*"))
    ignored_files = set(repo.ignored(*all_files))
    logging.debug("Ignored files:\n%s\n", "\n".join(sorted(ignored_files)))
    files_to_link = all_files - ignored_files
    return files_to_link


def link_files(
    files: set,
    dotfile_path: Path,
    ignore_patterns: set,
    links: list,
    links_file: Path,
    dry_run: bool,
):
    """Create symlinks for the specified files.

    Args:
        files: A set of file paths to link.
        dotfile_path: The path to the dotfile directory.
        ignore_patterns: A set of patterns for files to ignore.
        links: A list of existing link paths.
        links_file: The path to the links file.
        dry_run: If True, no changes will be made.

    """
    for src_str in sorted(files):
        src = Path(src_str)
        if src.is_file():
            if contains_any(str(src), ignore_patterns):
                logging.debug("Ignoring: %s", src)
                continue
            dst = Path.home() / src.relative_to(dotfile_path)
            if dst.exists() and not dst.is_symlink():
                logging.info("Skipping existing file: %s", dst)
                continue
            print(f"Linking {src} to {dst}")
            if str(dst) not in links:
                links.append(str(dst))
            if not dry_run:
                if dst.is_symlink():
                    dst.unlink()
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(src, dst)
    if not dry_run:
        links_file.write_text("\n".join(sorted(set(links))) + "\n")


def link_dots():
    """Link dotfiles."""
    dotfile_dir = parse_arguments()
    dotfile_path = verify_directory(dotfile_dir)
    repo = git.Repo(str(dotfile_path), search_parent_directories=True)
    ignore_patterns = load_ignore_patterns(dotfile_path)
    links_file = dotfile_path / "links.local"
    existing_links = load_existing_links(links_file)
    valid_links = clean_up_links(existing_links, dotfile_path, dry_run=_DRY_RUN)
    files_to_link = get_files_to_link(dotfile_path, repo)
    logging.debug("Files to link:\n%s\n", "\n".join(sorted(files_to_link)))
    link_files(
        files_to_link,
        dotfile_path,
        ignore_patterns,
        valid_links,
        links_file,
        _DRY_RUN,
    )
    print()
    logging.info("Known links:\n%s\n", "\n".join(valid_links))


if __name__ == "__main__":
    link_dots()
