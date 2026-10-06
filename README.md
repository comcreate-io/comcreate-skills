# ComCreate Skills

Portable, evidence-backed [Agent Skills](https://agentskills.io) for Claude Code and Codex.

This repository is private while the library is dogfooded, but its tracked content is public-ready: no client material, credentials, personal paths, private memories, or organization-specific runtime state belongs here.

## Core skills

| Skill | Purpose | Invocation |
|---|---|---|
| `design-product-flows` | Design and audit lifecycle flows using explicit evidence and testable hypotheses | Automatic or explicit |
| `self-improvement-loop` | Distill sanitized agent feedback into human-gated proposals | Explicit only |
| `pr-review-sweep` | Run one bounded, high-signal pull request review sweep | Explicit only |
| `ci-triage-sweep` | Diagnose CI failures and gate draft fixes behind a local oracle | Explicit only |
| `docs-gardener` | Find mechanically provable documentation drift | Explicit only |
| `klientboost-playbook` | Apply outcome-marketing ops, copy, and pitch-chart shape in the host project | Automatic or explicit |
| `comcreate-brand` | Produce ComCreate-branded PDFs and documents in the comcreate.io design system | Automatic or explicit |

## Use the library

Requires Python 3.11 or newer. The CLI has no runtime dependencies.

```bash
python3 ./bin/comcreate-skills validate
python3 ./bin/comcreate-skills list
python3 ./bin/comcreate-skills install --target both --profile core
python3 ./bin/comcreate-skills status
```

Installation copies managed skills by default:

- Codex: `~/.agents/skills/<name>`
- Claude Code: `~/.claude/skills/<name>`

Claude Code copies of manual-only skills receive `disable-model-invocation: true`. Codex uses each skill's `agents/openai.yaml` policy. Development links are available with `--mode link`; they are intentionally refused for manual-only Claude skills because a link cannot apply the invocation adapter safely.

The installer records only managed destinations in `${XDG_CONFIG_HOME:-~/.config}/comcreate-skills/install-state.json`. Uninstall refuses to remove a managed copy that has been modified since installation.

## Inventory local skills

`inventory` reads known user skill roots plus bounded project roots, deduplicates by canonical path and content hash, and emits metadata only:

```bash
python3 ./bin/comcreate-skills inventory --out inventory.local.json
```

The report contains skill names, runtime labels, observed invocation/reference counts, last-used dates, project counts, status, variant counts, and content hashes. It never emits prompts, transcript text, session content, or absolute source paths.

Use `--no-usage` to skip local usage aggregation, `--no-defaults` to test only explicit roots, or add a root with `--root codex=/path/to/skills`.

## Curation model

- `core`: cleared, portable, tested, and distributable.
- `incubator`: useful but unresolved or not yet portable.
- `external`: link-only third-party recommendations.
- `private`: excluded client, employee, credential, or infrastructure material.

Original skills live in `skills/`. Third-party skills are never vendored casually; `catalog/external.json` points to upstream projects and records their declared or unresolved license status.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Core changes require deterministic validation, behavioral cases, provenance, and one maintainer review.

## Public release

The repository remains private until every requirement in [PUBLIC_RELEASE_CHECKLIST.md](PUBLIC_RELEASE_CHECKLIST.md) is complete.
