# Configuration contract

```json
{
  "roots": ["repository-or-workspace-root"],
  "filePatterns": ["AGENTS.md", "CLAUDE.md"],
  "maxDepth": 4,
  "excludedSegments": ["archive", "node_modules", ".git"],
  "stateDirectory": "path",
  "proposalSink": "path",
  "maxFiles": 4,
  "maxProposals": 3
}
```

Resolve paths relative to each configured root. Store opaque document identifiers in shared reports when absolute paths would expose workstation or client information.
