---
name: opensource-documentation
description: Create, overhaul, audit, and verify open-source project documentation for any language or project type. Use when Codex needs to write or restructure a README, document source code or public APIs, build tutorials/guides/reference material, add contributor/security/release documentation, improve audience journeys, validate examples and claims, inspect generated API docs or packaged artifacts, or assess documentation readiness for an open-source release.
---

# Open-Source Documentation

Create documentation as a tested product surface. Optimize for the reader's
shortest successful journey, accurate public contracts, and evidence-backed
trust—not document length or template completeness.

## Core rules

- Preserve unrelated work and inspect repository instructions before editing.
- Derive facts from code, manifests, CI, release configuration, generated
  output, and distribution artifacts. Do not use prose to verify copied prose.
- Classify material claims as **proved**, **declared**, **planned**, or
  **unknown**. Never silently promote a weaker state to proved.
- Select headings from the reader's needs. Do not add empty sections to satisfy
  a universal README template.
- Treat source-level docs, examples, community health, security routes, legal
  material, packaging, and lifecycle docs as part of the documentation surface.
- Prefer an available language-specific documentation skill for source-level
  conventions while this skill owns repository-wide journeys and trust checks.
- Use current primary sources for version-sensitive standards and ecosystem
  conventions.
- Never count lint suppression, generator exclusion, or hidden public items as
  documentation coverage.
- Never claim that documentation, tests, or static analysis prove production
  readiness or security.

## Workflow

### 1. Protect and inventory

1. Inspect worktree state and preserve user changes.
2. Record the target revision, package boundaries, project types, primary and
   generated languages, public interfaces, supported versions, and shipped
   artifacts.
3. Read existing docs, source exports, manifests, examples, tests, CI, release
   automation, package inclusion rules, and support/security files before
   choosing a structure.
4. Identify primary audiences and their entry question, first task, success
   signal, next task, and recovery route.
5. Run the bundled inventory script for deterministic observations:

```bash
python3 <skill-root>/scripts/audit_documentation.py <repository>
```

Use `--format json` for machine-readable evidence. Use `--strict` only when
structural findings such as broken local links should return a nonzero status.
The script inventories evidence; it does not prove semantic quality.

### 2. Load only relevant reference sections

The exhaustive reference is over 10,000 words. Preview its map before reading:

```bash
rg -n '^## |^### ' <skill-root>/references/checklist.md
```

Read these sections for a comprehensive documentation task:

- Sections 1–3 for repository inventory, audiences, README flow, and document
  set.
- Section 4 for source code, public API contracts, inline comments, and doc
  tests.
- Section 5 for tutorial, how-to, reference, explanation, and troubleshooting
  intent.
- The matching section 6 project-type profile.
- Only the detected section 7 language profiles; use 7.0 for unlisted
  languages.
- Sections 8–9 for open-source trust, lifecycle, writing, accessibility, and
  visuals.
- Sections 10–12 for validation, observed failure modes, and scoring.
- Section 13 when researching authoritative standards or native tools.

Useful selectors:

```bash
rg -n '^### 2\.' <skill-root>/references/checklist.md
rg -n '^### 4\.' <skill-root>/references/checklist.md
rg -n '^### 6\.' <skill-root>/references/checklist.md
rg -n '^### 7\.' <skill-root>/references/checklist.md
rg -n '^### 10\.' <skill-root>/references/checklist.md
```

For a narrow request, read the matching section plus validation section 10.

### 3. Design the reader journeys

1. Choose one primary README flow and secondary routes by audience.
2. Keep the README a front door: identity, proof, status, first success, basic
   use, next routes, support, contribution, security, and license as applicable.
3. Move depth into documents selected by intent:
   - tutorial for learning;
   - how-to for a concrete goal;
   - reference for complete contracts;
   - explanation for mental models and tradeoffs;
   - troubleshooting for symptoms, diagnosis, recovery, and escalation.
