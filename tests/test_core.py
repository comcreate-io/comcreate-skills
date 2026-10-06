from __future__ import annotations

import json
import os
import shutil
import sys
import unittest
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comcreate_skills.core import (  # noqa: E402
    install,
    inventory_local,
    make_temporary_home,
    path_exists,
    status,
    uninstall,
    validate_repository,
)


class CoreTests(unittest.TestCase):
    def test_repository_validation_passes(self) -> None:
        self.assertEqual(validate_repository(), [])

    def test_inventory_deduplicates_content_and_emits_no_source_paths(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        root = os.path.join(home, "portable-skills")
        skill = os.path.join(root, "fixture-skill")
        os.makedirs(skill, exist_ok=True)
        with open(os.path.join(skill, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write(
                "\n".join(
                    [
                        "---",
                        "name: fixture-skill",
                        "description: Exercise sanitized inventory behavior.",
                        "---",
                        "",
                        "# Fixture",
                        "",
                    ]
                )
            )

        report = inventory_local(
            {
                "home": home,
                "defaults": False,
                "usage": False,
                "roots": [
                    {"runtime": "codex", "path": root},
                    {"runtime": "claude-code", "path": root},
                ],
            }
        )

        self.assertEqual(len(report["skills"]), 1)
        self.assertEqual(report["skills"][0]["runtimes"], ["claude-code", "codex"])
        self.assertEqual(report["skills"][0]["projectCount"], 0)
        self.assertEqual(report["skills"][0]["variantCount"], 1)
        self.assertNotIn(home, json.dumps(report))

    def test_inventory_keeps_local_skills_and_usage_when_bytes_are_not_utf8(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        skill_dir = os.path.join(home, "portable-skills", "fixture-skill")
        os.makedirs(skill_dir, exist_ok=True)
        with open(os.path.join(skill_dir, "SKILL.md"), "wb") as handle:
            handle.write(
                b"---\n"
                b"name: fixture-skill\n"
                b"description: Exercise sanitized inventory behavior.\n"
                b"---\n"
                b"\n"
                b"# Fixture\n"
                b"\n"
                b"bad \xff byte\n"
            )

        log_dir = os.path.join(home, ".codex", "sessions")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "rollout.jsonl"), "wb") as handle:
            handle.write(
                b'{"type":"function_call","path":"/tmp/fixture-skill/SKILL.md"}\xff\n'
            )

        report = inventory_local(
            {
                "home": home,
                "defaults": False,
                "sinceDays": 30,
                "roots": [
                    {
                        "runtime": "codex",
                        "path": os.path.join(home, "portable-skills"),
                    }
                ],
            }
        )

        self.assertEqual(report["schemaVersion"], 1)
        self.assertEqual(len(report["skills"]), 1)
        skill = report["skills"][0]
        last_used = skill.pop("lastUsed")
        self.assertEqual(
            skill,
            {
                "name": "fixture-skill",
                "status": "incubator",
                "runtimes": ["codex"],
                "invocationCount": 1,
                "projectCount": 0,
                "variantCount": 1,
                "contentHashes": [
                    "sha256:33f295ed03b7ca9d06e8f0700be1cde573bbc58d42592c6542beae80735faa19"
                ],
            },
        )
        self.assertRegex(last_used, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        self.assertNotIn(home, json.dumps(report))

    def test_copy_install_adapts_manual_only_claude_skills_and_uninstalls_safely(
        self,
    ) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        records = install(
            {
                "home": home,
                "target": "both",
                "profile": "core",
                "mode": "copy",
            }
        )
        self.assertEqual(len(records), 14)

        with open(
            os.path.join(home, ".claude", "skills", "self-improvement-loop", "SKILL.md"),
            encoding="utf-8",
        ) as handle:
            claude_loop = handle.read()
        self.assertRegex(claude_loop, r"disable-model-invocation: true")

        with open(
            os.path.join(home, ".agents", "skills", "self-improvement-loop", "SKILL.md"),
            encoding="utf-8",
        ) as handle:
            codex_loop = handle.read()
        self.assertNotRegex(codex_loop, r"disable-model-invocation")

        self.assertEqual(
            [entry["state"] for entry in status({"home": home})],
            ["current"] * 14,
        )

        removed = uninstall({"home": home, "profile": "core"})
        self.assertEqual(len(removed), 14)
        self.assertFalse(
            path_exists(os.path.join(home, ".agents", "skills", "design-product-flows"))
        )

    def test_explicit_test_home_contains_its_own_installer_state(self) -> None:
        home = make_temporary_home()
        unrelated_config = make_temporary_home("unrelated-config-")
        previous_config = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = unrelated_config

        def restore() -> None:
            if previous_config is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = previous_config
            shutil.rmtree(home, ignore_errors=True)
            shutil.rmtree(unrelated_config, ignore_errors=True)

        self.addCleanup(restore)

        install(
            {
                "home": home,
                "target": "codex",
                "profile": "design-product-flows",
                "mode": "copy",
            }
        )
        self.assertTrue(
            path_exists(
                os.path.join(home, ".config", "comcreate-skills", "install-state.json")
            )
        )
        self.assertFalse(
            path_exists(
                os.path.join(unrelated_config, "comcreate-skills", "install-state.json")
            )
        )

    def test_status_detects_modifications_and_uninstall_refuses_data_loss(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        install(
            {
                "home": home,
                "target": "codex",
                "profile": "design-product-flows",
                "mode": "copy",
            }
        )
        skill_file = os.path.join(
            home, ".agents", "skills", "design-product-flows", "SKILL.md"
        )
        with open(skill_file, encoding="utf-8") as handle:
            original = handle.read()
        with open(skill_file, "w", encoding="utf-8") as handle:
            handle.write(f"{original}\nmodified\n")

        self.assertEqual(status({"home": home})[0]["state"], "modified")
        with self.assertRaisesRegex(
            RuntimeError, "refusing to remove a modified managed destination"
        ):
            uninstall({"home": home, "profile": "design-product-flows"})

    def test_installer_refuses_unmanaged_conflicts(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        conflict = os.path.join(home, ".agents", "skills", "design-product-flows")
        os.makedirs(conflict, exist_ok=True)
        with open(os.path.join(conflict, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("unmanaged")

        with self.assertRaisesRegex(
            RuntimeError, "refusing to overwrite unmanaged destination"
        ):
            install(
                {
                    "home": home,
                    "target": "codex",
                    "profile": "design-product-flows",
                    "mode": "copy",
                }
            )

    def test_installer_preflights_a_profile_before_writing_any_destination(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        conflict = os.path.join(home, ".agents", "skills", "self-improvement-loop")
        os.makedirs(conflict, exist_ok=True)
        with open(os.path.join(conflict, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("unmanaged")

        with self.assertRaisesRegex(
            RuntimeError, "refusing to overwrite unmanaged destination"
        ):
            install(
                {
                    "home": home,
                    "target": "codex",
                    "profile": "core",
                    "mode": "copy",
                }
            )
        self.assertFalse(
            path_exists(os.path.join(home, ".agents", "skills", "design-product-flows"))
        )

    def test_manual_only_claude_skills_reject_development_links(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        with self.assertRaisesRegex(RuntimeError, "development links are unsafe"):
            install(
                {
                    "home": home,
                    "target": "claude",
                    "profile": "self-improvement-loop",
                    "mode": "link",
                }
            )

    def test_portable_skills_support_verified_development_links(self) -> None:
        home = make_temporary_home()
        self.addCleanup(shutil.rmtree, home, True)

        install(
            {
                "home": home,
                "target": "both",
                "profile": "design-product-flows",
                "mode": "link",
            }
        )
        self.assertEqual(
            [entry["state"] for entry in status({"home": home})],
            ["current", "current"],
        )
        self.assertEqual(
            len(uninstall({"home": home, "profile": "design-product-flows"})),
            2,
        )


if __name__ == "__main__":
    unittest.main()
