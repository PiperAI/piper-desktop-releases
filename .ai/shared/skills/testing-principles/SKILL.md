---
name: testing-principles
description: Which tests to write and how to keep the suite small and meaningful. Use whenever writing, changing or reviewing tests, together with the repository's own testing skill if it has one.
---

# Testing principles

Tests are code we maintain. Write few tests that check behavior, survive refactors and catch real bugs. The repository's own testing skill, if any, adds the stack-specific how.

## Choose the kind of test

| Kind | Use for | Notes |
| --- | --- | --- |
| Integration | Endpoints, use cases, repositories, workers | Default choice. Real database and framework; mock only external services |
| Contract | Third-party APIs and SDKs | Recorded real responses; re-record periodically to catch API drift |
| Focused unit | Dense pure logic: parsing, mapping, math, dates, scoring | Table-driven or property-based, not one function per case |
| Evals | LLM prompts, agents, tool selection | Golden dataset + deterministic checks + LLM-as-judge |
| End-to-end | A handful of critical user flows | Few and stable |

## Rules

- Test through public interfaces. Never mock the repository's own modules; mock only external boundaries.
- Name each test after the behavior it checks, not the method it calls.
- One test per behavior, not per function. Parametrize instead of duplicating.
- Every test must fail if the behavior it covers breaks. No tests that only prove code ran.
- Extend an existing test before adding a new file. Reuse fixtures and factories.
- Don't test framework glue (task wrappers, wiring factories, CLI entrypoints).
- Coverage percentage is not a goal.
- Delete tests that are redundant, coupled to implementation, or have never failed.

## Workflow

1. From the task, write failing tests that describe the behavior. They are the spec a reviewer reads first.
2. Implement until they pass.
