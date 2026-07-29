import {
  chmod,
  cp,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  readlink,
  realpath,
  rename,
  rm,
  stat,
  symlink,
  writeFile,
} from "node:fs/promises";
import { createHash } from "node:crypto";
import { homedir, tmpdir } from "node:os";
import { basename, dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const IGNORED_SEGMENTS = new Set([
  ".git",
  "node_modules",
  "archive",
  "dist",
  "build",
  ".cache",
]);

export async function pathExists(path) {
  try {
    await lstat(path);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

export async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

export async function writeJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export function parseFrontmatter(text) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) throw new Error("missing YAML frontmatter");

  const fields = {};
  for (const rawLine of match[1].split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const field = line.match(/^([a-zA-Z0-9_-]+):\s*(.*)$/);
    if (!field) throw new Error(`unsupported frontmatter line: ${rawLine}`);
    let value = field[2].trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    fields[field[1]] = value;
  }

  return { fields, body: text.slice(match[0].length), raw: match[0] };
}

async function listFiles(root, options = {}, depth = 0, prefix = "") {
  const { maxDepth = 20, includeHidden = true } = options;
  if (depth > maxDepth) return [];

  const entries = await readdir(root, { withFileTypes: true });
  const output = [];

  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (!includeHidden && entry.name.startsWith(".")) continue;
    if (entry.name === ".git") continue;
    const absolute = join(root, entry.name);
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;

    if (entry.isDirectory()) {
      output.push(
        ...(await listFiles(
          absolute,
          options,
          depth + 1,
          relativePath,
        )),
      );
    } else if (entry.isFile()) {
      output.push({ absolute, relative: relativePath });
    } else if (entry.isSymbolicLink()) {
      const target = await realpath(absolute).catch(() => null);
      if (!target) {
        output.push({ absolute, relative: relativePath, broken: true });
      } else {
        const targetStat = await stat(target);
        if (targetStat.isDirectory()) {
          output.push(
            ...(await listFiles(
              target,
              options,
              depth + 1,
              relativePath,
            )),
          );
        } else {
          output.push({ absolute: target, relative: relativePath });
        }
      }
    }
  }

  return output;
}

export async function hashDirectory(root) {
  const files = await listFiles(root);
  const hash = createHash("sha256");
  for (const file of files) {
    hash.update(file.relative);
    if (file.broken) {
      hash.update("BROKEN_LINK");
    } else {
      hash.update(await readFile(file.absolute));
    }
  }
  return `sha256:${hash.digest("hex")}`;
}

function opaque(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

async function skillDirectories(root) {
  if (!(await pathExists(root))) return [];
  const rootSkill = join(root, "SKILL.md");
  if (await pathExists(rootSkill)) return [root];

  const entries = await readdir(root, { withFileTypes: true });
  const output = [];
  for (const entry of entries) {
    if (!entry.isDirectory() && !entry.isSymbolicLink()) continue;
    const candidate = join(root, entry.name);
    if (await pathExists(join(candidate, "SKILL.md"))) output.push(candidate);
  }
  return output;
}

async function discoverProjectSkillRoots(base, maxDepth = 5) {
  const found = [];
  async function walk(current, depth) {
    if (depth > maxDepth || !(await pathExists(current))) return;
    const entries = await readdir(current, { withFileTypes: true }).catch(
      () => [],
    );

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      if (IGNORED_SEGMENTS.has(entry.name)) continue;
      const absolute = join(current, entry.name);
      if (entry.name === ".agents" || entry.name === ".claude") {
        const skills = join(absolute, "skills");
        if (await pathExists(skills)) {
          found.push({
            path: skills,
            runtime: entry.name === ".agents" ? "codex" : "claude-code",
            projectId: opaque(current),
          });
        }
        continue;
      }
      if (entry.name.startsWith(".") && depth > 0) continue;
      await walk(absolute, depth + 1);
    }
  }
  await walk(base, 0);
  return found;
}

