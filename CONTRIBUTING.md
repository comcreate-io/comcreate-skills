# Contributing

Use a pull request for every core-skill change. Branches use conventional prefixes such as `feat/`, `fix/`, `docs/`, or `test/`.

## Add or change a skill

1. Keep one focused workflow per skill.
2. Put required `name` and trigger-rich `description` fields in `SKILL.md`.
3. Keep `SKILL.md` concise and link optional detail from `references/`.
4. Add or update `agents/openai.yaml`.
5. Register status, provenance, version, maintainers, runtimes, dependencies, and invocation policy in `catalog/skills.json`.
6. Add direct, indirect, incomplete-input, negative-trigger, and failure-mode cases under `tests/behavior/`.
7. Run `python3 -m unittest discover -s tests -v` and `python3 ./bin/comcreate-skills validate`.

Every contribution must state:

- trigger boundary;
- expected inputs and output;
- failure and stop behavior;
- runtime and tool dependencies;
- provenance and license;
- verification evidence.

Do not include client data, private repositories, credentials, employee-specific paths, personal memories, notification destinations, or machine-specific state. Put genuinely private extensions in a separate private overlay repository.

## Review standard

One maintainer review is required. Reviewers verify portability, provenance, activation boundaries, failure behavior, deterministic checks, and the deletion test: if removing an instruction would not make the agent measurably worse, remove it.

Do not add AI authorship footers or assistant identities to commits or pull requests.
