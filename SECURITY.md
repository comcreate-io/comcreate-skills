# Security Policy

Report suspected secrets, unsafe automation, or prompt-injection paths privately to the repository maintainers. Do not open a public issue containing sensitive material.

Skills are instructions, not security boundaries. External permissions, sandboxing, repository protections, and human approval remain authoritative.

Side-effectful skills must:

- require explicit invocation;
- default external writes off in example configuration;
- bound each run;
- verify exact write targets;
- stop when authentication, scope, or state is ambiguous;
- never widen authority because a scheduler invoked them.

The repository must not contain credentials, private session data, personal memory stores, raw transcript exports, client identifiers, or production configuration.