function defaultInventoryRoots(home) {
  return [
    {
      label: "shared-user",
      path: join(home, ".agents", "skills"),
      runtimes: ["codex", "claude-code"],
      projectId: null,
    },
    {
      label: "codex-user",
      path: join(home, ".codex", "skills"),
      runtimes: ["codex"],
      projectId: null,
    },
    {
      label: "claude-import",
      path: join(home, ".codex", "claude-import", "skills"),
      runtimes: ["claude-code"],
      projectId: null,
    },
  ];
}

async function extractUsage(home, sinceDays) {
  const usage = new Map();
  const cutoff = Date.now() - sinceDays * 24 * 60 * 60 * 1000;

  function record(name, usedAt, projectId) {
    const normalized = name.includes(":") ? name.split(":").at(-1) : name;
    if (!SKILL_NAME.test(normalized)) return;
    const existing = usage.get(normalized) ?? {
      invocationCount: 0,
      lastUsed: null,
      projects: new Set(),
    };
    existing.invocationCount += 1;
    if (!existing.lastUsed || usedAt > existing.lastUsed) {
      existing.lastUsed = usedAt;
    }
    if (projectId) existing.projects.add(projectId);
    usage.set(normalized, existing);
  }

  async function scanLogs(root, runtime) {
    if (!(await pathExists(root))) return;
    const files = await listFiles(root, { maxDepth: 8 });
    for (const file of files) {
      if (!file.relative.endsWith(".jsonl") || file.broken) continue;
      const metadata = await stat(file.absolute);
      if (metadata.mtimeMs < cutoff || metadata.size > 25 * 1024 * 1024) {
        continue;
      }

      const contents = await readFile(file.absolute, "utf8");
      const lines = contents.split(/\r?\n/);
      let projectId = runtime === "claude-code" ? opaque(dirname(file.absolute)) : null;

      if (runtime === "codex") {
        for (const line of lines.slice(0, 5)) {
          const cwd = line.match(/"cwd"\s*:\s*"([^"]+)"/);
          if (cwd) {
            projectId = opaque(cwd[1]);
            break;
          }
        }
      }

      for (const line of lines) {
        if (runtime === "codex") {
          if (
            !line.includes("SKILL.md") ||
            (!line.includes("function_call") &&
              !line.includes("custom_tool_call"))
          ) {
            continue;
          }
          const matches = line.matchAll(
            /\/([a-z0-9]+(?:-[a-z0-9]+)*)\/SKILL\.md/g,
          );
          for (const match of matches) {
            record(match[1], metadata.mtime.toISOString(), projectId);
          }
        } else {
          if (!line.includes('"name":"Skill"') && !line.includes('"name": "Skill"')) {
            continue;
          }
          const matches = line.matchAll(
            /"skill"\s*:\s*"([a-z0-9:-]+)"/g,
          );
          for (const match of matches) {
            record(match[1], metadata.mtime.toISOString(), projectId);
          }
        }
      }
    }
  }

  await scanLogs(join(home, ".codex", "sessions"), "codex");
  await scanLogs(join(home, ".claude", "projects"), "claude-code");
  return usage;
}

