---
name: pr-review-sweep
description: Perform one bounded review sweep over configured pull requests and report only correctness, security, or meaningful edge-case findings. Use for scheduled or manual multi-repository PR review, dry runs, or reviewing one configured repository.
---

# PR Review Sweep

Review pull requests for high-signal defects. This skill is side-effectful and must be invoked explicitly.

## Require configuration

Obtain the repository scope, state directory, maximum pull requests, branch exclusions, bot exclusions, comment policy, and notification policy. Do not assume an organization, account, branch name, or messaging service.

## Enforce safety

- Run exactly one sweep, then stop.
- Treat no findings as success; never lower the bar to produce output.
- Never merge, close, approve, mark ready, or push commits.
- Skip previously reviewed head commits.
- Exclude configured automation branches and the sweep's own outputs.
- Cap work at the configured maximum.
- In dry-run mode, perform discovery and review but make no external writes or state advances.
- When comments are allowed, update only a comment carrying the configured marker and stable comment identifier. Never edit an arbitrary latest comment.

## Run the sweep

1. Verify repository access and load state.
2. Discover open pull requests within the configured scope.
3. Apply branch, bot, draft, age, and already-reviewed filters.
4. Select work deterministically by risk and age.
5. Inspect the diff, surrounding code, tests, and repository guidance.
6. Report only actionable correctness, security, data-loss, or material edge-case findings with tight file and line evidence.
7. Return `NO_FINDINGS` when the evidence does not clear that bar.
8. In dry-run mode, report intended comments and state changes without applying them.
9. Otherwise, post or update at most one consolidated marked comment per pull request when explicitly authorized.
10. Save the reviewed head commit and bounded run summary, then stop.

## Failure behavior

Abort without advancing state when authentication, repository discovery, diff retrieval, or comment-target verification fails. Report the failed stage and the minimum recovery action.
