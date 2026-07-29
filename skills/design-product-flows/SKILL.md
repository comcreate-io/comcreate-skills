---
name: design-product-flows
description: Design, audit, or improve evidence-backed product flows and behavioral UI patterns. Use for onboarding, activation, dashboards, retention mechanics, paywalls, upgrades, lifecycle journeys, or comparative interface-pattern research.
---

# Design Product Flows

Design the behavior and sequence before styling individual screens. Treat observed interface patterns as evidence for hypotheses, not proof that a pattern works.

## Establish the decision

1. Identify the user, lifecycle moment, current job, and desired outcome.
2. Define the next meaningful value event.
3. Name the decision the interface must help the user make.
4. Record business goals, user benefit, baseline behavior, and material constraints.
5. Ask for a missing fact only when it would change the recommendation; otherwise state the assumption.

## Analyze the whole flow

Map the entry trigger, ordered steps, branches, exits, success state, and return path. At each step, determine:

- what the user knows, wants, and may distrust;
- what effort, information, permission, or commitment is requested;
- what value the user receives in exchange;
- whether the next action is clear and honest;
- how skip, decline, failure, and retry behave.

Separate comprehension, motivation, capability, trust, and timing problems. Do not use visual polish to disguise a sequencing problem.

## Research patterns

When current examples would improve the work, compare several real flows and extract the mechanism beneath their styling. Classify evidence and transfer risk using [references/evidence.md](references/evidence.md).

Frequency shows that a pattern is common, not effective. Never invent research results, conversion data, user intent, or compliance requirements.

## Form testable hypotheses

For each recommendation, provide:

- observed problem and evidence;
- proposed trigger, sequence, content intent, and states;
- user mechanism and benefit;
- expected business outcome;
- primary behavioral metric;
- trust, accessibility, quality, and downstream guardrails;
- confidence and open assumptions.

Prefer a few meaningfully different variants over cosmetic permutations. Keep the existing experience as a control when experimentation is possible.

## Specify the handoff

Include eligibility, steps, branching, information shown and requested, loading and error states, back/skip/dismiss/retry behavior, analytics events, accessibility, reduced motion, privacy, and billing constraints.

Reject fake urgency, misleading scarcity, guilt, hidden renewal terms, obstructive cancellation, disguised permission requests, and engagement mechanics detached from user value.

## Verify

- Advance a user outcome, not only a company metric.
- Match the sequence to user readiness.
- Return visible value for requested inputs.
- Distinguish observation from causal evidence.
- Treat failure and recovery as first-class states.
- Make metrics capable of revealing benefit and harm.
- Keep the flow understandable without animation, color, or coercion.
