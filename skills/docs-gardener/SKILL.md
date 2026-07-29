---
name: docs-gardener
description: Audit repository guidance and operational documentation for mechanically provable drift, then produce human-gated proposals. Use for scheduled documentation maintenance, stale command checks, moved-path detection, or bounded AGENTS.md and CLAUDE.md audits.
---

# Docs Gardener

Find documentation drift with replayable checks. This skill proposes changes but never edits guidance during the audit.

## Require configuration

Obtain named search roots, file patterns, maximum depth, exclusions, state directory, maximum files, maximum proposals, and proposal sink. Never scan an unbounded home directory or infer private project roots.

## Enforce the constitution

1. Run one bounded sweep and stop.
2. Produce proposals only; never edit audited guidance.
3. Treat no drift as success.
4. Require a named command and failing output for every finding.
5. Prefer deletion and correction over new guidance.
6. Never propose wording churn or style cleanup.
7. Re-run the evidence command immediately before recording a proposal.
8. Exclude the gardener's state, proposal sink, generated outputs, dependencies, and configured archives.
9. Cap audited files and proposals.

## Audit

1. Discover only configured filenames beneath configured roots and depth limits.
2. Order never-audited files first, then oldest audits.
3. Skip unchanged files whose repository-state key and document modification time match state.
4. Audit only checkable claims: paths, commands, package scripts, versions, imports, configuration keys, and named generated artifacts.
5. Do not convert opinions, preferences, or architectural intent into drift findings.
6. For each failure, capture the target, claim, exact check, bounded output, proposed correction, and replayable verification.
7. Re-run the check; drop findings that no longer fail.
8. Append only the configured maximum of human-gated proposals.
9. Record audited and skipped files using opaque identifiers, then stop.

## Failure behavior

Abort the sweep when discovery escapes configured roots, a required tool is missing, state is unreadable, or evidence cannot be reproduced. Do not widen the scan to compensate.