export async function inventoryLocal(options = {}) {
  const home = resolve(options.home ?? homedir());
  const roots = options.defaults === false ? [] : defaultInventoryRoots(home);

  for (const explicit of options.roots ?? []) {
    roots.push({
      label: "explicit",
      path: resolve(explicit.path),
      runtimes: [explicit.runtime],
      projectId: explicit.projectId ?? null,
    });
  }

  if (options.defaults !== false) {
    for (const projectBase of [
      join(home, "projects"),
      join(home, "Desktop", "projects"),
    ]) {
      for (const projectRoot of await discoverProjectSkillRoots(projectBase)) {
        roots.push({
          label: "project",
          path: projectRoot.path,
          runtimes: [projectRoot.runtime],
          projectId: projectRoot.projectId,
        });
      }
    }
  }

  const catalog = await readJson(join(repoRoot, "catalog", "skills.json"));
  const external = await readJson(join(repoRoot, "catalog", "external.json"));
  const statusByName = new Map([
    ...catalog.skills.map((skill) => [skill.name, skill.status]),
    ...external.skills.map((skill) => [skill.name, "external"]),
  ]);

  const grouped = new Map();
  for (const root of roots) {
    for (const directory of await skillDirectories(root.path)) {
      const skillText = await readFile(join(directory, "SKILL.md"), "utf8").catch(
        () => null,
      );
      if (!skillText) continue;

      let fields;
      try {
        ({ fields } = parseFrontmatter(skillText));
      } catch {
        continue;
      }
      const name = fields.name || basename(directory);
      if (!SKILL_NAME.test(name)) continue;

      const canonical = await realpath(directory).catch(() => directory);
      const contentHash = await hashDirectory(canonical);
      const key = `${name}|${contentHash}`;
      const current = grouped.get(key) ?? {
        name,
        status: statusByName.get(name) ?? "incubator",
        runtimes: new Set(),
        projectIds: new Set(),
        canonicalIds: new Set(),
        contentHash,
      };
      root.runtimes.forEach((runtime) => current.runtimes.add(runtime));
      if (root.projectId) current.projectIds.add(root.projectId);
      current.canonicalIds.add(opaque(canonical));
      grouped.set(key, current);
    }
  }

  const usage =
    options.usage === false
      ? new Map()
      : await extractUsage(home, options.sinceDays ?? 90);

  const byName = new Map();
  for (const variant of grouped.values()) {
    const current = byName.get(variant.name) ?? {
      name: variant.name,
      status: variant.status,
      runtimes: new Set(),
      projectIds: new Set(),
      contentHashes: new Set(),
    };
    variant.runtimes.forEach((runtime) => current.runtimes.add(runtime));
    variant.projectIds.forEach((projectId) => current.projectIds.add(projectId));
    current.contentHashes.add(variant.contentHash);
    byName.set(variant.name, current);
  }

  const skills = [...byName.values()]
    .map((skill) => {
      const observed = usage.get(skill.name);
      const projectIds = new Set(skill.projectIds);
      observed?.projects.forEach((project) => projectIds.add(project));
      return {
        name: skill.name,
        status: skill.status,
        runtimes: [...skill.runtimes].sort(),
        invocationCount: observed?.invocationCount ?? 0,
        lastUsed: observed?.lastUsed ?? null,
        projectCount: projectIds.size,
        variantCount: skill.contentHashes.size,
        contentHashes: [...skill.contentHashes].sort(),
      };
    })
    .sort(
      (a, b) =>
        b.invocationCount - a.invocationCount ||
        a.name.localeCompare(b.name),
    );

  return {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    skills,
  };
}

function localMarkdownLinks(text) {
  const links = [];
  for (const match of text.matchAll(/\]\(([^)]+)\)/g)) {
    const target = match[1].split("#")[0];
    if (!target || /^[a-z]+:\/\//i.test(target) || target.startsWith("#")) {
      continue;
    }
    links.push(target);
  }
  return links;
}