4. Build a documentation map covering only applicable user, integrator,
   operator, contributor, maintainer, security, legal, and release surfaces.
5. Put a concrete mental model and smallest useful example before advanced
   architecture when newcomers are an audience.

### 4. Document the implementation contract

1. Derive the supported public inventory from compiler/package-visible exports.
2. Document package/module purpose and every supported public declaration using
   the language's native convention.
3. Cover applicable inputs, units, outputs, failure modes, side effects,
   invariants, lifecycle, ownership, concurrency, async/cancellation,
   performance, security, availability, deprecation, and examples.
4. Explain why and invariants in inline comments; do not paraphrase syntax.
5. Generate and inspect the API documentation. Check navigation, overview
   pages, re-exports, overloads, feature/platform gates, links, search, and
   intentionally hidden items.
6. Compile, type-check, or execute doc examples with native tooling whenever
   possible. Label anything not executed.

### 5. Verify the complete user surface

Create a claim ledger for every material install, compatibility, API, output,
performance, security, lifecycle, inventory, and licensing statement.

Before an unqualified completion claim, verify all applicable gates:

- [ ] Installation and first success work from a clean supported environment.
- [ ] Commands, examples, output, and failure behavior match the implementation.
- [ ] Local links, anchors, external references, and navigation resolve.
- [ ] Generated API docs cover the supported public inventory and are useful.
- [ ] The actual source archive, package, container, installer, or binary
  contains every file and path the docs promise.
- [ ] Upgrade, rollback, cleanup, backup, and destructive instructions are
  scoped and recoverable where applicable.
- [ ] Security reporting, supported versions, permissions, secrets, privacy,
  and trust boundaries are accurate.
- [ ] License and attribution cover code plus vendored code, examples, media,
  data, models, and generated assets.
- [ ] Accessibility and rendering are checked in the actual publication format.
- [ ] Counts, coverage, benchmarks, screenshots, and compatibility statements
  are revision/version/date-bound and independently reproducible.
- [ ] A skeptical final read finds no counterexample to the completion wording.

Use the narrowest repository-native validation commands. For tests managed by a
test ledger or project policy, follow that policy rather than bypassing it.

### 6. Keep the documentation audit in scope

This is a documentation skill, not a general implementation, API-design,
security, or maintainability review.

- Inspect implementation only as needed to verify documented claims, public
  contracts, examples, exported surfaces, and shipped artifacts.
- Rank and score only documentation findings in a documentation audit.
- Report an implementation issue only when direct evidence shows that it blocks
  truthful documentation. Put it in a separate, unranked **Implementation
  blockers exposed by documentation validation** appendix.
- State such a blocker minimally as the evidence/contract contradiction. Do not
  recommend implementation changes unless the user also requested an
  implementation or design review.
- Exclude unrelated code quality, API design, architecture, maintainability,
  performance, and security findings from the documentation report.
- Never hide a code/docs/default mismatch by documenting false behavior. Mark
  the affected documentation claim as blocked or unknown.
- Prefer executable examples, schemas, doc tests, generated inventories, and CI
  checks that keep future code and docs aligned.
- Do not infer correctness, maintainability, security, governance health, or
  adoption solely from documentation completeness.

## Completion report

Report:

- audiences and profiles applied;
- files and public surfaces changed;
- exact commands run and artifact forms inspected;
- proved, declared, planned, unknown, and environment-blocked claims;
- skipped checks with reasons;
- residual documentation debt and risk.

When necessary, add the separate unranked **Implementation blockers exposed by
documentation validation** appendix defined above. Omit it when no blocker
directly prevents truthful documentation.

Avoid “fully documented,” “all examples work,” “secure,” or “production ready”
unless the exact stated scope is supported by the evidence.

## Reference

Read [the exhaustive checklist](references/checklist.md) according to the
routing rules above. It contains audience-specific README heading flows,
repository and source-code checks, project/language profiles, open-source trust
requirements, validation gates, observed session failure modes, a quality
rubric, and authoritative sources.
