from __future__ import annotations

import json
import re
import sys
from typing import Any

from .core import (
    install,
    inventory_local,
    load_catalog,
    load_external_catalog,
    status,
    uninstall,
    validate_repository,
    write_json,
)

HELP = """comcreate-skills

Commands:
  inventory [--out FILE] [--home DIR] [--since-days N] [--no-usage]
            [--no-defaults] [--root RUNTIME=PATH]
  list [--json]
  validate [--json]
  install --target codex|claude|both [--profile core|SKILL] [--mode copy|link]
          [--home DIR] [--state FILE]
  status [--json] [--home DIR] [--state FILE]
  uninstall [--profile core|SKILL] [--home DIR] [--state FILE]
"""


def help_text() -> None:
    print(HELP)


def parse(argv: list[str]) -> tuple[str | None, dict[str, Any]]:
    command = argv[0] if argv else None
    rest = argv[1:] if argv else []
    options: dict[str, Any] = {"roots": []}
    index = 0
    while index < len(rest):
        argument = rest[index]
        if argument == "--json":
            options["json"] = True
        elif argument == "--no-usage":
            options["usage"] = False
        elif argument == "--no-defaults":
            options["defaults"] = False
        elif argument.startswith("--"):
            key = re.sub(r"-([a-z])", lambda match: match.group(1).upper(), argument[2:])
            value = rest[index + 1] if index + 1 < len(rest) else None
            if not value or value.startswith("--"):
                raise RuntimeError(f"missing value for {argument}")
            index += 1
            if key == "root":
                separator = value.find("=")
                if separator < 1:
                    raise RuntimeError("--root must use RUNTIME=PATH")
                runtime = value[:separator]
                if runtime not in {"codex", "claude-code"}:
                    raise RuntimeError("--root runtime must be codex or claude-code")
                options["roots"].append(
                    {"runtime": runtime, "path": value[separator + 1 :]}
                )
            elif key == "sinceDays":
                try:
                    since_days = int(value, 10)
                except ValueError as error:
                    raise RuntimeError("--since-days must be a positive integer") from error
                if since_days < 1:
                    raise RuntimeError("--since-days must be a positive integer")
                options["sinceDays"] = since_days
            else:
                options[key] = value
        else:
            raise RuntimeError(f"unexpected argument: {argument}")
        index += 1
    return command, options


def print_rows(rows: list[dict[str, Any]], fields: list[dict[str, str]]) -> None:
    if not rows:
        print("No entries.")
        return
    widths = []
    for field in fields:
        width = len(field["label"])
        for row in rows:
            value = row.get(field["key"])
            text = "" if value is None else str(value)
            width = max(width, len(text))
        widths.append(width)
    print(
        "  ".join(
            field["label"].ljust(widths[index]) for index, field in enumerate(fields)
        )
    )
    for row in rows:
        print(
            "  ".join(
                ("" if row.get(field["key"]) is None else str(row.get(field["key"]))).ljust(
                    widths[index]
                )
                for index, field in enumerate(fields)
            )
        )


def _dumps(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def run(argv: list[str] | None = None) -> int:
    command, options = parse(sys.argv[1:] if argv is None else argv)
    if not command or command in {"help", "--help"}:
        help_text()
        return 0

    if command == "inventory":
        report = inventory_local(options)
        if options.get("out"):
            write_json(options["out"], report)
            print(
                f"Wrote {len(report['skills'])} sanitized skill records to {options['out']}"
            )
        else:
            print(_dumps(report))
        return 0

    if command == "list":
        catalog = load_catalog()
        external = load_external_catalog()
        rows = [
            *[
                {
                    "name": skill["name"],
                    "status": skill["status"],
                    "category": skill["category"],
                }
                for skill in catalog["skills"]
            ],
            *[
                {
                    "name": skill["name"],
                    "status": "external",
                    "category": skill["category"],
                }
                for skill in external["skills"]
            ],
        ]
        if options.get("json"):
            print(_dumps(rows))
        else:
            print_rows(
                rows,
                [
                    {"key": "name", "label": "NAME"},
                    {"key": "status", "label": "STATUS"},
                    {"key": "category", "label": "CATEGORY"},
                ],
            )
        return 0

    if command == "validate":
        errors = validate_repository()
        if options.get("json"):
            print(_dumps({"valid": len(errors) == 0, "errors": errors}))
        elif not errors:
            print("Repository is valid.")
        else:
            print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1 if errors else 0

    if command == "install":
        records = install(options)
        print_rows(
            records,
            [
                {"key": "skill", "label": "SKILL"},
                {"key": "runtime", "label": "RUNTIME"},
                {"key": "mode", "label": "MODE"},
            ],
        )
        return 0

    if command == "status":
        rows = status(options)
        if options.get("json"):
            print(_dumps(rows))
        else:
            print_rows(
                rows,
                [
                    {"key": "skill", "label": "SKILL"},
                    {"key": "runtime", "label": "RUNTIME"},
                    {"key": "mode", "label": "MODE"},
                    {"key": "state", "label": "STATE"},
                ],
            )
        return 1 if any(row["state"] != "current" for row in rows) else 0

    if command == "uninstall":
        rows = uninstall(options)
        print_rows(
            rows,
            [
                {"key": "skill", "label": "SKILL"},
                {"key": "runtime", "label": "RUNTIME"},
                {"key": "mode", "label": "MODE"},
            ],
        )
        return 0

    raise RuntimeError(f"unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except Exception as error:
        print(f"comcreate-skills: {error}", file=sys.stderr)
        return 1
