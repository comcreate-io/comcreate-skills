# Configuration contract

```json
{
  "repositories": ["owner/repository"],
  "stateDirectory": "path",
  "lookbackHours": 24,
  "maxFailures": 3,
  "maxDraftFixes": 1,
  "fixBranchPrefix": "ci-fix/",
  "comment": {
    "enabled": false,
    "marker": "stable hidden marker"
  },
  "draftFixesEnabled": false,
  "notification": {
    "enabled": false,
    "channel": "implementation-defined"
  }
}
```

Begin with dry runs, comments disabled, and draft fixes disabled. Enable each write capability independently after its preconditions have been verified.
