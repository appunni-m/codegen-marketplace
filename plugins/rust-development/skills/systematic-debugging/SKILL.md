---
name: systematic-debugging
description: Diagnose complex failures with reproducible evidence, competing hypotheses, bounded instrumentation, first-divergence tracing, and regression verification. Use when debugging, performing root-cause analysis, tracing expected-versus-actual behavior, or validating a port against a reference implementation.
license: MIT
compatibility: Any language, Any build system
metadata:
  version: "1.0.0"
---

# Systematic Debugging

Use evidence to narrow a failure before changing production code. Preserve
unrelated work and adapt the workflow to the repository's tools and policies.

## Core Principle

**Find the earliest observed divergence, then test why it occurs.** It is a
strong lead, not proof that every downstream symptom has the same cause.

```
Reproduce → Bound the failing stage → Form a hypothesis → Falsify it → Fix → Regress
```

Avoid masking a defect with output clamps or input-specific exceptions unless
the domain contract genuinely requires that behavior. Avoid broad refactors
while evidence is still being gathered because they add new variables.

## Workflow

1. **Reproduce precisely** — Record the smallest known failing input, exact
   command, environment, revision, and expected versus actual behavior.
2. **Protect the workspace** — Inspect existing changes and preserve them. Use
   a separate worktree or patch for risky experiments; do not create commits or
   discard files without authorization.
3. **Establish an oracle** — Use a specification, version-matched reference
   implementation, invariant, or regression test. State its limitations.
4. **Bound the failure** — Compare stable boundaries or pipeline stages. Use
   binary search when the stages are ordered and deterministic.
5. **Form competing hypotheses** — Write predictions that distinguish likely
   causes. A passing probe only means that probe did not reproduce the defect.
6. **Instrument narrowly** — Emit deterministic, bounded traces for the suspect
   state. Remove temporary instrumentation after retaining useful evidence.
7. **Fix the smallest causal unit** — Preserve intentional behavior and add a
   regression test that fails before the fix.
8. **Verify broadly** — Re-run the focused reproducer, nearby tests, and the
   repository's approved full validation workflow.
9. **Report evidence** — Separate confirmed cause, supporting observations,
   rejected hypotheses, residual uncertainty, and unrelated failures.

## Common Anti-Patterns

| Anti-pattern | Why it fails | What to do instead |
|---|---|---|
| Clamping output to match expected | Masks algorithm bugs | Find why the value differs |
| Changing several layers at once | Makes causality ambiguous | Change one bounded cause, then verify |
| Treating one passing probe as disproof | The probe may be incomplete | State what input and path were exercised |
| Assuming the reference is correct | Versions or fixtures may differ | Verify provenance and version alignment |
| Keeping unbounded trace output | Hides the first useful difference | Emit stable fields for one reproducer |
| Recording diagnosis only in source comments | Comments can become stale | Prefer regression tests and issue/commit evidence |

## Methodology Reference

Read only the references relevant to the task:

- `references/porting-protocol.md` — parity work for a version-matched C-to-Rust port
- `references/pipeline-tracing.md` — Pipeline-stage tracing: dump, compare, find first divergence
- `references/root-cause-analysis.md` — tracing backward from a confirmed divergence
- `references/hypothesis-driven.md` — Hypothesis-driven debugging: minimal test cases before full suites

## Review Output

Report the reproducer, first confirmed divergence, causal explanation, minimal
fix, regression coverage, validation results, and remaining uncertainty. Do not
claim a root cause when the evidence only narrows the search area.
