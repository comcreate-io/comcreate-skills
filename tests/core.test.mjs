import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";

import {
  install,
  inventoryLocal,
  makeTemporaryHome,
  pathExists,
  status,
  uninstall,
  validateRepository,
} from "../lib/core.mjs";

test("repository validation passes", async () => {
  assert.deepEqual(await validateRepository(), []);
});

test("inventory deduplicates content and emits no source paths", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  const root = join(home, "portable-skills");
  const skill = join(root, "fixture-skill");
  await mkdir(skill, { recursive: true });
  await writeFile(
    join(skill, "SKILL.md"),
    [
      "---",
      "name: fixture-skill",
      "description: Exercise sanitized inventory behavior.",
      "---",
      "",
      "# Fixture",
      "",
    ].join("\n"),
  );

  const report = await inventoryLocal({
    home,
    defaults: false,
    usage: false,
    roots: [
      { runtime: "codex", path: root },
      { runtime: "claude-code", path: root },
    ],
  });

  assert.equal(report.skills.length, 1);
  assert.deepEqual(report.skills[0].runtimes, ["claude-code", "codex"]);
  assert.equal(report.skills[0].projectCount, 0);
  assert.equal(report.skills[0].variantCount, 1);
  assert.equal(JSON.stringify(report).includes(home), false);
});

test("copy install adapts manual-only Claude skills and uninstalls safely", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  const records = await install({
    home,
    target: "both",
    profile: "core",
    mode: "copy",
  });
  assert.equal(records.length, 10);

  const claudeLoop = await readFile(
    join(home, ".claude", "skills", "self-improvement-loop", "SKILL.md"),
    "utf8",
  );
  assert.match(claudeLoop, /disable-model-invocation: true/);

  const codexLoop = await readFile(
    join(home, ".agents", "skills", "self-improvement-loop", "SKILL.md"),
    "utf8",
  );
  assert.doesNotMatch(codexLoop, /disable-model-invocation/);

  assert.deepEqual(
    (await status({ home })).map((entry) => entry.state),
    Array(10).fill("current"),
  );

  const removed = await uninstall({ home, profile: "core" });
  assert.equal(removed.length, 10);
  assert.equal(
    await pathExists(
      join(home, ".agents", "skills", "design-product-flows"),
    ),
    false,
  );
});

test("an explicit test home contains its own installer state", async (t) => {
  const home = await makeTemporaryHome();
  const unrelatedConfig = await makeTemporaryHome("unrelated-config-");
  const previousConfig = process.env.XDG_CONFIG_HOME;
  process.env.XDG_CONFIG_HOME = unrelatedConfig;
  t.after(async () => {
    if (previousConfig === undefined) delete process.env.XDG_CONFIG_HOME;
    else process.env.XDG_CONFIG_HOME = previousConfig;
    await rm(home, { recursive: true, force: true });
    await rm(unrelatedConfig, { recursive: true, force: true });
  });

  await install({
    home,
    target: "codex",
    profile: "design-product-flows",
    mode: "copy",
  });
  assert.equal(
    await pathExists(
      join(home, ".config", "comcreate-skills", "install-state.json"),
    ),
    true,
  );
  assert.equal(
    await pathExists(
      join(unrelatedConfig, "comcreate-skills", "install-state.json"),
    ),
    false,
  );
});

test("status detects modifications and uninstall refuses data loss", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  await install({
    home,
    target: "codex",
    profile: "design-product-flows",
    mode: "copy",
  });
  const skillFile = join(
    home,
    ".agents",
    "skills",
    "design-product-flows",
    "SKILL.md",
  );
  await writeFile(skillFile, `${await readFile(skillFile, "utf8")}\nmodified\n`);

  assert.equal((await status({ home }))[0].state, "modified");
  await assert.rejects(
    uninstall({ home, profile: "design-product-flows" }),
    /refusing to remove a modified managed destination/,
  );
});

test("installer refuses unmanaged conflicts", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  const conflict = join(
    home,
    ".agents",
    "skills",
    "design-product-flows",
  );
  await mkdir(conflict, { recursive: true });
  await writeFile(join(conflict, "SKILL.md"), "unmanaged");

  await assert.rejects(
    install({
      home,
      target: "codex",
      profile: "design-product-flows",
      mode: "copy",
    }),
    /refusing to overwrite unmanaged destination/,
  );
});

test("installer preflights a profile before writing any destination", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  const conflict = join(
    home,
    ".agents",
    "skills",
    "self-improvement-loop",
  );
  await mkdir(conflict, { recursive: true });
  await writeFile(join(conflict, "SKILL.md"), "unmanaged");

  await assert.rejects(
    install({
      home,
      target: "codex",
      profile: "core",
      mode: "copy",
    }),
    /refusing to overwrite unmanaged destination/,
  );
  assert.equal(
    await pathExists(
      join(home, ".agents", "skills", "design-product-flows"),
    ),
    false,
  );
});

test("manual-only Claude skills reject development links", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  await assert.rejects(
    install({
      home,
      target: "claude",
      profile: "self-improvement-loop",
      mode: "link",
    }),
    /development links are unsafe/,
  );
});

test("portable skills support verified development links", async (t) => {
  const home = await makeTemporaryHome();
  t.after(() => rm(home, { recursive: true, force: true }));

  await install({
    home,
    target: "both",
    profile: "design-product-flows",
    mode: "link",
  });
  assert.deepEqual(
    (await status({ home })).map((entry) => entry.state),
    ["current", "current"],
  );
  assert.equal((await uninstall({ home, profile: "design-product-flows" })).length, 2);
});
