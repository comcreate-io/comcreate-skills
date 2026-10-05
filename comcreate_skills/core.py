from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = str(Path(__file__).resolve().parent.parent)

SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORED_SEGMENTS = {
    ".git",
    "node_modules",
    "archive",
    "dist",
    "build",
    ".cache",
}

_FRONTMATTER = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)")
_FIELD = re.compile(r"^([a-zA-Z0-9_-]+):\s*(.*)$")
_CODEX_SKILL_PATH = re.compile(r"/([a-z0-9]+(?:-[a-z0-9]+)*)/SKILL\.md")
_CLAUDE_SKILL = re.compile(r'"skill"\s*:\s*"([a-z0-9:-]+)"')
_LOCAL_MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")
_CODEX_CWD = re.compile(r'"cwd"\s*:\s*"([^"]+)"')
_MANUAL_INVOCATION = re.compile(r"allow_implicit_invocation:\s*false")

_FORBIDDEN = [
    (re.compile(r"/home/[a-z0-9._-]+", re.I), "absolute Linux home path"),
    (re.compile(r"/Users/[a-z0-9._-]+", re.I), "absolute macOS home path"),
    (re.compile(r"C:\\Users\\", re.I), "absolute Windows home path"),
    (
        re.compile(r"\b(?:cartermccann|comcreate-io|telegram)\b", re.I),
        "private runtime assumption",
    ),
    (re.compile(r"~/\.Codex\b"), "legacy machine-specific state path"),
    (
        re.compile(r"\b(?:sk-[a-z0-9_-]{16,}|gh[opusr]_[a-z0-9]{16,})\b", re.I),
        "secret-like token",
    ),
]


def path_exists(path: str) -> bool:
    try:
        os.lstat(path)
        return True
    except OSError as error:
        if error.errno == errno.ENOENT or isinstance(error, FileNotFoundError):
            return False
        raise


def read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, value: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"{json.dumps(value, indent=2, ensure_ascii=False)}\n")


def parse_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER.match(text)
    if not match:
        raise RuntimeError("missing YAML frontmatter")

    fields: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        field = _FIELD.match(line)
        if not field:
            raise RuntimeError(f"unsupported frontmatter line: {raw_line}")
        value = field.group(2).strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        fields[field.group(1)] = value

    return {"fields": fields, "body": text[match.end() :], "raw": match.group(0)}


def _list_files(
    root: str,
    options: dict[str, Any] | None = None,
    depth: int = 0,
    prefix: str = "",
) -> list[dict[str, Any]]:
    options = options or {}
    max_depth = options.get("maxDepth", 20)
    include_hidden = options.get("includeHidden", True)
    if depth > max_depth:
        return []

    with os.scandir(root) as iterator:
        entries = sorted(
            iterator, key=lambda entry: (entry.name.casefold(), entry.name)
        )
    output: list[dict[str, Any]] = []

    for entry in entries:
        if not include_hidden and entry.name.startswith("."):
            continue
        if entry.name == ".git":
            continue
        absolute = os.path.join(root, entry.name)
        relative_path = f"{prefix}/{entry.name}" if prefix else entry.name

        if entry.is_dir(follow_symlinks=False):
            output.extend(_list_files(absolute, options, depth + 1, relative_path))
        elif entry.is_file(follow_symlinks=False):
            output.append({"absolute": absolute, "relative": relative_path})
        elif entry.is_symlink():
            try:
                target = os.path.realpath(absolute)
                target_stat = os.stat(target)
            except OSError:
                output.append(
                    {"absolute": absolute, "relative": relative_path, "broken": True}
                )
                continue
            if os.path.isdir(target):
                output.extend(_list_files(target, options, depth + 1, relative_path))
            else:
                output.append({"absolute": target, "relative": relative_path})

    return output


