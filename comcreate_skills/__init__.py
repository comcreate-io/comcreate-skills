"""Portable, evidence-backed Agent Skills for Claude Code and Codex."""

from .core import (
    REPO_ROOT,
    ensure_executable,
    hash_directory,
    install,
    inventory_local,
    load_catalog,
    load_external_catalog,
    make_temporary_home,
    parse_frontmatter,
    path_exists,
    status,
    uninstall,
    validate_repository,
    write_json,
)

__all__ = [
    "REPO_ROOT",
    "ensure_executable",
    "hash_directory",
    "install",
    "inventory_local",
    "load_catalog",
    "load_external_catalog",
    "make_temporary_home",
    "parse_frontmatter",
    "path_exists",
    "status",
    "uninstall",
    "validate_repository",
    "write_json",
]
