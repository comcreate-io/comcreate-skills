# Configuration contract

```json
{
  "repositories": ["owner/repository"],
  "stateDirectory": "path",
  "maxPullRequests": 6,
  "excludedBranchPrefixes": ["automation/"],
  "excludedAuthors": ["dependency-bot"],
  "includeDrafts": false,
  "comment": {
    "enabled": false,
    "marker": "stable hidden marker"
  },
  "notification": {
    "enabled": false,
    "channel": "implementation-defined"
  }
}
```

Start with comments and notifications disabled. Enable them only after a dry run verifies discovery, filtering, marker lookup, and output quality.