export async function validateRepository() {
  const errors = [];
  const catalogPath = join(repoRoot, "catalog", "skills.json");
  const externalPath = join(repoRoot, "catalog", "external.json");
  const catalog = await readJson(catalogPath);
  const external = await readJson(externalPath);
  const catalogNames = new Set();

  for (const skill of catalog.skills) {
    if (catalogNames.has(skill.name)) {
      errors.push(`duplicate catalog skill: ${skill.name}`);
    }
    catalogNames.add(skill.name);

    for (const field of [
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
    ]) {
      if (skill[field] === undefined || skill[field] === null && field !== "path") {
        errors.push(`${skill.name}: missing catalog field ${field}`);
      }
    }

    if (skill.status !== "core") continue;
    if (!skill.path) {
      errors.push(`${skill.name}: core skill has no path`);
      continue;
    }

    const skillDirectory = join(repoRoot, skill.path);
    const skillFile = join(skillDirectory, "SKILL.md");
    if (!(await pathExists(skillFile))) {
      errors.push(`${skill.name}: missing ${skill.path}/SKILL.md`);
      continue;
    }

    const text = await readFile(skillFile, "utf8");
    let frontmatter;
    try {
      frontmatter = parseFrontmatter(text);
    } catch (error) {
      errors.push(`${skill.name}: ${error.message}`);
      continue;
    }

    const fieldNames = Object.keys(frontmatter.fields).sort();
    if (fieldNames.join(",") !== "description,name") {
      errors.push(
        `${skill.name}: SKILL.md frontmatter must contain only name and description`,
      );
    }
    if (frontmatter.fields.name !== skill.name) {
      errors.push(
        `${skill.name}: frontmatter name does not match catalog and directory`,
      );
    }
    if (!SKILL_NAME.test(frontmatter.fields.name ?? "")) {
      errors.push(`${skill.name}: invalid Agent Skills name`);
    }
    const description = frontmatter.fields.description ?? "";
    if (!description || description.length > 1024) {
      errors.push(`${skill.name}: description must be 1-1024 characters`);
    }
    if (text.includes("[TODO") || text.includes("TODO:")) {
      errors.push(`${skill.name}: unresolved TODO`);
    }
    if (text.split(/\r?\n/).length > 500) {
      errors.push(`${skill.name}: SKILL.md exceeds 500 lines`);
    }

    const forbidden = [
      { pattern: /\/home\/[a-z0-9._-]+/i, label: "absolute Linux home path" },
      { pattern: /\/Users\/[a-z0-9._-]+/i, label: "absolute macOS home path" },
      { pattern: /C:\\Users\\/i, label: "absolute Windows home path" },
      { pattern: /\b(?:cartermccann|comcreate-io|telegram)\b/i, label: "private runtime assumption" },
      { pattern: /~\/\.Codex\b/, label: "legacy machine-specific state path" },
      { pattern: /\b(?:sk-[a-z0-9_-]{16,}|gh[opusr]_[a-z0-9]{16,})\b/i, label: "secret-like token" },
    ];
    for (const check of forbidden) {
      if (check.pattern.test(text)) {
        errors.push(`${skill.name}: contains ${check.label}`);
      }
    }

    for (const link of localMarkdownLinks(text)) {
      if (!(await pathExists(resolve(skillDirectory, link)))) {
        errors.push(`${skill.name}: broken reference ${link}`);
      }
    }

    const openaiYaml = join(skillDirectory, "agents", "openai.yaml");
    if (!(await pathExists(openaiYaml))) {
      errors.push(`${skill.name}: missing agents/openai.yaml`);
    } else if (skill.manualOnly) {
      const metadata = await readFile(openaiYaml, "utf8");
      if (!/allow_implicit_invocation:\s*false/.test(metadata)) {
        errors.push(
          `${skill.name}: manual-only skill must disable Codex implicit invocation`,
        );
      }
    }

    const behaviorFile = join(
      repoRoot,
      "tests",
      "behavior",
      `${skill.name}.json`,
    );
    if (!(await pathExists(behaviorFile))) {
      errors.push(`${skill.name}: missing behavioral cases`);
    } else {
      const behavior = await readJson(behaviorFile);
      for (const kind of ["direct", "indirect", "incomplete", "negative", "failure"]) {
        if (!Array.isArray(behavior[kind]) || behavior[kind].length === 0) {
          errors.push(`${skill.name}: missing ${kind} behavioral cases`);
        }
      }
    }
  }

  const skillEntries = await readdir(join(repoRoot, "skills"), {
    withFileTypes: true,
  });
  for (const entry of skillEntries) {
    if (entry.isDirectory() && !catalogNames.has(entry.name)) {
      errors.push(`uncataloged skill directory: ${entry.name}`);
    }
  }

  for (const skill of external.skills) {
    if (!skill.name || !skill.sourceUrl || !skill.license) {
      errors.push(`external catalog entry missing name, sourceUrl, or license`);
    }
    if (skill.distribution !== "link-only") {
      errors.push(`${skill.name}: external entries must be link-only`);
    }
  }

  const coreProfile = await readJson(join(repoRoot, "profiles", "core.json"));
  const coreNames = catalog.skills
    .filter((skill) => skill.status === "core")
    .map((skill) => skill.name)
    .sort();
  if (
    JSON.stringify([...coreProfile.skills].sort()) !== JSON.stringify(coreNames)
  ) {
    errors.push("profiles/core.json does not match core catalog entries");
  }

  return errors;
}

export async function loadCatalog() {
  return readJson(join(repoRoot, "catalog", "skills.json"));
}

export async function loadExternalCatalog() {
  return readJson(join(repoRoot, "catalog", "external.json"));
}