def hash_directory(root: str) -> str:
    digest = hashlib.sha256()
    for file in _list_files(root):
        digest.update(file["relative"].encode("utf-8"))
        if file.get("broken"):
            digest.update(b"BROKEN_LINK")
        else:
            with open(file["absolute"], "rb") as handle:
                digest.update(handle.read())
    return f"sha256:{digest.hexdigest()}"


def _opaque(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _skill_directories(root: str) -> list[str]:
    if not path_exists(root):
        return []
    root_skill = os.path.join(root, "SKILL.md")
    if path_exists(root_skill):
        return [root]

    output: list[str] = []
    try:
        entries = os.scandir(root)
    except OSError:
        return []
    with entries:
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
                continue
            candidate = os.path.join(root, entry.name)
            if path_exists(os.path.join(candidate, "SKILL.md")):
                output.append(candidate)
    return output


def _discover_project_skill_roots(base: str, max_depth: int = 5) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(current: str, depth: int) -> None:
        if depth > max_depth or not path_exists(current):
            return
        try:
            entries = list(os.scandir(current))
        except OSError:
            return

        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            if entry.name in IGNORED_SEGMENTS:
                continue
            absolute = os.path.join(current, entry.name)
            if entry.name in {".agents", ".claude"}:
                skills = os.path.join(absolute, "skills")
                if path_exists(skills):
                    found.append(
                        {
                            "path": skills,
                            "runtime": "codex" if entry.name == ".agents" else "claude-code",
                            "projectId": _opaque(current),
                        }
                    )
                continue
            if entry.name.startswith(".") and depth > 0:
                continue
            walk(absolute, depth + 1)

    walk(base, 0)
    return found


def _default_inventory_roots(home: str) -> list[dict[str, Any]]:
    return [
        {
            "label": "shared-user",
            "path": os.path.join(home, ".agents", "skills"),
            "runtimes": ["codex", "claude-code"],
            "projectId": None,
        },
        {
            "label": "codex-user",
            "path": os.path.join(home, ".codex", "skills"),
            "runtimes": ["codex"],
            "projectId": None,
        },
        {
            "label": "claude-import",
            "path": os.path.join(home, ".codex", "claude-import", "skills"),
            "runtimes": ["claude-code"],
            "projectId": None,
        },
    ]


def _iso_mtime(mtime: float) -> str:
    return (
        datetime.fromtimestamp(mtime, timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _extract_usage(home: str, since_days: int) -> dict[str, dict[str, Any]]:
    usage: dict[str, dict[str, Any]] = {}
    cutoff_ms = datetime.now(timezone.utc).timestamp() * 1000 - since_days * 24 * 60 * 60 * 1000

    def record(name: str, used_at: str, project_id: str | None) -> None:
        normalized = name.split(":")[-1] if ":" in name else name
        if not SKILL_NAME.match(normalized):
            return
        existing = usage.get(normalized)
        if existing is None:
            existing = {
                "invocationCount": 0,
                "lastUsed": None,
                "projects": set(),
            }
            usage[normalized] = existing
        existing["invocationCount"] += 1
        if not existing["lastUsed"] or used_at > existing["lastUsed"]:
            existing["lastUsed"] = used_at
        if project_id:
            existing["projects"].add(project_id)

    def scan_logs(root: str, runtime: str) -> None:
        if not path_exists(root):
            return
        for file in _list_files(root, {"maxDepth": 8}):
            if not file["relative"].endswith(".jsonl") or file.get("broken"):
                continue
            metadata = os.stat(file["absolute"])
            if metadata.st_mtime * 1000 < cutoff_ms or metadata.st_size > 25 * 1024 * 1024:
                continue

            with open(file["absolute"], encoding="utf-8", errors="replace") as handle:
                contents = handle.read()
            lines = re.split(r"\r?\n", contents)
            project_id = (
                _opaque(os.path.dirname(file["absolute"]))
                if runtime == "claude-code"
                else None
            )

            if runtime == "codex":
                for line in lines[:5]:
                    cwd = _CODEX_CWD.search(line)
                    if cwd:
                        project_id = _opaque(cwd.group(1))
                        break

            used_at = _iso_mtime(metadata.st_mtime)
            for line in lines:
                if runtime == "codex":
                    if "SKILL.md" not in line or (
                        "function_call" not in line and "custom_tool_call" not in line
                    ):
                        continue
                    for match in _CODEX_SKILL_PATH.finditer(line):
                        record(match.group(1), used_at, project_id)
                else:
                    if '"name":"Skill"' not in line and '"name": "Skill"' not in line:
                        continue
                    for match in _CLAUDE_SKILL.finditer(line):
                        record(match.group(1), used_at, project_id)

    scan_logs(os.path.join(home, ".codex", "sessions"), "codex")
    scan_logs(os.path.join(home, ".claude", "projects"), "claude-code")
    return usage


def inventory_local(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    home = os.path.abspath(options.get("home") or os.path.expanduser("~"))
    roots = [] if options.get("defaults") is False else _default_inventory_roots(home)

    for explicit in options.get("roots") or []:
        roots.append(
            {
                "label": "explicit",
                "path": os.path.abspath(explicit["path"]),
                "runtimes": [explicit["runtime"]],
                "projectId": explicit.get("projectId"),
            }
        )

    if options.get("defaults") is not False:
        for project_base in [
            os.path.join(home, "projects"),
            os.path.join(home, "Desktop", "projects"),
        ]:
            for project_root in _discover_project_skill_roots(project_base):
                roots.append(
                    {
                        "label": "project",
                        "path": project_root["path"],
                        "runtimes": [project_root["runtime"]],
                        "projectId": project_root["projectId"],
                    }
                )

    catalog = read_json(os.path.join(REPO_ROOT, "catalog", "skills.json"))
    external = read_json(os.path.join(REPO_ROOT, "catalog", "external.json"))
    status_by_name = {
        **{skill["name"]: skill["status"] for skill in catalog["skills"]},
        **{skill["name"]: "external" for skill in external["skills"]},
    }

    grouped: dict[str, dict[str, Any]] = {}
    for root in roots:
        for directory in _skill_directories(root["path"]):
            skill_file = os.path.join(directory, "SKILL.md")
            try:
                with open(skill_file, encoding="utf-8", errors="replace") as handle:
                    skill_text = handle.read()
            except OSError:
                continue

            try:
                fields = parse_frontmatter(skill_text)["fields"]
            except Exception:
                continue
            name = fields.get("name") or os.path.basename(directory)
            if not SKILL_NAME.match(name):
                continue

            try:
                canonical = os.path.realpath(directory)
            except OSError:
                canonical = directory
            content_hash = hash_directory(canonical)
            key = f"{name}|{content_hash}"
            current = grouped.get(key)
            if current is None:
                current = {
                    "name": name,
                    "status": status_by_name.get(name, "incubator"),
                    "runtimes": set(),
                    "projectIds": set(),
                    "canonicalIds": set(),
                    "contentHash": content_hash,
                }
                grouped[key] = current
            current["runtimes"].update(root["runtimes"])
            if root["projectId"]:
                current["projectIds"].add(root["projectId"])
            current["canonicalIds"].add(_opaque(canonical))

    usage = (
        {}
        if options.get("usage") is False
        else _extract_usage(
            home,
            90 if options.get("sinceDays") is None else options["sinceDays"],
        )
    )

    by_name: dict[str, dict[str, Any]] = {}
    for variant in grouped.values():
        current = by_name.get(variant["name"])
        if current is None:
            current = {
                "name": variant["name"],
                "status": variant["status"],
                "runtimes": set(),
                "projectIds": set(),
                "contentHashes": set(),
            }
            by_name[variant["name"]] = current
        current["runtimes"].update(variant["runtimes"])
        current["projectIds"].update(variant["projectIds"])
        current["contentHashes"].add(variant["contentHash"])

    skills = []
    for skill in by_name.values():
        observed = usage.get(skill["name"])
        project_ids = set(skill["projectIds"])
        if observed:
            project_ids.update(observed["projects"])
        skills.append(
            {
                "name": skill["name"],
                "status": skill["status"],
                "runtimes": sorted(skill["runtimes"]),
                "invocationCount": observed["invocationCount"] if observed else 0,
                "lastUsed": observed["lastUsed"] if observed else None,
                "projectCount": len(project_ids),
                "variantCount": len(skill["contentHashes"]),
                "contentHashes": sorted(skill["contentHashes"]),
            }
        )
    skills.sort(key=lambda item: (-item["invocationCount"], item["name"]))

    return {
        "schemaVersion": 1,
        "generatedAt": _now_iso(),
        "skills": skills,
    }


def _local_markdown_links(text: str) -> list[str]:
    links: list[str] = []
    for match in _LOCAL_MARKDOWN_LINK.finditer(text):
        target = match.group(1).split("#")[0]
        if not target or re.match(r"^[a-z]+://", target, re.I) or target.startswith("#"):
            continue
        links.append(target)
    return links


def validate_repository() -> list[str]:
    errors: list[str] = []
    catalog_path = os.path.join(REPO_ROOT, "catalog", "skills.json")
    external_path = os.path.join(REPO_ROOT, "catalog", "external.json")
    catalog = read_json(catalog_path)
    external = read_json(external_path)
    catalog_names: set[str] = set()

    for skill in catalog["skills"]:
        if skill["name"] in catalog_names:
            errors.append(f"duplicate catalog skill: {skill['name']}")
        catalog_names.add(skill["name"])

        for field in [
            "name",
            "version",
            "status",
            "category",
            "maintainers",
            "license",
            "provenance",
            "runtimes",
            "dependencies",
            "manualOnly",
        ]:
            if field not in skill or (
                skill[field] is None and field != "path"
            ):
                errors.append(f"{skill['name']}: missing catalog field {field}")

        if skill.get("status") != "core":
            continue
        if not skill.get("path"):
            errors.append(f"{skill['name']}: core skill has no path")
            continue

        skill_directory = os.path.join(REPO_ROOT, skill["path"])
        skill_file = os.path.join(skill_directory, "SKILL.md")
        if not path_exists(skill_file):
            errors.append(f"{skill['name']}: missing {skill['path']}/SKILL.md")
            continue

        with open(skill_file, encoding="utf-8") as handle:
            text = handle.read()
        try:
            frontmatter = parse_frontmatter(text)
        except Exception as error:
            errors.append(f"{skill['name']}: {error}")
            continue

        field_names = ",".join(sorted(frontmatter["fields"]))
        if field_names != "description,name":
            errors.append(
                f"{skill['name']}: SKILL.md frontmatter must contain only name and description"
            )
        if frontmatter["fields"].get("name") != skill["name"]:
            errors.append(
                f"{skill['name']}: frontmatter name does not match catalog and directory"
            )
        if not SKILL_NAME.match(frontmatter["fields"].get("name") or ""):
            errors.append(f"{skill['name']}: invalid Agent Skills name")
        description = frontmatter["fields"].get("description") or ""
        if not description or len(description) > 1024:
            errors.append(f"{skill['name']}: description must be 1-1024 characters")
        if "[TODO" in text or "TODO:" in text:
            errors.append(f"{skill['name']}: unresolved TODO")
        if len(re.split(r"\r?\n", text)) > 500:
            errors.append(f"{skill['name']}: SKILL.md exceeds 500 lines")

        for pattern, label in _FORBIDDEN:
            if pattern.search(text):
                errors.append(f"{skill['name']}: contains {label}")

        for link in _local_markdown_links(text):
            if not path_exists(os.path.abspath(os.path.join(skill_directory, link))):
                errors.append(f"{skill['name']}: broken reference {link}")

        openai_yaml = os.path.join(skill_directory, "agents", "openai.yaml")
        if not path_exists(openai_yaml):
            errors.append(f"{skill['name']}: missing agents/openai.yaml")
        elif skill.get("manualOnly"):
            with open(openai_yaml, encoding="utf-8") as handle:
                metadata = handle.read()
            if not _MANUAL_INVOCATION.search(metadata):
                errors.append(
                    f"{skill['name']}: manual-only skill must disable Codex implicit invocation"
                )

        behavior_file = os.path.join(
            REPO_ROOT, "tests", "behavior", f"{skill['name']}.json"
        )
        if not path_exists(behavior_file):
            errors.append(f"{skill['name']}: missing behavioral cases")
        else:
            behavior = read_json(behavior_file)
            for kind in ["direct", "indirect", "incomplete", "negative", "failure"]:
                if not isinstance(behavior.get(kind), list) or not behavior[kind]:
                    errors.append(f"{skill['name']}: missing {kind} behavioral cases")

    skills_root = os.path.join(REPO_ROOT, "skills")
    with os.scandir(skills_root) as skill_entries:
        for entry in skill_entries:
            if entry.is_dir(follow_symlinks=False) and entry.name not in catalog_names:
                errors.append(f"uncataloged skill directory: {entry.name}")

    for skill in external["skills"]:
        if not skill.get("name") or not skill.get("sourceUrl") or not skill.get("license"):
            errors.append("external catalog entry missing name, sourceUrl, or license")
        if skill.get("distribution") != "link-only":
            errors.append(f"{skill.get('name')}: external entries must be link-only")

    core_profile = read_json(os.path.join(REPO_ROOT, "profiles", "core.json"))
    core_names = sorted(
        skill["name"] for skill in catalog["skills"] if skill.get("status") == "core"
    )
    if sorted(core_profile["skills"]) != core_names:
        errors.append("profiles/core.json does not match core catalog entries")

    return errors


def load_catalog() -> Any:
    return read_json(os.path.join(REPO_ROOT, "catalog", "skills.json"))


def load_external_catalog() -> Any:
    return read_json(os.path.join(REPO_ROOT, "catalog", "external.json"))


def _selected_skills(profile_or_name: str) -> list[dict[str, Any]]:
    catalog = load_catalog()
    profile_path = os.path.join(REPO_ROOT, "profiles", f"{profile_or_name}.json")
    if path_exists(profile_path):
        names = read_json(profile_path)["skills"]
    else:
        names = [profile_or_name]

    selected = []
    for name in names:
        skill = next((candidate for candidate in catalog["skills"] if candidate["name"] == name), None)
        if not skill:
            raise RuntimeError(f"unknown skill or profile: {name}")
        if skill.get("status") != "core" or not skill.get("path"):
            raise RuntimeError(
                f"{name} is not installable while status is {skill.get('status')}"
            )
        selected.append(skill)
    return selected


def _target_directories(home: str, target: str, name: str) -> list[dict[str, str]]:
    destinations: list[dict[str, str]] = []
    if target in {"codex", "both"}:
        destinations.append(
            {
                "runtime": "codex",
                "path": os.path.join(home, ".agents", "skills", name),
            }
        )
    if target in {"claude", "both"}:
        destinations.append(
            {
                "runtime": "claude-code",
                "path": os.path.join(home, ".claude", "skills", name),
            }
        )
    if not destinations:
        raise RuntimeError("target must be codex, claude, or both")
    return destinations


def _state_path(home: str, override: str | None, use_environment_config: bool = True) -> str:
    if override:
        return os.path.abspath(override)
    config_root = (
        os.path.abspath(os.environ["XDG_CONFIG_HOME"])
        if use_environment_config and os.environ.get("XDG_CONFIG_HOME")
        else os.path.join(home, ".config")
    )
    return os.path.join(config_root, "comcreate-skills", "install-state.json")


def _load_state(path: str) -> dict[str, Any]:
    if not path_exists(path):
        return {"schemaVersion": 1, "installations": []}
    state = read_json(path)
    if state.get("schemaVersion") != 1 or not isinstance(state.get("installations"), list):
        raise RuntimeError(f"unsupported installer state at {path}")
    return state


def _add_claude_manual_only(text: str) -> str:
    parsed = parse_frontmatter(text)
    if parsed["fields"].get("disable-model-invocation") == "true":
        return text
    lines = re.split(r"\r?\n", parsed["raw"])
    lines.insert(len(lines) - 2, "disable-model-invocation: true")
    return f"{chr(10).join(lines)}{parsed['body']}"


def _remove_path(path: str) -> None:
    if not path_exists(path):
        return
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)


def _render_copy(
    source: str, destination: str, skill: dict[str, Any], runtime: str
) -> dict[str, str]:
    parent = os.path.dirname(destination)
    os.makedirs(parent, exist_ok=True)
    staging_root = tempfile.mkdtemp(prefix=".comcreate-skills-", dir=parent)
    staged = os.path.join(staging_root, os.path.basename(destination))
    shutil.copytree(source, staged, symlinks=False)

    if runtime == "claude-code" and skill.get("manualOnly"):
        skill_file = os.path.join(staged, "SKILL.md")
        with open(skill_file, encoding="utf-8") as handle:
            original = handle.read()
        with open(skill_file, "w", encoding="utf-8") as handle:
            handle.write(_add_claude_manual_only(original))

    return {"stagingRoot": staging_root, "staged": staged}


def _current_installation_hash(installation: dict[str, Any]) -> str | None:
    if not path_exists(installation["targetPath"]):
        return None
    if installation.get("mode") == "link":
        if not os.path.islink(installation["targetPath"]):
            return "not-a-link"
        target = os.path.normpath(
            os.path.join(
                os.path.dirname(installation["targetPath"]),
                os.readlink(installation["targetPath"]),
            )
        )
        return f"link:{target}"
    return hash_directory(installation["targetPath"])


def install(options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    options = options or {}
    home = os.path.abspath(options.get("home") or os.path.expanduser("~"))
    profile = options.get("profile") or "core"
    target = options.get("target") or "both"
    mode = options.get("mode") or "copy"
    if mode not in {"copy", "link"}:
        raise RuntimeError("mode must be copy or link")

    path = _state_path(home, options.get("state"), options.get("home") is None)
    state = _load_state(path)
    installed: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []

    for skill in _selected_skills(profile):
        source = os.path.join(REPO_ROOT, skill["path"])
        source_hash = hash_directory(source)

        for destination in _target_directories(home, target, skill["name"]):
            if (
                mode == "link"
                and destination["runtime"] == "claude-code"
                and skill.get("manualOnly")
            ):
                raise RuntimeError(
                    f"{skill['name']}: development links are unsafe for manual-only Claude skills; use copy mode"
                )

            existing_state = next(
                (
                    entry
                    for entry in state["installations"]
                    if entry["targetPath"] == destination["path"]
                ),
                None,
            )
            if path_exists(destination["path"]):
                if not existing_state:
                    raise RuntimeError(
                        f"{skill['name']}: refusing to overwrite unmanaged destination {destination['path']}"
                    )
                current_hash = _current_installation_hash(existing_state)
                if current_hash != existing_state["installedHash"]:
                    raise RuntimeError(
                        f"{skill['name']}: managed destination was modified; resolve it before updating"
                    )

            operations.append(
                {
                    "skill": skill,
                    "source": source,
                    "sourceHash": source_hash,
                    "destination": destination,
                }
            )

    for operation in operations:
        skill = operation["skill"]
        source = operation["source"]
        source_hash = operation["sourceHash"]
        destination = operation["destination"]
        if mode == "link":
            _remove_path(destination["path"])
            os.makedirs(os.path.dirname(destination["path"]), exist_ok=True)
            os.symlink(source, destination["path"], target_is_directory=True)
            installed_hash = f"link:{source}"
        else:
            rendered = _render_copy(
                source, destination["path"], skill, destination["runtime"]
            )
            _remove_path(destination["path"])
            os.rename(rendered["staged"], destination["path"])
            shutil.rmtree(rendered["stagingRoot"], ignore_errors=True)
            installed_hash = hash_directory(destination["path"])

        record = {
            "skill": skill["name"],
            "version": skill["version"],
            "runtime": destination["runtime"],
            "mode": mode,
            "targetPath": destination["path"],
            "sourceHash": source_hash,
            "installedHash": installed_hash,
            "installedAt": _now_iso(),
        }
        index = next(
            (
                i
                for i, entry in enumerate(state["installations"])
                if entry["targetPath"] == destination["path"]
            ),
            -1,
        )
        if index >= 0:
            state["installations"][index] = record
        else:
            state["installations"].append(record)
        installed.append(record)
        write_json(path, state)

    return installed


def status(options: dict[str, Any] | None = None) -> list[dict[str, str]]:
    options = options or {}
    home = os.path.abspath(options.get("home") or os.path.expanduser("~"))
    path = _state_path(home, options.get("state"), options.get("home") is None)
    state = _load_state(path)
    catalog = load_catalog()
    output: list[dict[str, str]] = []

    for installation in state["installations"]:
        skill = next(
            (
                candidate
                for candidate in catalog["skills"]
                if candidate["name"] == installation["skill"]
            ),
            None,
        )
        source_hash = None
        if skill and skill.get("path") and path_exists(os.path.join(REPO_ROOT, skill["path"])):
            source_hash = hash_directory(os.path.join(REPO_ROOT, skill["path"]))
        current_hash = _current_installation_hash(installation)
        state_label = "current"
        if current_hash is None:
            state_label = "missing"
        elif current_hash != installation["installedHash"]:
            state_label = "modified"
        elif source_hash != installation["sourceHash"]:
            state_label = "outdated"

        output.append(
            {
                "skill": installation["skill"],
                "runtime": installation["runtime"],
                "mode": installation["mode"],
                "state": state_label,
            }
        )
    return output


def uninstall(options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    options = options or {}
    home = os.path.abspath(options.get("home") or os.path.expanduser("~"))
    path = _state_path(home, options.get("state"), options.get("home") is None)
    state = _load_state(path)
    removed: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    removal_queue: list[dict[str, Any]] = []
    selected = None
    if options.get("profile"):
        selected = {skill["name"] for skill in _selected_skills(options["profile"])}

    for installation in state["installations"]:
        if selected is not None and installation["skill"] not in selected:
            retained.append(installation)
            continue

        current_hash = _current_installation_hash(installation)
        if current_hash is None:
            removal_queue.append({"installation": installation, "alreadyMissing": True})
            continue
        if current_hash != installation["installedHash"]:
            raise RuntimeError(
                f"{installation['skill']}: refusing to remove a modified managed destination"
            )
        removal_queue.append({"installation": installation, "alreadyMissing": False})

    for queued in removal_queue:
        if not queued["alreadyMissing"]:
            _remove_path(queued["installation"]["targetPath"])
        if queued["alreadyMissing"]:
            removed.append({**queued["installation"], "alreadyMissing": True})
        else:
            removed.append(queued["installation"])

    state["installations"] = retained
    write_json(path, state)
    return removed


def make_temporary_home(prefix: str = "comcreate-skills-") -> str:
    return tempfile.mkdtemp(prefix=prefix)


def ensure_executable(path: str) -> None:
    os.chmod(path, 0o755)
