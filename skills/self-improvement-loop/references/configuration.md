# Configuration contract

Provide these values before running the loop:

```json
{
  "evidenceSource": "path or tool that emits sanitized feedback only",
  "proposalLedger": "path to inert proposals",
  "decisionLedger": "path to accepted and rejected decisions",
  "runLedger": "path to run summaries",
  "windowDays": 2,
  "maxWindowDays": 7,
  "maxProposals": 3
}
```

The evidence source may emit quoted feedback, timestamps, project-neutral session identifiers, and source categories. It must omit credentials, environment values, tool outputs, assistant reasoning, third-party pasted instructions, client data, and unrelated prompt content.

Keep proposals inert. A scheduler may invoke one sweep, but it must not grant authority to apply proposals or rewrite the loop's own constitution.