async function selectedSkills(profileOrName) {
  const catalog = await loadCatalog();
  const profilePath = join(repoRoot, "profiles", `${profileOrName}.json`);
  let names;
  if (await pathExists(profilePath)) {
    names = (await readJson(profilePath)).skills;
  } else {
    names = [profileOrName];
  }

  return names.map((name) => {
    const skill = catalog.skills.find((candidate) => candidate.name === name);
    if (!skill) throw new Error(`unknown skill or profile: ${name}`);
    if (skill.status !== "core" || !skill.path) {
      throw new Error(`${name} is not installable while status is ${skill.status}`);
    }
    return skill;
  });
}

function targetDirectories(home, target, name) {
  const destinations = [];
  if (target === "codex" || target === "both") {
    destinations.push({
      runtime: "codex",
      path: join(home, ".agents", "skills", name),
    });
  }
  if (target === "claude" || target === "both") {
    destinations.push({
      runtime: "claude-code",
      path: join(home, ".claude", "skills", name),
    });
  }
  if (destinations.length === 0) {
    throw new Error(`target must be codex, claude, or both`);
  }
  return destinations;
}

function statePath(home, override, useEnvironmentConfig = true) {
  if (override) return resolve(override);
  const configRoot = useEnvironmentConfig && process.env.XDG_CONFIG_HOME
    ? resolve(process.env.XDG_CONFIG_HOME)
    : join(home, ".config");
  return join(configRoot, "comcreate-skills", "install-state.json");
}

async function loadState(path) {
  if (!(await pathExists(path))) {
    return { schemaVersion: 1, installations: [] };
  }
  const state = await readJson(path);
  if (state.schemaVersion !== 1 || !Array.isArray(state.installations)) {
    throw new Error(`unsupported installer state at ${path}`);
  }
  return state;
}

function addClaudeManualOnly(text) {
  const parsed = parseFrontmatter(text);
  if (parsed.fields["disable-model-invocation"] === "true") return text;
  const lines = parsed.raw.split(/\r?\n/);
  lines.splice(lines.length - 2, 0, "disable-model-invocation: true");
  return `${lines.join("\n")}${parsed.body}`;
}

async function renderCopy(source, destination, skill, runtime) {
  const parent = dirname(destination);
  await mkdir(parent, { recursive: true });
  const stagingRoot = await mkdtemp(join(parent, ".comcreate-skills-"));
  const staged = join(stagingRoot, basename(destination));
  await cp(source, staged, { recursive: true, dereference: true });

  if (runtime === "claude-code" && skill.manualOnly) {
    const skillFile = join(staged, "SKILL.md");
    const adapted = addClaudeManualOnly(await readFile(skillFile, "utf8"));
    await writeFile(skillFile, adapted, "utf8");
  }

  return { stagingRoot, staged };
}

async function currentInstallationHash(installation) {
  if (!(await pathExists(installation.targetPath))) return null;
  if (installation.mode === "link") {
    const metadata = await lstat(installation.targetPath);
    if (!metadata.isSymbolicLink()) return "not-a-link";
    const target = resolve(dirname(installation.targetPath), await readlink(installation.targetPath));
    return `link:${target}`;
  }
  return hashDirectory(installation.targetPath);
}

