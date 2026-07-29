---
name: ci-triage-sweep
description: Perform one bounded triage sweep over configured CI failures, diagnose root causes, and optionally propose draft fixes behind reproduce-before and pass-after gates. Use for manual or scheduled CI maintenance and dry runs.
---

# CI Triage Sweep

Diagnose recent CI failures without turning an unattended loop into a merge bot. This skill is side-effectful and must be invoked explicitly.

## Require configuration

Obtain repository scope, state directory, lookback window, triage and fix caps, branch prefix, comment marker, writable actions, and notification policy. Never assume an organization, default branch, account, or CI provider.

## Enforce safety

- Run exactly one sweep, then stop.
- Treat no new failures as success.
- Never merge, mark ready, force-push, or push to an existing branch.
- Never operate on the sweep's own branches or outputs.
- Require a local reproduce-before and pass-after oracle before proposing a fix.
- Fall back to diagnosis-only when the oracle is missing, nondeterministic, or expensive.
- Cap triaged failures and draft fixes using configuration.
- Make no external writes and advance no state in dry-run mode.

## Run the sweep

1. Verify CI and repository access; load state without hiding corruption.
2. Discover recent failures using each repository's actual default branch and configured lookback.
3. Exclude stale, superseded, canceled, automation-generated, and already-triaged failures.
4. Group repeated failures by stable signature.
5. Inspect logs and relevant repository code to identify the root cause.
6. Record a concise diagnosis, evidence, and recovery action.
7. If comments are authorized, post or update one marker-gated diagnosis per failure.
8. Consider a fix only when it is mechanical, scoped, reproducible locally, and proven by the same oracle after the change.
9. If draft fixes are authorized, create a new nonexisting branch and a draft pull request; never continue or merge it.
10. Record state and a bounded run summary, then stop.

## Failure behavior

Abort without advancing high-water marks when authentication, discovery, log retrieval, local reproduction, target-branch verification, or marker lookup fails. Preserve diagnosis evidence but do not improvise a write path.
