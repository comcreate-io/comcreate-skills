#!/usr/bin/env node

import {
  install,
  inventoryLocal,
  loadCatalog,
  loadExternalCatalog,
  status,
  uninstall,
  validateRepository,
  writeJson,
} from "../lib/core.mjs";

function help() {
  console.log(`comcreate-skills

Commands:
  inventory [--out FILE] [--home DIR] [--since-days N] [--no-usage]
            [--no-defaults] [--root RUNTIME=PATH]
  list [--json]
  validate [--json]
  install --target codex|claude|both [--profile core|SKILL] [--mode copy|link]
          [--home DIR] [--state FILE]
  status [--json] [--home DIR] [--state FILE]
  uninstall [--profile core|SKILL] [--home DIR] [--state FILE]
`);
}

function parse(argv) {
  const [command, ...rest] = argv;
  const options = { roots: [] };
  for (let index = 0; index < rest.length; index += 1) {
    const argument = rest[index];
    if (argument === "--json") options.json = true;
    else if (argument === "--no-usage") options.usage = false;
    else if (argument === "--no-defaults") options.defaults = false;
    else if (argument.startsWith("--")) {
      const key = argument.slice(2).replace(/-([a-z])/g, (_, letter) =>
        letter.toUpperCase(),
      );
      const value = rest[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`missing value for ${argument}`);
      }
      index += 1;
      if (key === "root") {
        const separator = value.indexOf("=");
        if (separator < 1) {
          throw new Error(`--root must use RUNTIME=PATH`);
        }
        const runtime = value.slice(0, separator);
        if (!["codex", "claude-code"].includes(runtime)) {
          throw new Error(`--root runtime must be codex or claude-code`);
        }
        options.roots.push({
          runtime,
          path: value.slice(separator + 1),
        });
      } else if (key === "sinceDays") {
        options.sinceDays = Number.parseInt(value, 10);
        if (!Number.isInteger(options.sinceDays) || options.sinceDays < 1) {
          throw new Error(`--since-days must be a positive integer`);
        }
      } else {
        options[key] = value;
      }
    } else {
      throw new Error(`unexpected argument: ${argument}`);
    }
  }
  return { command, options };
}

function printRows(rows, fields) {
  if (rows.length === 0) {
    console.log("No entries.");
    return;
  }
  const widths = fields.map(({ key, label }) =>
    Math.max(
      label.length,
      ...rows.map((row) => String(row[key] ?? "").length),
    ),
  );
  console.log(
    fields
      .map(({ label }, index) => label.padEnd(widths[index]))
      .join("  "),
  );
  for (const row of rows) {
    console.log(
      fields
        .map(({ key }, index) =>
          String(row[key] ?? "").padEnd(widths[index]),
        )
        .join("  "),
    );
  }
}

async function main() {
  const { command, options } = parse(process.argv.slice(2));
  if (!command || command === "help" || command === "--help") {
    help();
    return;
  }

  if (command === "inventory") {
    const report = await inventoryLocal(options);
    if (options.out) {
      await writeJson(options.out, report);
      console.log(
        `Wrote ${report.skills.length} sanitized skill records to ${options.out}`,
      );
    } else {
      console.log(JSON.stringify(report, null, 2));
    }
    return;
  }

  if (command === "list") {
    const catalog = await loadCatalog();
    const external = await loadExternalCatalog();
    const rows = [
      ...catalog.skills.map((skill) => ({
        name: skill.name,
        status: skill.status,
        category: skill.category,
      })),
      ...external.skills.map((skill) => ({
        name: skill.name,
        status: "external",
        category: skill.category,
      })),
    ];
    if (options.json) console.log(JSON.stringify(rows, null, 2));
    else {
      printRows(rows, [
        { key: "name", label: "NAME" },
        { key: "status", label: "STATUS" },
        { key: "category", label: "CATEGORY" },
      ]);
    }
    return;
  }

  if (command === "validate") {
    const errors = await validateRepository();
    if (options.json) {
      console.log(JSON.stringify({ valid: errors.length === 0, errors }, null, 2));
    } else if (errors.length === 0) {
      console.log("Repository is valid.");
    } else {
      console.error(errors.map((error) => `- ${error}`).join("\n"));
    }
    if (errors.length > 0) process.exitCode = 1;
    return;
  }

  if (command === "install") {
    const records = await install(options);
    printRows(records, [
      { key: "skill", label: "SKILL" },
      { key: "runtime", label: "RUNTIME" },
      { key: "mode", label: "MODE" },
    ]);
    return;
  }

  if (command === "status") {
    const rows = await status(options);
    if (options.json) console.log(JSON.stringify(rows, null, 2));
    else {
      printRows(rows, [
        { key: "skill", label: "SKILL" },
        { key: "runtime", label: "RUNTIME" },
        { key: "mode", label: "MODE" },
        { key: "state", label: "STATE" },
      ]);
    }
    if (rows.some((row) => row.state !== "current")) process.exitCode = 1;
    return;
  }

  if (command === "uninstall") {
    const rows = await uninstall(options);
    printRows(rows, [
      { key: "skill", label: "SKILL" },
      { key: "runtime", label: "RUNTIME" },
      { key: "mode", label: "MODE" },
    ]);
    return;
  }

  throw new Error(`unknown command: ${command}`);
}

main().catch((error) => {
  console.error(`comcreate-skills: ${error.message}`);
  process.exitCode = 1;
});