export async function install(options) {
  const home = resolve(options.home ?? homedir());
  const profile = options.profile ?? "core";
  const target = options.target ?? "both";
  const mode = options.mode ?? "copy";
  if (!["copy", "link"].includes(mode)) {
    throw new Error(`mode must be copy or link`);
  }

  const path = statePath(home, options.state, options.home === undefined);
  const state = await loadState(path);
  const installed = [];
  const operations = [];

  for (const skill of await selectedSkills(profile)) {
    const source = join(repoRoot, skill.path);
    const sourceHash = await hashDirectory(source);

    for (const destination of targetDirectories(home, target, skill.name)) {
      if (
        mode === "link" &&
        destination.runtime === "claude-code" &&
        skill.manualOnly
      ) {
        throw new Error(
          `${skill.name}: development links are unsafe for manual-only Claude skills; use copy mode`,
        );
      }

      const existingState = state.installations.find(
        (entry) => entry.targetPath === destination.path,
      );
      if (await pathExists(destination.path)) {
        if (!existingState) {
          throw new Error(
            `${skill.name}: refusing to overwrite unmanaged destination ${destination.path}`,
          );
        }
        const currentHash = await currentInstallationHash(existingState);
        if (currentHash !== existingState.installedHash) {
          throw new Error(
            `${skill.name}: managed destination was modified; resolve it before updating`,
          );
        }
      }

      operations.push({
        skill,
        source,
        sourceHash,
        destination,
      });
    }
  }

  for (const operation of operations) {
    const { skill, source, sourceHash, destination } = operation;
    let installedHash;
    if (mode === "link") {
      await rm(destination.path, { recursive: true, force: true });
      await mkdir(dirname(destination.path), { recursive: true });
      await symlink(source, destination.path, "dir");
      installedHash = `link:${source}`;
    } else {
      const rendered = await renderCopy(
        source,
        destination.path,
        skill,
        destination.runtime,
      );
      await rm(destination.path, { recursive: true, force: true });
      await rename(rendered.staged, destination.path);
      await rm(rendered.stagingRoot, { recursive: true, force: true });
      installedHash = await hashDirectory(destination.path);
    }

    const record = {
      skill: skill.name,
      version: skill.version,
      runtime: destination.runtime,
      mode,
      targetPath: destination.path,
      sourceHash,
      installedHash,
      installedAt: new Date().toISOString(),
    };
    const index = state.installations.findIndex(
      (entry) => entry.targetPath === destination.path,
    );
    if (index >= 0) state.installations[index] = record;
    else state.installations.push(record);
    installed.push(record);
    await writeJson(path, state);
  }

  return installed;
}

export async function status(options = {}) {
  const home = resolve(options.home ?? homedir());
  const path = statePath(home, options.state, options.home === undefined);
  const state = await loadState(path);
  const catalog = await loadCatalog();
  const output = [];

  for (const installation of state.installations) {
    const skill = catalog.skills.find(
      (candidate) => candidate.name === installation.skill,
    );
    const sourceHash =
      skill?.path && (await pathExists(join(repoRoot, skill.path)))
        ? await hashDirectory(join(repoRoot, skill.path))
        : null;
    const currentHash = await currentInstallationHash(installation);
    let stateLabel = "current";
    if (currentHash === null) stateLabel = "missing";
    else if (currentHash !== installation.installedHash) stateLabel = "modified";
    else if (sourceHash !== installation.sourceHash) stateLabel = "outdated";

    output.push({
      skill: installation.skill,
      runtime: installation.runtime,
      mode: installation.mode,
      state: stateLabel,
    });
  }
  return output;
}

export async function uninstall(options = {}) {
  const home = resolve(options.home ?? homedir());
  const path = statePath(home, options.state, options.home === undefined);
  const state = await loadState(path);
  const removed = [];
  const retained = [];
  const removalQueue = [];
  const selected = options.profile
    ? new Set((await selectedSkills(options.profile)).map((skill) => skill.name))
    : null;

  for (const installation of state.installations) {
    if (selected && !selected.has(installation.skill)) {
      retained.push(installation);
      continue;
    }

    const currentHash = await currentInstallationHash(installation);
    if (currentHash === null) {
      removalQueue.push({ installation, alreadyMissing: true });
      continue;
    }
    if (currentHash !== installation.installedHash) {
      throw new Error(
        `${installation.skill}: refusing to remove a modified managed destination`,
      );
    }
    removalQueue.push({ installation, alreadyMissing: false });
  }

  for (const queued of removalQueue) {
    if (!queued.alreadyMissing) {
      await rm(queued.installation.targetPath, {
        recursive: true,
        force: true,
      });
    }
    removed.push(
      queued.alreadyMissing
        ? { ...queued.installation, alreadyMissing: true }
        : queued.installation,
    );
  }

  state.installations = retained;
  await writeJson(path, state);
  return removed;
}

export async function makeTemporaryHome(prefix = "comcreate-skills-") {
  return mkdtemp(join(tmpdir(), prefix));
}

export async function ensureExecutable(path) {
  await chmod(path, 0o755);
}
