# Open-Source Documentation — Exhaustive Checklist

Research baseline: 2026-07-30. Revalidate version-sensitive standards and
ecosystem behavior when applying this reference.

## Contents

1. [Repository and audience inventory](#1-repository-and-audience-inventory)
2. [README heading flows](#2-readme-heading-flows)
3. [Documentation-set coverage](#3-documentation-set-coverage)
4. [Source-code documentation](#4-source-code-documentation)
5. [Document intent and content checks](#5-document-intent-and-content-checks)
6. [Project-type specialties](#6-project-type-specialties)
7. [Language and ecosystem specialties](#7-language-and-ecosystem-specialties)
8. [Open-source trust, community, and lifecycle](#8-open-source-trust-community-and-lifecycle)
9. [Writing, accessibility, localization, and visuals](#9-writing-accessibility-localization-and-visual-content)
10. [Truth and validation gates](#10-truth-and-validation-gates)
11. [Observed failure modes](#11-failure-mode-checklist-from-observed-codex-sessions)
12. [Quality rubric](#12-quality-rubric)
13. [Authoritative reference index](#13-authoritative-reference-index)

## Purpose

The `opensource-documentation` skill lets an agent inspect an arbitrary
repository and produce or repair its documentation in one focused session. It
optimizes for a successful reader journey, truthful claims, complete
public-interface coverage, and verifiable examples. It does not
optimize for document length, badge count, visual polish, or passing a shallow
lint check.

The skill is primarily a checklist of what to inspect and prove. It is not a
generic writing tutorial and it must not force every project into one README
template.

No reviewed authority defines a universal “best README” or guarantees
documentation quality. The heading flows in this reference are a synthesis:
[GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
defines core front-door questions; the
[OpenSSF OSPS Baseline](https://baseline.openssf.org/versions/2026-02-19)
defines important open-source project controls; [Diátaxis](https://diataxis.fr/)
separates reader intents; W3C guidance supplies accessibility constraints; and
native language sources supply code-documentation conventions. The project,
audience, and verified user journey decide the final structure. Versioned
standards and tool behavior must be rechecked when the skill runs.

## Normative language and evidence

The reference uses these labels:

- **Required**: necessary for the skill to claim completion.
- **Conditional**: required when the repository exposes the named surface or
  has the named risk.
- **Recommended**: normally improves the reader journey, but may be omitted
  with a project-specific reason.
- **Not applicable**: the surface does not exist; record why rather than
  silently skipping it.

Every factual project claim should also have an evidence state:

- **Proved**: checked against source, configuration, a generated artifact, or a
  successful command at the documented revision.
- **Declared**: stated by the project but not independently executable in the
  current environment.
- **Planned**: a future intention, roadmap item, or unimplemented design.
- **Unknown**: no reliable evidence was found.

Never convert declared, planned, or unknown information into a proved claim by
rewriting it more confidently.

## Compact runtime checklist

This is the intended shape of the eventual compact skill. The detailed sections
below define each check.

- [ ] Identify repository type, languages, package boundaries, public
  interfaces, supported platforms, and intended audiences.
- [ ] Read the code, manifests, CI, release configuration, existing docs,
  examples, and packaged artifact before deciding the documentation structure.
- [ ] Build an audience-to-task map and choose the shortest successful path for
  each primary audience.
- [ ] Give the README an audience-appropriate heading order; do not include
  headings merely to satisfy a template.
- [ ] Cover installation, first success, normal use, failure recovery, support,
  contribution, security, licensing, and lifecycle where applicable.
- [ ] Document every supported public code surface using its language's native
  documentation convention.
- [ ] Separate tutorials, task recipes, reference, and explanation when their
  reader intents would otherwise conflict.
- [ ] Check every material claim against a non-circular source of truth.
- [ ] Build, run, or type-check examples using supported versions and fresh
  inputs; mark anything not executed.
- [ ] Generate and inspect API documentation, including navigation, public-item
  coverage, links, rendering, and hidden/suppressed items.
- [ ] Validate the installed or released artifact, not only the source tree.
- [ ] Check links, anchors, accessibility, secrets, destructive commands,
  security contacts, licensing, and community health files.
- [ ] Perform an adversarial final read as a new user, integrator, contributor,
  operator, and maintainer.
- [ ] Report proved checks, skipped checks with reasons, residual uncertainty,
  and exact validation commands; never claim more than the evidence shows.

## 1. Repository and audience inventory

### 1.1 Repository identity

- [ ] **Required** — Record the repository's actual name, purpose, maturity, and
  ownership from source-controlled evidence.
- [ ] **Required** — Identify whether it is a library, CLI, application,
  service, API, SDK, framework, plugin, protocol, specification, monorepo,
  template, research artifact, data project, or a combination.
- [ ] **Required** — Identify all package roots and which one, if any, is the
  canonical user entry point.
- [ ] **Required** — Identify primary languages and generated-language
  bindings.
- [ ] **Required** — Identify build systems, package managers, test runners,
  documentation generators, linters, release systems, and deployment systems.
- [ ] **Required** — Identify the target revision, branch, tag, or release.
- [ ] **Conditional** — Identify long-term-support branches, minimum supported
  runtime versions, feature flags, optional dependencies, and platform-specific
  builds.
- [ ] **Conditional** — Identify which files are shipped in source archives,
  registries, containers, installers, wheels, crates, gems, packages, or binary
  releases.

### 1.2 Audience map

For every included audience, record its entry question, first task, success
signal, next likely task, and recovery route.

- [ ] Evaluator: “What is this, why would I choose it, and can I trust it?”
- [ ] New user: “What is the shortest safe path to a first useful result?”
- [ ] Returning user: “Where is the exact option, API, or recipe I need?”
- [ ] Library integrator: “What contract can my code rely on?”
- [ ] CLI operator: “What commands, files, environment variables, outputs, and
  exit codes exist?”
- [ ] Service operator: “How do I deploy, secure, observe, upgrade, back up, and
  recover it?”
- [ ] Plugin or extension author: “What extension points and compatibility
  promises exist?”
- [ ] Contributor: “How do I reproduce the project and submit an acceptable
  change?”
- [ ] Maintainer: “How do I release, deprecate, migrate, triage, and respond to
  security reports?”
- [ ] Security reviewer: “What is the trust boundary, supported version policy,
  reporting route, and threat model?”
- [ ] Research reproducer: “Can I recreate the environment, inputs, evaluation,
  and reported result?”
- [ ] Downstream packager: “What are the build inputs, licenses, generated
  assets, platform requirements, and reproducibility constraints?”

### 1.3 Audience calibration

- [ ] **Required** — State assumed knowledge before using specialist
  terminology.
- [ ] **Required** — Define project-specific terms on first use.
- [ ] **Required** — Put a concrete mental model or smallest useful example
  before architecture and advanced taxonomy when newcomers are an audience.
- [ ] **Recommended** — Test a small introductory sample before expanding a
  long conceptual guide.
- [ ] **Recommended** — Provide “new here,” “using it now,” and “contributing”
  routes when one linear path would serve none of them well.
- [ ] **Required** — Do not make implementation detail a prerequisite for the
  first successful user task.

## 2. README heading flows

The README is the repository's front door, not the complete manual. Select a
flow based on the primary audience. Merge tiny adjacent sections and link to
deeper documents. A heading is justified only when it answers a real reader
question.

### 2.1 Universal front-door flow

Recommended order for most open-source repositories:

1. Project name
2. One-sentence purpose and intended user
3. Proof or demonstration
4. Status, compatibility, and important warnings
5. Quick start
6. Basic usage
7. Where to go next
8. Support and troubleshooting
9. Contributing
10. Security
11. License and attribution

Checks:

- [ ] The first screen explains what the project does and for whom.
- [ ] The value proposition is concrete rather than a slogan.
- [ ] A screenshot, terminal transcript, or minimal output is present only when
  it helps the reader evaluate or understand the project.
- [ ] Badges are limited to high-value signals and have accessible labels.
- [ ] Experimental, archived, unmaintained, or insecure status is visible
  before installation.
- [ ] The quick start reaches a useful result without detouring through design
  history.
- [ ] The README links to detailed reference rather than duplicating it.
- [ ] Critical instructions remain available in a packaged source artifact.

### 2.2 Evaluator-first README

Recommended heading order:

1. What it is
2. Why it exists
3. What it looks like
4. Key capabilities and explicit non-goals
5. Maturity and support status
6. Compatibility
7. Five-minute evaluation
8. Comparison or selection guidance
9. Security and trust
10. License
11. Documentation, support, and community

Checks:

- [ ] Comparisons use defined criteria and verifiable, revision-bound facts.
- [ ] Performance claims name workload, environment, date, revision, and
  method.
- [ ] “Production ready,” “secure,” “compatible,” and similar claims state
  scope or are removed.
- [ ] Limitations and non-goals are visible before adoption.

### 2.3 Library or framework README

Recommended heading order:

1. Purpose and smallest example
2. Stability and compatibility
3. Installation
4. Import and first use
5. Core concepts
6. Common recipes
7. Public API reference
8. Errors and failure behavior
9. Configuration and feature flags
10. Concurrency, performance, and resource behavior
11. Versioning, deprecation, and migration
12. Contributing, security, and license

Checks:

- [ ] Install command and package name match the registry artifact.
- [ ] Import paths match installed package layout.
- [ ] The smallest example compiles or executes with the documented version.
- [ ] Public API docs are reachable in one link from the README.
- [ ] Supported runtime, compiler, ABI, and feature combinations are explicit.
- [ ] Default features and optional features are distinguished.

### 2.4 CLI README

Recommended heading order:

1. Purpose and example transcript
2. Installation
3. Quick start
4. Command model
5. Common tasks
6. Global options and command reference
7. Configuration precedence
8. Environment variables
9. Files, state, cache, and logs
10. Input/output formats
11. Exit codes and automation behavior
12. Shell completion
13. Troubleshooting
14. Uninstall or cleanup
15. Contributing, security, and license

Checks:

- [ ] Every documented command exists in the current binary.
- [ ] Help output, defaults, aliases, and option spelling agree with docs.
- [ ] Examples distinguish shell prompt text from literal input.
- [ ] Quoting is correct for each claimed shell and operating system.
- [ ] Destructive commands describe scope, preview/dry-run behavior, recovery,
  and confirmation.
- [ ] Standard input, standard output, standard error, color, terminal, and
  non-interactive behavior are documented where relevant.
- [ ] Exit codes are checked rather than inferred.

### 2.5 Hosted service or self-hosted application README

Recommended heading order:

1. Purpose and deployment shape
2. Status and support
3. Quick local evaluation
4. Production prerequisites
5. Deployment options
6. Configuration and secrets
7. Initial setup and migrations
8. Operations
9. Observability
10. Backup and restore
11. Upgrade and rollback
12. Scaling and availability
13. Security model
14. Troubleshooting
15. Uninstall and data retention
16. Contributing, support, and license

Checks:

- [ ] Local demo instructions are not represented as production guidance.
- [ ] Persistent state and external dependencies are identified.
- [ ] Secret generation, storage, rotation, and redaction expectations are
  stated without publishing real credentials.
- [ ] Health, readiness, metrics, logs, and alert signals are explained.
- [ ] Migration, backup, restore, rollback, and disaster-recovery claims are
  tested or explicitly unverified.
- [ ] Reverse proxy, TLS, authentication, authorization, network exposure, and
  default credentials are covered where applicable.

### 2.6 HTTP API or SDK README

Recommended heading order:

1. API purpose and stability
2. Base URL or package setup
3. Authentication
4. First successful request
5. Resource or operation model
6. Request and response conventions
7. Errors
8. Pagination, filtering, and sorting
9. Rate limits and quotas
10. Idempotency, retries, and timeouts
11. Webhooks or events
12. Versioning and deprecation
13. SDKs and machine-readable specification
14. Security and support

Checks:

- [ ] Example requests use reserved example domains and non-secret tokens.
- [ ] Authentication examples cannot be mistaken for live credentials.
- [ ] Status codes, error schema, correlation IDs, and retryability are
  documented.
- [ ] Nullability, optionality, timestamps, units, encoding, and precision are
  explicit.
- [ ] Pagination ordering and consistency behavior are stated.
- [ ] Rate-limit scope and reset semantics are stated.
- [ ] Idempotency and retry examples cannot duplicate unsafe operations.
- [ ] OpenAPI, AsyncAPI, GraphQL schema, protobuf, or equivalent generated
  reference matches the deployed interface.

### 2.7 GUI, desktop, mobile, or end-user application README

Recommended heading order:

1. What the application does
2. Screenshots or short demonstration
3. Supported platforms and maturity
4. Installation
5. First-use walkthrough
6. Common workflows
7. Permissions, privacy, and data location
8. Import, export, backup, and sync
9. Accessibility and localization
10. Updates and migration
11. Troubleshooting and diagnostics
12. Uninstall and data removal
13. Support, contribution, security, and license

Checks:

- [ ] Screenshots match the current version and have useful alternative text.
- [ ] Platform permissions are explained at the point of need.
- [ ] Data collection, network access, telemetry, and local storage are
  accurately described.
- [ ] Keyboard, screen-reader, motion, contrast, and localization limitations
  are not hidden.

### 2.8 Plugin, extension, template, or integration README

Recommended heading order:

1. Host product and problem solved
2. Compatibility matrix
3. Installation
4. Enablement and permissions
5. First use
6. Configuration
7. Extension points
8. Examples
9. Upgrade and host-version migration
10. Security boundaries
11. Troubleshooting and removal
12. Development, publishing, and license

Checks:

- [ ] Host application versions and APIs are pinned or bounded.
- [ ] Required permissions and data access are explained before enablement.
- [ ] Generated project/template placeholders are all enumerated.
- [ ] Removal consequences and retained data are documented.

### 2.9 Research, data science, or machine-learning README

Recommended heading order:

1. Abstract and research question
2. Status and scope of claims
3. Result summary
4. Reproduction map
5. Environment and hardware
6. Data acquisition, schema, and license
7. Preprocessing
8. Training or computation
9. Evaluation
10. Models, checkpoints, and artifacts
11. Limitations, uncertainty, and responsible-use notes
12. Citation
13. Contribution, security, and license

Checks:

- [ ] Random seeds, splits, preprocessing, hardware, runtime, and dependency
  lock information are recorded.
- [ ] Dataset and model licenses are compatible with the repository's claims.
- [ ] Reported metrics define exact dataset, split, aggregation, uncertainty,
  and evaluation code revision.
- [ ] Results generated from unavailable private data are marked non-reproducible.
- [ ] Generated artifacts have checksums, provenance, and size expectations.
- [ ] Ethical, privacy, bias, safety, and misuse limitations are addressed when
  material.

### 2.10 Monorepo README

Recommended heading order:

1. Workspace purpose
2. Package or service map
3. Which entry point to choose
4. Repository-wide prerequisites
5. Quick start by audience
6. Shared development commands
7. Package-specific documentation links
8. Dependency and release model
9. Testing and CI
10. Contribution and ownership
11. Security and license

Checks:

- [ ] Package names, paths, owners, lifecycle status, and publish destinations
  are generated or checked from manifests.
- [ ] Root commands state their scope and package-selection behavior.
- [ ] Shared and package-specific versioning are distinguished.
- [ ] Cross-package examples use released or workspace versions intentionally.

### 2.11 Contributor-first flow

The root README should provide a short route to `CONTRIBUTING.md`. The detailed
contributor flow should normally be:

1. Ways to contribute
2. Code of conduct
3. Repository setup
4. Build
5. Test
6. Documentation and examples
7. Style and generated files
8. Change scope and issue expectations
9. Commit and pull-request expectations
10. Review and CI
11. Contributor certificate or sign-off
12. Security-sensitive changes
13. Maintainer contacts

Checks:

- [ ] Setup starts from a clean checkout.
- [ ] Required tools and exact supported versions are discoverable.
- [ ] Generated files state their source and regeneration command.
- [ ] Test tiers and platform-specific tests are distinguished.
- [ ] Contribution rules agree with actual CI and pull-request templates.

### 2.12 Maintainer flow

Normally place this in `MAINTAINERS.md`, `RELEASING.md`, or a maintainer guide:

1. Roles, ownership, and access
2. Triage and support policy
3. Branch and version policy
4. Release preparation
5. Artifact generation and signing
6. Publishing
7. Verification
8. Announcement and changelog
9. Deprecation and migration
10. Security response
11. Backport and end-of-life policy
12. Recovery from failed releases

Checks:

- [ ] Release steps match automation and name responsible credentials without
  exposing them.
- [ ] Artifacts, signatures, checksums, provenance, SBOMs, and registry entries
  are verified after publishing.
- [ ] Failure recovery does not rely on destructive repository operations
  without backups or explicit approval.

## 3. Documentation-set coverage

### 3.1 Root and community files

- [ ] **Required** — `README` or equivalent front door.
- [ ] **Required** — recognized open-source `LICENSE` file with correct project
  and third-party scope.
- [ ] **Required** — contribution route, even if it says contributions are not
  currently accepted.
- [ ] **Required** — vulnerability reporting route that avoids public disclosure
  of unpatched issues.
- [ ] **Recommended** — code of conduct and enforcement/contact route.
- [ ] **Recommended** — support policy distinguishing questions, bugs, feature
  requests, and private security reports.
- [ ] **Conditional** — governance, maintainer, funding, citation, trademark,
  export-control, privacy, or acceptable-use documents.
- [ ] **Conditional** — changelog, release notes, migration guides, and
  end-of-life policy for versioned software.
- [ ] **Conditional** — issue and pull-request templates that agree with
  contribution docs.

### 3.2 User documentation

- [ ] Installation from each supported distribution route.
- [ ] Upgrade, downgrade, migration, uninstall, and cleanup behavior.
- [ ] First useful success with observable expected output.
- [ ] Core concepts and terminology.
- [ ] Task-oriented recipes for common goals.
- [ ] Complete configuration reference including precedence and defaults.
- [ ] Troubleshooting indexed by symptom and containing recovery checks.
- [ ] Accessibility, localization, platform, and environment constraints.
- [ ] Data handling, privacy, telemetry, network, and persistence behavior.
- [ ] Compatibility and support matrix with explicit scope.

### 3.3 Developer and integrator documentation

- [ ] Public API reference.
- [ ] Package, module, namespace, or crate overviews.
- [ ] Architecture and component boundaries.
- [ ] Extension and plugin contracts.
- [ ] Data models, schemas, protocols, and serialization rules.
- [ ] Errors, retries, cancellation, timeouts, concurrency, and resource
  ownership.
- [ ] Compatibility, versioning, deprecation, and migration contracts.
- [ ] Working examples for common and risky operations.
- [ ] Performance model and benchmark methodology where performance is a
  selection criterion.

### 3.4 Operator documentation

- [ ] Deployment topology and prerequisites.
- [ ] Configuration and secret-management contract.
- [ ] State, storage, migrations, backup, restore, and retention.
- [ ] Health, logs, metrics, traces, dashboards, and alerts.
- [ ] Capacity, scaling, availability, and failure modes.
- [ ] Upgrade, rollback, disaster recovery, and incident diagnostics.
- [ ] Security hardening and network boundaries.
- [ ] Administrative APIs and audit behavior.

### 3.5 Contributor and maintainer documentation

- [ ] Reproducible development environment.
- [ ] Build, test, lint, format, docs, and generation commands.
- [ ] Repository map and ownership boundaries.
- [ ] Design decision and architecture records where needed.
- [ ] Release and backport process.
- [ ] Dependency update and vulnerability response policy.
- [ ] Deprecation and end-of-life process.
- [ ] Governance and decision-making route.

## 4. Source-code documentation

Source documentation is a first-class deliverable, not an optional appendix.
Generated API pages are only useful when their comments describe contracts and
the generated navigation exposes the real public surface.

### 4.1 Public-surface inventory

- [ ] Derive the inventory from compiler-visible or package-visible exports,
  not from a hand-maintained count.
- [ ] Include public packages, modules, namespaces, crates, types, traits,
  interfaces, protocols, functions, methods, fields, properties, constants,
  enumerations, variants, errors, exceptions, events, callbacks, macros,
  annotations, attributes, operators, commands, schemas, and extension points.
- [ ] Include public items re-exported from another module.
- [ ] Distinguish supported public API, accidentally visible implementation,
  generated API, experimental API, and intentionally hidden API.
- [ ] Check feature-gated, platform-gated, version-gated, test-only, and
  deprecated surfaces.
- [ ] Check overloads, generic specializations, multi-clause functions, and
  language bindings.
- [ ] Ensure public declarations omitted by the documentation generator are
  either exposed, made non-public, or explicitly justified.
- [ ] Do not count a linter suppression, `doc(hidden)`, `@doc false`, or an
  exclusion glob as documentation coverage.

### 4.2 Package, module, crate, and namespace docs

- [ ] State the unit's purpose and boundary.
- [ ] Name the primary entry points.
- [ ] Explain the core mental model and important terminology.
- [ ] Show a minimal working example.
- [ ] State invariants and assumptions shared by its members.
- [ ] Describe feature flags, platform constraints, initialization, and global
  state.
- [ ] Link to related modules and deeper concepts.
- [ ] Distinguish public contract from internal implementation.
- [ ] Avoid a page that contains only an autogenerated symbol list.

### 4.3 Function and method docs

For every supported public callable, check all applicable contract facets:

- [ ] Purpose and when to choose it.
- [ ] Parameters by exact name.
- [ ] Accepted types beyond what syntax expresses.
- [ ] Units, encoding, locale, timezone, coordinate system, precision, range,
  shape, length, and sentinel values.
- [ ] Null, empty, missing, default, and omitted behavior.
- [ ] Return value, yield value, or stream/event sequence.
- [ ] Errors, exceptions, result variants, status values, and error codes.
- [ ] Panic, abort, trap, assertion, or undefined-behavior conditions.
- [ ] Side effects including mutation, I/O, network access, logging, telemetry,
  caching, and global state.
- [ ] Preconditions, postconditions, and invariants.
- [ ] Ownership, borrowing, aliasing, copying, allocation, and cleanup.
- [ ] Object/resource lifetime and disposal responsibilities.
- [ ] Thread safety, synchronization, reentrancy, actor isolation, and callback
  thread.
- [ ] Blocking, asynchronous, lazy, streaming, cancellation, timeout, backpressure,
  and retry behavior.
- [ ] Ordering, determinism, randomness, stability, and idempotency.
- [ ] Complexity, performance characteristics, memory use, and costly inputs
  when material to correct selection.
- [ ] Security-sensitive behavior and trust boundaries.
- [ ] Availability by platform, version, feature, capability, or permission.
- [ ] Deprecated replacement and migration consequence.
- [ ] A smallest realistic example for non-obvious usage.
- [ ] Cross-links to related callables and concepts.

### 4.4 Type, class, record, and data-model docs

- [ ] The concept represented by an instance.
- [ ] Valid and invalid states.
- [ ] Construction paths and factory preference.
- [ ] Field/property meanings, units, constraints, defaults, and mutability.
- [ ] Equality, identity, hashing, comparison, and ordering semantics.
- [ ] Serialization format, compatibility, unknown-field behavior, and schema
  evolution.
- [ ] Copy, clone, move, ownership, reference, and disposal behavior.
- [ ] Thread safety and mutation visibility.
- [ ] Subclassing, implementation, extension, and sealed-boundary contracts.
- [ ] Generic/type parameters and variance.
- [ ] Lifecycle states and allowed transitions.
- [ ] Memory layout or ABI only when it is a public guarantee.
- [ ] Representative construction and use example.

### 4.5 Enumerations, variants, errors, constants, and fields

- [ ] Every public value has semantic meaning, not merely its spelling repeated.
- [ ] Units and valid combinations are stated.
- [ ] Exhaustiveness and unknown/future-value behavior are stated.
- [ ] Error values say when they occur and whether retry or recovery is safe.
- [ ] Bit flags say whether values may be combined and how unknown bits behave.
- [ ] Constants that are protocol or ABI values name the governing specification.
- [ ] Defaults duplicated in comments are verified against executable defaults.

### 4.6 Constructors, destructors, and lifecycle APIs

- [ ] Required initialization order and ownership transfer.
- [ ] Partial-failure cleanup.
- [ ] Idempotence of close/dispose/free/shutdown operations.
- [ ] Finalizer or garbage-collector limitations.
- [ ] Context-manager, RAII, `defer`, or structured-concurrency expectations.
- [ ] Thread affinity and use-after-close behavior.
- [ ] Resource limits and pool behavior.

### 4.7 Asynchronous, concurrent, and distributed APIs

- [ ] Execution context, scheduler, executor, actor, or callback thread.
- [ ] Ordering and delivery guarantees.
- [ ] Cancellation propagation and cleanup.
- [ ] Timeout scope and clock assumptions.
- [ ] Retry policy and idempotency requirements.
- [ ] Backpressure and buffering.
- [ ] Race, atomicity, memory visibility, and thread-safety guarantees.
- [ ] Partial failure, duplicate delivery, split-brain, and consistency model.
- [ ] Shutdown, draining, and in-flight work behavior.

### 4.8 FFI, native, and ABI documentation

- [ ] Calling convention and symbol visibility.
- [ ] Supported ABI, compiler, standard library, and architecture combinations.
- [ ] Type layout, alignment, packing, endianness, and integer-width assumptions.
- [ ] Pointer provenance, validity, nullability, aliasing, and mutability.
- [ ] Buffer length and ownership for every pointer.
- [ ] Allocation and deallocation pairing across the boundary.
- [ ] String encoding and termination.
- [ ] Callback lifetime, context pointer, thread, and reentrancy.
- [ ] Error transport and thread-local error state.
- [ ] Exception, panic, or unwind behavior across the boundary.
- [ ] Handle lifetime and invalidation.
- [ ] Safety preconditions are adjacent to the unsafe entry point.

### 4.9 Inline implementation comments

- [ ] Explain why, constraints, invariants, protocol rules, surprising tradeoffs,
  and workarounds.
- [ ] Do not paraphrase obvious syntax.
- [ ] Keep comments adjacent to the code whose correctness depends on them.
- [ ] Link workarounds to an issue, upstream defect, specification, or removal
  condition.
- [ ] Give TODO/FIXME notes an actionable condition or tracking reference.
- [ ] Update or remove comments when behavior changes.
- [ ] Mark generated files and point to their source and regeneration command.
- [ ] Keep security and safety invariants explicit even when tests also enforce
  them.

### 4.10 Source examples and doc tests

- [ ] Example code uses the public API rather than private shortcuts.
- [ ] Imports, setup, feature flags, runtime, and teardown are included.
- [ ] Expected output is accurate and deterministic or variability is explained.
- [ ] Examples avoid live secrets, destructive production targets, and
  uncontrolled network dependencies.
- [ ] At least one example exercises an important failure path where misuse is
  costly.
- [ ] Native doctest, compiler, type checker, or extracted-example tooling runs
  in CI when available.
- [ ] Examples excluded from execution are labeled and separately syntax-checked.
- [ ] Snippets shared across documents have one source of truth.

## 5. Document intent and content checks

The four Diátaxis intents are a useful classification, not proof of quality.
Use them to prevent incompatible reader needs from being mixed.

### 5.1 Tutorial

- [ ] Serves a learner rather than acting as an exhaustive reference.
- [ ] Produces an early visible success.
- [ ] Uses a controlled, known-good path.
- [ ] Introduces only concepts needed for the next step.
- [ ] Shows expected intermediate and final results.
- [ ] Includes cleanup where the tutorial creates state.
- [ ] Has been completed from start to finish on a fresh environment.

### 5.2 How-to guide

- [ ] Names a concrete user goal.
- [ ] States prerequisites and starting state.
- [ ] Includes decision points and meaningful variants.
- [ ] States success verification.
- [ ] Covers common failures and safe recovery.
- [ ] Avoids turning into a conceptual essay or complete option reference.

### 5.3 Reference

- [ ] Mirrors the actual product structure and naming.
- [ ] Is complete within its declared scope.
- [ ] Defines syntax, types, defaults, constraints, errors, and version
  availability.
- [ ] Is searchable and predictably organized.
- [ ] Generated sections identify source of truth and generation version.
- [ ] Does not hide meaningful behavior behind vague prose.

### 5.4 Explanation

- [ ] Answers why the system is shaped this way.
- [ ] Establishes a mental model and terminology.
- [ ] Discusses alternatives, tradeoffs, constraints, and consequences.
- [ ] Clearly separates current behavior from history and future plans.
- [ ] Links back to actionable tutorials, how-tos, and reference.

### 5.5 Troubleshooting

- [ ] Organized by observable symptom or error text.
- [ ] Gives likely causes in a useful diagnostic order.
- [ ] Uses non-destructive checks before state-changing remedies.
- [ ] Shows expected diagnostic output.
- [ ] Separates workaround from root-cause fix.
- [ ] Includes rollback or recovery for risky remedies.
- [ ] Redacts tokens, user data, and sensitive paths from diagnostic examples.
- [ ] States when and where to seek support and what safe evidence to include.

## 6. Project-type specialties

### 6.1 Command-line tools

- [ ] Commands, subcommands, arguments, options, aliases, defaults, exit codes,
  streams, signals, and configuration precedence.
- [ ] Interactive versus non-interactive behavior.
- [ ] Shell quoting and platform path behavior.
- [ ] Machine-readable output stability.
- [ ] Completion generation and installation.
- [ ] Destructive action preview, confirmation, scope, and recovery.

### 6.2 Libraries and SDKs

- [ ] Package installation, import paths, public API, compatibility, feature
  selection, thread safety, error model, lifecycle, and migration.
- [ ] Supported language/runtime/compiler matrix.
- [ ] Semantic-versioning policy and what counts as a breaking change.
- [ ] Examples for synchronous, asynchronous, and failure behavior as applicable.

### 6.3 Services and daemons

- [ ] Deployment, ports, protocols, state, configuration, secrets, health,
  observability, scale, backup, restore, upgrade, rollback, and hardening.
- [ ] Privilege, user/group, filesystem, and network requirements.
- [ ] Graceful shutdown and in-flight request behavior.

### 6.4 Web APIs

- [ ] Authentication, authorization, resources, methods, schemas, errors,
  pagination, rate limits, retries, idempotency, versioning, and deprecation.
- [ ] Examples for each authentication mode and major error family.
- [ ] Machine-readable contract is generated or validated against implementation.

### 6.5 Event-driven systems

- [ ] Broker and protocol versions, channel/topic names, message schemas, keys,
  ordering, delivery, acknowledgement, retry, dead-letter, replay, and retention.
- [ ] Producer and consumer ownership.
- [ ] Schema compatibility and event-version migration.
- [ ] AsyncAPI or equivalent contract when appropriate.

### 6.6 Databases, migrations, and data formats

- [ ] Schema purpose, entities, relationships, keys, constraints, indexes, units,
  nullability, time semantics, encoding, and collation.
- [ ] Transaction, isolation, lock, concurrency, and failure behavior.
- [ ] Migration direction, compatibility window, backup, rollback, and data-loss
  risk.
- [ ] Query/procedure inputs, result sets, side effects, permissions, and
  performance expectations.
- [ ] Format grammar or schema, canonical examples, validation, versioning,
  unknown fields, limits, and security considerations.

### 6.7 Infrastructure as code and deployment charts

- [ ] Provider/tool versions, required credentials and permissions, state
  backend, inputs, outputs, defaults, resources created, costs, regions, and
  quotas.
- [ ] Plan/preview before apply.
- [ ] Drift, upgrades, imports, destruction scope, and disaster recovery.
- [ ] Secret values are referenced, never embedded.
- [ ] Docker, Compose, Kubernetes, Helm, Terraform, Pulumi, Nix, and cloud
  examples are checked with the native parser or validation command.

### 6.8 Plugins and extension systems

- [ ] Discovery, manifest, lifecycle, capabilities, permissions, hooks, data
  contracts, compatibility, sandbox, failure isolation, and uninstallation.
- [ ] Stable versus internal extension points.
- [ ] Host and plugin upgrade order.

### 6.9 Security-sensitive or cryptographic software

- [ ] Threat model, intended use, prohibited use, trust assumptions, key
  lifecycle, randomness, side channels, zeroization, and failure behavior.
- [ ] Protocol version and governing specification.
- [ ] Security guarantees are narrow, evidenced, and not inferred from test
  success.
- [ ] Examples do not encourage custom cryptographic construction.
- [ ] Vulnerability reporting and supported-version policy are prominent.

### 6.10 Embedded, systems, and hardware projects

- [ ] Target hardware, architecture, toolchain, memory/flash limits, clocks,
  voltage, pinout, peripherals, boot process, flashing, and recovery.
- [ ] Unsafe operations and bricking risk.
- [ ] Concurrency, interrupts, timing, real-time assumptions, and power behavior.
- [ ] Hardware revision and firmware compatibility.

### 6.11 Build tools, generators, and compilers

- [ ] Inputs, outputs, grammar, resolution model, incremental behavior, cache,
  determinism, diagnostics, exit codes, plugins, and generated-file ownership.
- [ ] Bootstrap requirements and reproducible build path.
- [ ] Generated output compatibility policy.

## 7. Language and ecosystem specialties

Apply only detected language profiles. Use the repository's configured native
tool when it differs from the common tool named here.

### 7.0 Universal fallback for any language

Use this profile for every language and especially for one not listed below.

- [ ] Identify the language specification, current project-supported versions,
  native or dominant documentation convention, generator, linter, and example
  test mechanism from authoritative current sources.
- [ ] Derive the public interface from the compiler, interpreter, package
  manifest, export rules, or generated metadata.
- [ ] Document package/module purpose and every supported public declaration.
- [ ] Apply all relevant contract facets from section 4: inputs, outputs,
  failures, side effects, invariants, lifetime/ownership, concurrency,
  performance, security, availability, and examples.
- [ ] Check language-specific semantics that prose can clarify but a signature
  cannot, including dynamic behavior, metaprogramming, generated code,
  conditional compilation, and foreign interfaces.
- [ ] Generate the reference, fail on unexplained warnings, compare it with the
  public inventory, and compile/run/type-check examples.
- [ ] Record the sources and versions used; do not invent annotation syntax or
  apply a similar language's convention by analogy.

### 7.1 Rust

- [ ] Use crate/module docs (`//!`) for purpose, mental model, entry points, and
  examples; use `///` for public items.
- [ ] Document public APIs exposed under every supported feature combination.
- [ ] Include applicable `# Errors`, `# Panics`, and `# Safety` contracts.
- [ ] State ownership, borrowing, lifetimes, pinning, allocation, `Send`/`Sync`,
  cancellation, and async behavior where they affect correct use.
- [ ] Document unsafe preconditions at the unsafe function/trait boundary and
  justify invariants near unsafe blocks.
- [ ] Exercise examples with rustdoc doctests; distinguish code intentionally
  marked `no_run`, `compile_fail`, or `ignore`.
- [ ] Check intra-doc links and generated rustdoc navigation.
- [ ] Check optional features, target-specific items, MSRV, and semver-sensitive
  trait implementations.

Native references: [rustdoc writing
guide](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html) and
[rustdoc tests](https://doc.rust-lang.org/rustdoc/documentation-tests.html).

### 7.2 Go

- [ ] Give every exported package, type, function, method, variable, and
  constant a doc comment beginning with the declared name or accepted form.
- [ ] Package comments explain purpose and major entry points.
- [ ] State useful zero value, mutability, goroutine safety, blocking, context
  cancellation, ownership of returned buffers, and error sentinel/type behavior.
- [ ] Examples follow `Example`, `ExampleType`, or `ExampleType_Method`
  conventions when they should appear and run under `go test`.
- [ ] Deprecations begin with the recognized `Deprecated:` paragraph.
- [ ] Check rendered `go doc`/pkgsite output, examples, internal packages, build
  tags, modules, and minimum Go version.

Native reference: [Go doc comments](https://go.dev/doc/comment).

### 7.3 Python

- [ ] Use docstrings for public modules, packages, classes, functions, methods,
  and public attributes where supported.
- [ ] Keep the summary line separate from the detailed body.
- [ ] Document exact parameter names, keyword-only behavior, defaults not clear
  from the signature, returns/yields, raised exceptions, side effects, and
  calling restrictions.
- [ ] State iterator/generator laziness, async behavior, context-manager
  lifecycle, mutability, thread/process safety, and dtype/shape/units for
  scientific APIs.
- [ ] Choose one parseable house style compatible with the configured generator
  rather than mixing Google, NumPy, and Sphinx field syntax.
- [ ] Check type hints and prose for contradiction.
- [ ] Run doctest or extracted examples where appropriate; do not make unstable
  output exact without normalization.
- [ ] Check built distributions to ensure README, typing markers, stubs, and
  referenced docs are included.

Native references: [PEP 257](https://peps.python.org/pep-0257/) and
[doctest](https://docs.python.org/3/library/doctest.html).

### 7.4 JavaScript

- [ ] Document public modules, exports, classes, functions, properties, events,
  callbacks, and typedefs using the project's JSDoc-compatible convention.
- [ ] State runtime and module-system support: browser/Node/Deno/Bun,
  ESM/CommonJS, package exports, and bundler assumptions.
- [ ] Document promise resolution/rejection, sync throws, callback timing,
  event payloads, abort signals, resource cleanup, and mutation.
- [ ] State accepted structural shapes when the source lacks static types.
- [ ] Check examples in each claimed runtime and both import forms when both are
  supported.
- [ ] Check generated API navigation and symbol resolution rather than merely
  detecting `/**` blocks.

Native tool reference: [JSDoc](https://jsdoc.app/).

### 7.5 TypeScript

- [ ] Document the exported surface that consumers receive from package entry
  points and declaration files.
- [ ] Explain generics, constraints, conditional/mapped types, discriminated
  unions, overload selection, branded/opaque types, and variance when not
  obvious.
- [ ] Document each union branch and meaningful property.
- [ ] State promise rejection, cancellation, runtime validation, and the gap
  between compile-time types and untrusted runtime input.
- [ ] Use TSDoc/JSDoc tags supported by the configured generator and editor.
- [ ] Check API report/declaration changes when API Extractor or an equivalent
  contract tool exists.
- [ ] Type-check snippets and inspect TypeDoc or equivalent output, including
  re-exports and external links.

Native reference: [TypeDoc doc comments](https://typedoc.org/documents/Doc_Comments.html).

### 7.6 Java

- [ ] Use Javadoc for public modules, packages, types, constructors, methods,
  fields, enum constants, annotation members, and record components as
  applicable.
- [ ] Start with a useful summary; document type parameters, parameters, return
  values, thrown exceptions, deprecation, and version/since information.
- [ ] State nullability, mutability, thread safety, inheritance/subclassing
  contracts, resource ownership, and checked versus unchecked failure.
- [ ] Keep `@throws` conditions aligned with implementation and inherited
  contracts.
- [ ] Link overloads and related types precisely.
- [ ] Run Javadoc with warnings treated according to project policy and inspect
  module/package overview pages and broken links.

Native reference: [Javadoc documentation-comment
specification](https://docs.oracle.com/en/java/javase/26/docs/specs/javadoc/doc-comment-spec.html).

### 7.7 Kotlin

- [ ] Provide KDoc for supported public APIs; use the first paragraph as the
  summary.
- [ ] Document type parameters, primary constructor, properties, extension
  receiver, return value, useful exception conditions, samples, and version.
- [ ] State nullability beyond syntax, coroutine context, suspension,
  cancellation, Flow/channel coldness and backpressure, and thread safety.
- [ ] Check multiplatform `expect`/`actual` differences and platform
  availability.
- [ ] Use `@Deprecated` for compiler-visible deprecation and provide replacement
  guidance.
- [ ] Generate and inspect Dokka output; ensure `@suppress` is not masking
  supported API.

Native references: [KDoc](https://kotlinlang.org/docs/kotlin-doc.html) and
[library documentation
guidance](https://kotlinlang.org/docs/api-guidelines-informative-documentation.html).

### 7.8 C

- [ ] Document installed/public headers as the contract and keep implementation
  comments subordinate to them.
- [ ] State pointer ownership, nullability, lengths, aliasing, mutability,
  alignment, allocation/free pairing, and lifetime.
- [ ] State integer width, overflow, sentinel, endianness, encoding, errno,
  return-code, and thread-local error behavior.
- [ ] Document preprocessor conditions, feature-test macros, platform ABI,
  calling convention, symbol visibility, and version availability.
- [ ] Explain callback context, thread, reentrancy, and lifetime.
- [ ] Check generated Doxygen or configured output and compile examples under
  supported compilers and warning levels.

Common tool reference: [Doxygen comment
blocks](https://www.doxygen.nl/manual/docblocks.html).

### 7.9 C++

- [ ] Apply all relevant C/ABI checks plus templates, concepts, overloads,
  deduction, move semantics, exception guarantees, and allocator behavior.
- [ ] State ownership in smart/raw pointers, reference lifetime, iterator/range
  invalidation, view/string-view lifetime, and borrowing.
- [ ] Document RAII, destruction order, `noexcept`, strong/basic exception
  guarantee, and moved-from state.
- [ ] State thread safety, data-race rules, synchronization, and callback thread.
- [ ] Distinguish header-only, module, ABI, compiler, standard-library, and C++
  language-version support.
- [ ] Compile documentation examples with supported configurations and inspect
  generated cross-links and overload grouping.

Common tool reference: [Doxygen comment
blocks](https://www.doxygen.nl/manual/docblocks.html).

### 7.10 C# and .NET

- [ ] Use compiler-recognized XML documentation for public types and members.
- [ ] Cover summary, type parameters, parameters, returns/value, exceptions,
  remarks, examples, related APIs, and inheritance where applicable.
- [ ] State nullable-reference behavior, async/cancellation, `IDisposable` or
  `IAsyncDisposable` ownership, enumeration laziness, thread safety, and event
  subscription lifetime.
- [ ] Check extension methods, records, delegates, events, attributes, and
  generic constraints.
- [ ] Enable XML documentation output and relevant warnings; validate well-formed
  XML and referenced parameter names.
- [ ] Inspect IntelliSense and generated reference, not just the emitted XML.

Native references: [C# documentation
comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-specification/documentation-comments)
and [.NET API comment
guidance](https://learn.microsoft.com/en-us/contribute/content/dotnet/api-documentation).

### 7.11 F#

- [ ] Use `///` XML documentation on public modules, values, types, members, and
  signatures.
- [ ] Explain curried argument groups, generic constraints, units of measure,
  active patterns, computation expressions, discriminated unions, and partial
  functions where relevant.
- [ ] State null interop, asynchronous workflow/task behavior, sequence laziness,
  mutation, and exception behavior.
- [ ] Prefer documenting the `.fsi` public contract when signature files define
  the exposed API.
- [ ] Enable XML documentation generation and F# documentation warnings.

Native reference: [F# XML
documentation](https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/xml-documentation).

### 7.12 Swift and Objective-C

- [ ] Use documentation comments recognized by Xcode/DocC for public symbols.
- [ ] Document parameters, return, thrown errors, availability, deprecation,
  nullability, ownership, and examples.
- [ ] State async/await cancellation, actor isolation, `Sendable`, callback
  queues, retain cycles, and Objective-C bridging.
- [ ] Cover protocol requirements, associated types, generic constraints,
  property wrappers, and result builders where applicable.
- [ ] Check Swift Package and framework documentation builds, symbol links,
  tutorials, and platform availability in DocC.

Native reference: [Apple documentation
authoring](https://developer.apple.com/documentation/xcode/writing-documentation).

### 7.13 Dart and Flutter

- [ ] Use `///` for public libraries, types, constructors, members, top-level
  functions, and variables.
- [ ] Make the first paragraph a useful summary and use resolvable bracket links
  for in-scope identifiers.
- [ ] Document Future errors, Stream subscription/cancellation/broadcast
  behavior, isolates, nullability, widget lifecycle, and `BuildContext` limits.
- [ ] Avoid separate conflicting comments for a property getter and setter.
- [ ] Include code samples where they materially clarify use.
- [ ] Run analyzer documentation lints and generate/inspect `dart doc`.

Native reference: [Effective Dart:
Documentation](https://dart.dev/effective-dart/documentation).

### 7.14 Ruby

- [ ] Document public modules, classes, methods, attributes, constants, blocks,
  mixins, refinements, and metaprogrammed APIs using the configured RDoc or YARD
  convention.
- [ ] State positional/keyword arguments, splats, block yield values, return,
  raised exceptions, mutation, thread/Ractor safety, and enumerator behavior.
- [ ] Document dynamic methods at their stable public definition point.
- [ ] Ensure examples work against the supported Ruby and dependency versions.
- [ ] Generate and inspect API documentation; check native extension surfaces
  separately.

Native tool reference: [RDoc documentation
authoring](https://ruby.github.io/rdoc/index.html).

### 7.15 PHP

- [ ] Use PHPDoc DocBlocks for public files, namespaces, classes, interfaces,
  traits, enums, functions, methods, properties, and constants where useful.
- [ ] Keep native type declarations and DocBlock types consistent; use DocBlocks
  for shapes, templates/generics, callables, and refinements syntax cannot
  express.
- [ ] Document parameters, returns, thrown exceptions, side effects, magic
  methods/properties, deprecation, and version.
- [ ] State nullability, mutation, reference parameters, generator behavior, and
  resource ownership.
- [ ] Run the configured static analyzer and generate/inspect phpDocumentor or
  equivalent output.

Native-tool reference: [phpDocumentor
DocBlocks](https://docs.phpdoc.org/guide/guides/docblocks.html).

### 7.16 Elixir

- [ ] Use `@moduledoc`, `@doc`, and `@typedoc` for supported public modules,
  functions/macros, callbacks, and types.
- [ ] Keep the first paragraph concise; refer to functions by name/arity and
  types/callbacks with resolvable forms.
- [ ] Document accepted pattern shapes, return tuples, raised exceptions,
  messages, process ownership, supervision, timeouts, and side effects.
- [ ] Add `:since` and deprecation metadata where applicable.
- [ ] Test IEx examples with ExUnit doctests.
- [ ] Treat `@doc false`/`@moduledoc false` as intentional API hiding, never as
  coverage.

Native reference: [Elixir documentation
guide](https://hexdocs.pm/elixir/writing-documentation.html).

### 7.17 Erlang

- [ ] Use `-moduledoc` and `-doc` for public modules, functions, types, and
  callbacks; keep specs and prose consistent.
- [ ] Document function name/arity, message formats, mailbox effects, process
  links/monitors, timeout, supervision, and return/error tuples.
- [ ] Use `since`, `deprecated`, `group`, and equivalence metadata where useful.
- [ ] Test eligible examples with `ct_doctest`.
- [ ] Inspect EEP-48/ExDoc output and ensure `-doc false` does not conceal a
  supported interface.

Native reference: [Erlang system documentation
guide](https://www.erlang.org/doc/system/documentation.html).

### 7.18 Scala

- [ ] Provide Scaladoc for public packages, classes, traits, objects, methods,
  members, extension methods, givens, and enums.
- [ ] Document value and type parameters, primary constructors, returns,
  exceptions, contextual/implicit parameters, and examples.
- [ ] Explain variance, higher-kinded types, type classes, effects, laziness,
  concurrency, and collection-view behavior when relevant.
- [ ] Distinguish Scala 2/3 syntax and cross-built behavior.
- [ ] Generate and inspect Scaladoc links, inherited members, source links, and
  version-specific output.

Native reference: [Scaladoc style
guide](https://docs.scala-lang.org/style/scaladoc.html).

### 7.19 Clojure

- [ ] Give public namespaces and Vars useful docstrings.
- [ ] Document argument shapes, destructuring, return values, nil behavior,
  laziness, realization, side effects, dynamic bindings, and thread safety.
- [ ] Make macro evaluation and quoting behavior explicit.
- [ ] Record `:added`, `:deprecated`, `:private`, and `:arglists` metadata
  consistently where the project uses them.
- [ ] Check generated cljdoc/Codox or configured reference and examples across
  supported Clojure/JVM versions.

Native references: [Clojure Var
metadata](https://clojure.org/reference/vars) and
[metadata](https://clojure.org/reference/metadata).

### 7.20 Haskell

- [ ] Add Haddock module headers and public declaration comments.
- [ ] Document totality/partiality, strictness/laziness, evaluation effects,
  complexity, exceptions, bottom/nontermination, and law expectations.
- [ ] Explain typeclass laws, instances, higher-kinded abstractions, effect
  stacks, resource lifetime, and concurrency where relevant.
- [ ] Include checked examples using doctest or project-native tooling.
- [ ] Generate Haddock with warnings and inspect re-exports, instance docs,
  source links, and package-version compatibility.

Native tool reference: [Haddock](https://www.haskell.org/haddock/).

### 7.21 OCaml

- [ ] Document the public module interface, especially `.mli` signatures that
  define the contract.
- [ ] Cover values, modules, functors, module types, variants, records, objects,
  exceptions, polymorphism, and labeled/optional arguments.
- [ ] State mutation, aliasing, exceptions, effects, concurrency/domain safety,
  and resource ownership.
- [ ] Generate `odoc`, inspect module hierarchy and cross-references, and include
  standalone `.mld` conceptual pages where needed.

Native reference: [OCaml documentation with
odoc](https://ocaml.org/docs/generating-documentation).

### 7.22 R

- [ ] Use roxygen2 or the configured source form for exported functions,
  datasets, classes, generics, methods, and package-level documentation.
- [ ] Document parameters, return structure, side effects, warnings/errors,
  missing values, recycling, vectorization, environments, and non-standard
  evaluation.
- [ ] For statistical functions, define assumptions, formula semantics, units,
  randomness, seeds, convergence, and uncertainty.
- [ ] Keep examples fast and self-contained; distinguish `\dontrun` from examples
  that are actually tested.
- [ ] Generate `.Rd`, run package checks, and inspect links and rendered help.

Native and ecosystem references: [Writing R
Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html#Documenting-functions)
and [roxygen2 function
documentation](https://roxygen2.r-lib.org/articles/rd.html).

### 7.23 Julia

- [ ] Attach Markdown docstrings to public modules, functions/methods, macros,
  types, fields, and globals.
- [ ] Show the signature or common call form, summary, details, and executable
  REPL example.
- [ ] Document multiple dispatch expectations, supported type domains, mutation
  (`!`), allocation, type stability/performance, exceptions, and dimensional
  units.
- [ ] Explain task/thread safety, distributed execution, randomness, and GPU
  constraints where applicable.
- [ ] Use `Docs.undocumented_names` or equivalent coverage checks and run
  Documenter doctests when configured.

Native reference: [Julia
documentation](https://docs.julialang.org/en/v1/manual/documentation/).

### 7.24 Lua

- [ ] Select and consistently use the project's documentation annotation system
  because the Lua language itself does not standardize API doc comments.
- [ ] Document modules/tables, functions, parameters, multiple return values,
  nil behavior, metatables/metamethods, callbacks, and globals.
- [ ] State Lua version, LuaJIT differences, C module ABI, ownership, stack
  effects, yieldability, and coroutine behavior.
- [ ] Generate and inspect LDoc or the configured output and run examples with
  each supported interpreter.

Language reference: [Lua reference manuals](https://lua.org/manual/).

### 7.25 POSIX shell, Bash, and other shells

- [ ] Put usage/help text in the executable interface and keep README examples
  synchronized with it.
- [ ] State required shell and version; do not label Bash syntax as POSIX `sh`.
- [ ] Document arguments, environment, standard streams, exit statuses, files,
  signals, traps, cleanup, dependencies, privileges, and portability.
- [ ] Quote examples safely and identify commands that modify or delete data.
- [ ] Check with the target shells, ShellCheck where applicable, and isolated
  temporary directories.
- [ ] Avoid examples that interpolate untrusted text or encourage piping
  network content directly to a privileged shell without verification.

### 7.26 PowerShell

- [ ] Provide comment-based help for exported functions and scripts or link
  correctly to external help.
- [ ] Cover `.SYNOPSIS`, `.DESCRIPTION`, each `.PARAMETER`, repeated `.EXAMPLE`,
  `.INPUTS`, `.OUTPUTS`, `.NOTES`, and `.LINK` as applicable.
- [ ] State pipeline input, output object types, remoting, platforms, required
  modules, privileges, and `SupportsShouldProcess` behavior.
- [ ] Document terminating versus non-terminating errors and meaningful exit
  codes.
- [ ] Validate `Get-Help` rendering and use PSScriptAnalyzer while recognizing
  that its presence rule does not prove content quality.

Native reference: [PowerShell comment-based
help](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_comment_based_help).

### 7.27 Zig

- [ ] Use `//!` at the start of a namespace for its overview and `///` on
  declarations.
- [ ] Document public types/functions, error sets, allocators, ownership,
  sentinel-terminated data, alignment, optional pointers, and lifetime.
- [ ] State comptime behavior, target/ABI assumptions, thread safety, and
  undefined-behavior preconditions.
- [ ] Generate package documentation and compile/test examples for supported Zig
  versions and targets.

Native reference: [Zig language
documentation](https://ziglang.org/documentation/master/).

### 7.28 Nim

- [ ] Use `##` documentation comments for exported modules and symbols.
- [ ] Document procedures, iterators, templates, macros, concepts, effects,
  exceptions, ownership/ARC-ORC behavior, and compile-time behavior.
- [ ] Keep export markers and generated public docs aligned.
- [ ] Run `nim doc`/project documentation, inspect links, and compile runnable
  examples on supported backends.

Native reference: [Nim DocGen
guide](https://nim-lang.org/docs/docgen.html).

### 7.29 Fortran

- [ ] Document every public module, derived type, procedure, generic interface,
  and public data object using the project's FORD/Doxygen-compatible convention.
- [ ] Record each dummy argument's `intent`, shape/rank, kind, units, optional
  behavior, allocation, and aliasing expectations.
- [ ] State numerical assumptions, precision, array ordering, bounds,
  coarray/OpenMP/MPI behavior, and C interoperability.
- [ ] Generate reference docs and compile examples with supported compilers and
  relevant standards modes.

Ecosystem reference: [Fortran modules and documentation
practice](https://fortran-lang.org/learn/best_practices/modules_programs/).

### 7.30 Solidity and smart contracts

- [ ] Use NatSpec for every public ABI element, including public state-variable
  getters.
- [ ] Separate user-facing transaction meaning from developer-facing invariants
  and implementation detail.
- [ ] Document parameters, named returns, events, custom errors, access control,
  payable/value behavior, state changes, reentrancy assumptions, and upgrade
  behavior.
- [ ] State chain/network, compiler/EVM version, proxy/storage-layout contract,
  oracle assumptions, gas implications, and admin trust.
- [ ] Generate compiler user/developer documentation JSON and compare it with
  ABI and deployed/versioned artifacts.
- [ ] Never treat documentation or test success as a security audit.

Native reference: [Solidity
NatSpec](https://docs.soliditylang.org/en/latest/natspec-format.html).

### 7.31 SQL and database code

- [ ] Document schemas, tables, columns, keys, constraints, indexes, views,
  functions, triggers, procedures, roles, and migrations that are public to
  operators or integrators.
- [ ] State input/output types, nullability, collation, timezone, precision,
  transaction boundaries, isolation, locks, side effects, and permissions.
- [ ] Explain query cardinality, ordering guarantees, pagination, expected
  indexes, and performance-sensitive scale assumptions.
- [ ] Document migration compatibility, lock duration, backfill, rollback,
  backup, and irreversible data loss.
- [ ] Validate examples on every claimed database engine/version; never present
  one dialect as portable SQL without proof.

### 7.32 Interface-description and schema languages

- [ ] OpenAPI documents authentication, operation IDs, schemas, examples,
  errors, pagination, headers, callbacks/webhooks, and versioning.
- [ ] AsyncAPI documents servers, channels, operations, messages, correlation,
  bindings, delivery assumptions, and security.
- [ ] GraphQL documents types, fields, arguments, defaults, nullability,
  deprecation, errors, pagination conventions, authorization, and cost limits.
- [ ] Protocol Buffers/gRPC documents services, methods, field meaning, units,
  enum zero values, reserved numbers/names, compatibility, deadlines, streaming,
  status codes, and retry/idempotency.
- [ ] JSON Schema documents identifiers, dialect, formats, defaults versus
  annotations, examples, composition, unknown properties, and compatibility.
- [ ] Generated clients/servers and published schema artifacts match the checked
  source and target revision.

Current specification references at the research date:
[OpenAPI](https://spec.openapis.org/oas/latest.html),
[AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0),
[GraphQL September 2025](https://spec.graphql.org/September2025/), and
[JSON Schema](https://json-schema.org/specification).

## 8. Open-source trust, community, and lifecycle

### 8.1 Licensing and attribution

- [ ] The project has a recognized license or explicitly states that no license
  is granted.
- [ ] README license wording matches the actual license file.
- [ ] Copyright notices and SPDX identifiers are accurate for their files.
- [ ] Dependencies, vendored code, copied snippets, fonts, images, datasets,
  models, examples, and generated assets have compatible terms and attribution.
- [ ] Dual/multi-license choice is unambiguous.
- [ ] Contribution terms, DCO, or CLA expectations are stated before submission.
- [ ] Distribution artifacts contain required license and notice files.
- [ ] REUSE conformance is checked when the project adopts REUSE.

References: [OSI licenses](https://opensource.org/licenses) and
[REUSE specification](https://reuse.software/spec/).

### 8.2 Security

- [ ] Private vulnerability-reporting contact or platform route exists.
- [ ] Supported versions and response expectations are stated.
- [ ] Public issue templates redirect undisclosed vulnerabilities.
- [ ] Threat model and trust boundaries exist for security-sensitive systems.
- [ ] Authentication, authorization, secret handling, encryption, network
  exposure, sandboxing, and update trust are documented where relevant.
- [ ] Commands and examples contain no real or plausible active credentials.
- [ ] Secret scanning and push protection are not described as complete
  prevention.
- [ ] Security guarantees are not inferred solely from unit tests, fuzzing,
  static analysis, or a linter.

### 8.3 Community health and governance

- [ ] Contribution route is welcoming, scoped, and operational.
- [ ] Code of conduct includes enforcement/reporting information.
- [ ] Support channels state their intended use and response expectations.
- [ ] Governance, maintainers, decision rights, and succession are documented
  when project scale requires them.
- [ ] Issue labels/templates do not demand data the project will not use.
- [ ] Community links are current and do not point to abandoned channels.

Reference: [GitHub community
profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories).

### 8.4 Versioning, change, and support

- [ ] Versioning policy defines public API and breaking change.
- [ ] Support window and end-of-life behavior are explicit.
- [ ] Changelog distinguishes user impact from internal activity.
- [ ] Deprecations name replacement, introduction version, removal horizon, and
  migration.
- [ ] Upgrade guides cover data/schema/config/API changes and rollback.
- [ ] Release notes link to exact artifacts and revision.
- [ ] Claims about latest/current/default versions are date-checked.

Reference: [Semantic Versioning](https://semver.org/).

### 8.5 OpenSSF baseline-aligned checks

- [ ] User guide exists for basic functionality.
- [ ] Build instructions exist and identify required dependencies.
- [ ] Contribution guide exists.
- [ ] Support scope and duration are documented.
- [ ] Dependency-management policy and automated dependency updates are
  addressed.
- [ ] Tests and test-running instructions exist.
- [ ] Architecture and security-sensitive interfaces are documented at the
  appropriate maturity level.
- [ ] Public interfaces and security reporting are documented.
- [ ] Legal and licensing material is present.

Reference: [OpenSSF OSPS Baseline
2026-02-19](https://baseline.openssf.org/versions/2026-02-19).

## 9. Writing, accessibility, localization, and visual content

### 9.1 Language quality

- [ ] Important information appears before background detail.
- [ ] Headings describe the reader's question or task.
- [ ] Paragraphs and sentences have one clear job.
- [ ] Terms are consistent and included in a glossary only when repeated lookup
  is useful.
- [ ] Pronouns have clear antecedents.
- [ ] Instructions identify the actor and expected outcome.
- [ ] Warnings appear before the risky action.
- [ ] Avoid idioms, jokes, cultural references, and directional language that
  complicate translation.
- [ ] Dates, units, timezones, locale, and number formats are unambiguous.
- [ ] Text does not rely on color, shape, position, or typography alone.

Reference: [Google developer-documentation global
guidance](https://developers.google.com/style/translation).

### 9.2 Accessibility

- [ ] Heading levels form a meaningful hierarchy.
- [ ] Link text makes sense out of context.
- [ ] Images have appropriate alternative text; decorative images use the
  platform's decorative treatment.
- [ ] Complex diagrams have an adjacent textual explanation.
- [ ] Tables have headers and are not used for visual layout.
- [ ] Instructions do not rely only on color or spatial position.
- [ ] Animated content has controls or alternatives where needed.
- [ ] Captions/transcripts exist for meaningful audio/video.
- [ ] Code samples are not the only explanation of a concept.
- [ ] Rendered sites meet the project's declared WCAG target.

References: [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[WAI writing tips](https://www.w3.org/WAI/tips/writing/), and the
[WAI alt-text decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/).

### 9.3 Diagrams, screenshots, and generated media

- [ ] Every visual has a reader task and a maintained source.
- [ ] Labels match current product terminology.
- [ ] Architecture diagrams distinguish logical, deployment, trust, and data
  flow views rather than mixing them.
- [ ] Screenshots redact personal data, credentials, internal URLs, and machine
  identifiers.
- [ ] Screenshots are not used where copyable text is needed.
- [ ] Version-sensitive visuals name their version or are regenerated.
- [ ] Source files, fonts, icons, and images have compatible licenses.
- [ ] A text alternative carries the important information.

## 10. Truth and validation gates

### 10.1 Claim ledger

For every material claim, record:

| Field | Check |
| --- | --- |
| Claim | Exact statement a reader may rely on |
| Audience | Who is affected if it is wrong |
| Source of truth | Code, manifest, config, CI, artifact, spec, or authoritative declaration |
| Scope | Version, platform, feature, package, revision, and date |
| Verification | Command, inspection, or external authoritative source |
| Result | Proved, declared, planned, or unknown |
| Documentation locations | Every place the claim is repeated |

Material claim families:

- [ ] Install and uninstall commands.
- [ ] Package names, import paths, executable names, and file paths.
- [ ] Defaults, option names, environment variables, and precedence.
- [ ] Supported versions, platforms, features, and compatibility.
- [ ] API signatures, schemas, error behavior, and examples.
- [ ] Output, screenshots, benchmarks, performance, and scale.
- [ ] Security, privacy, telemetry, and data-retention behavior.
- [ ] Project maturity, maintenance, support, and roadmap.
- [ ] Counts, percentages, coverage, inventory, and generated statistics.
- [ ] License, attribution, and distribution contents.

### 10.2 Non-circular verification

- [ ] A README claim is not verified by another document that copied the README.
- [ ] A hand-maintained API count is not verified by recomputing from that same
  list.
- [ ] Documentation coverage is not proved by suppressing missing-doc warnings.
- [ ] A generated page is checked against source exports, not only against its
  own generation manifest.
- [ ] A test described in docs is checked in CI/config or executed, not assumed
  from its name.
- [ ] A compatibility table is checked against actual build/test/release
  configurations.
- [ ] A release artifact is inspected directly rather than inferred from the
  source directory.
- [ ] A benchmark claim is reproduced from the benchmark harness and raw result,
  not copied from prose.

### 10.3 Command and example validation

- [ ] Commands are copied exactly from the edited documentation into a fresh or controlled
  environment.
- [ ] Prerequisites and setup are no more permissive than documented.
- [ ] Commands are tested under each claimed operating system/shell or scope is
  narrowed.
- [ ] Expected stdout, stderr, exit status, files, network effects, and cleanup
  are checked.
- [ ] Examples do not depend on undeclared local files, caches, environment
  variables, credentials, or prior commands.
- [ ] Random, time-dependent, network-dependent, and concurrent output is
  normalized or described without false exactness.
- [ ] Copy/paste boundaries exclude prompts, line numbers, and explanatory text.
- [ ] Destructive examples use disposable targets and include recovery.
- [ ] Code snippets compile, type-check, parse, or run with native tooling.

Reference: [Google code-sample
guidance](https://developers.google.com/style/code-samples).

### 10.4 Generated API documentation validation

- [ ] The documentation generator finishes without unexplained warnings.
- [ ] The public inventory is compared with rendered public items.
- [ ] Package/module/crate overview pages contain meaningful prose.
- [ ] Navigation reaches central APIs without knowing internal file names.
- [ ] Overloads, re-exports, feature-gated items, inherited members, and
  deprecated items render correctly.
- [ ] Cross-references and source links resolve.
- [ ] Examples render correctly and remain executable.
- [ ] Search/index output includes the expected symbols.
- [ ] No central page is blank or mostly an autogenerated name list.
- [ ] Hidden/excluded items have explicit API-boundary justification.
- [ ] The published output is inspected, not only the local source comments.

### 10.5 Link and navigation validation

- [ ] Local files exist in source and distribution artifacts.
- [ ] Relative links work from the rendered location.
- [ ] Heading anchors resolve under the target renderer.
- [ ] External links resolve and point to authoritative, version-appropriate
  pages.
- [ ] Redirects do not hide obsolete or unrelated targets.
- [ ] Links to `latest` are intentional; versioned reference uses versioned URLs
  when stability matters.
- [ ] Fragments, case sensitivity, URL encoding, and trailing slashes are checked.
- [ ] Orphan pages and dead-end navigation are detected.
- [ ] A network/link checker result is treated as one signal, not proof that the
  linked content supports the claim.

### 10.6 Package and release-artifact validation

- [ ] Build the exact package/archive/container/binary form users receive.
- [ ] List its files and confirm README, license, notices, schemas, examples,
  type metadata, and required linked docs are present.
- [ ] Follow its instructions outside the source checkout.
- [ ] Verify package name, executable, import path, version, and metadata.
- [ ] Test install, first use, upgrade where feasible, uninstall, and cleanup.
- [ ] Verify generated docs identify the same version/revision as the artifact.
- [ ] Check checksums, signatures, attestations, provenance, and SBOM claims
  where published.

### 10.7 Security and privacy validation

- [ ] Scan documentation and history-visible changes for secrets and personal
  data before publishing.
- [ ] Use RFC-reserved example domains and IP addresses where realistic values
  are needed.
- [ ] Ensure commands do not weaken security silently.
- [ ] Verify links for vulnerability reporting and security contacts.
- [ ] Check that default credentials, insecure development flags, or public
  bind addresses are prominently scoped.
- [ ] Redact logs and screenshots.
- [ ] Separate threat-model assumptions from verified controls.

References: [RFC 2606 example
domains](https://www.rfc-editor.org/rfc/rfc2606) and
[RFC 5737 example IPv4
addresses](https://www.rfc-editor.org/rfc/rfc5737).

### 10.8 Metrics, benchmarks, and inventories

- [ ] Every count states what is counted, exclusions, revision, and generation
  method.
- [ ] Dynamic counts are generated from the underlying source or removed.
- [ ] Coverage percentage names tool, configuration, test suite, scope, and
  revision.
- [ ] Benchmark tables name hardware, operating system, runtime/compiler,
  dependencies, workload, warmup, samples, aggregation, variance, and date.
- [ ] Comparisons use equivalent configuration and disclose material tradeoffs.
- [ ] Marketing prose does not generalize beyond measured workloads.
- [ ] Stale-result checks compare against independent source state rather than
  the checked-in result itself.

### 10.9 Rendering and accessibility validation

- [ ] Render Markdown/reStructuredText/AsciiDoc with the actual platform or a
  compatible renderer.
- [ ] Inspect headings, tables, callouts, nested lists, code fences, math,
  footnotes, images, and line wrapping.
- [ ] Validate HTML/CSS where useful, while recognizing that markup validation
  does not prove usability or accessibility.
- [ ] Run the configured accessibility checker and manually inspect keyboard,
  screen-reader structure, contrast, zoom, and text alternatives for important
  pages.
- [ ] Inspect narrow/mobile and high-zoom layouts.

The W3C validator explicitly cautions that validation is not a full quality
check: [W3C Markup Validation
Service](https://validator.w3.org/docs/help.html#validandquality).

### 10.10 Fresh-reader adversarial review

Review the finished set from each applicable role:

- [ ] New user can identify purpose and reach first success.
- [ ] Returning user can find exact reference without rereading the tutorial.
- [ ] Integrator can determine contract, errors, lifecycle, and compatibility.
- [ ] Operator can diagnose, back up, upgrade, roll back, and recover.
- [ ] Contributor can reproduce CI-relevant checks.
- [ ] Maintainer can release and recover from a partial release.
- [ ] Security reviewer can locate trust boundaries and private reporting route.
- [ ] Packager can build from distributed source with complete legal material.
- [ ] Reader can distinguish proved behavior from plans and unsupported claims.

### 10.11 Completion report

A documentation task is complete only when the report includes:

- [ ] Files and surfaces changed.
- [ ] Audiences and project profiles applied.
- [ ] Commands executed and their results.
- [ ] Generated/published artifacts inspected.
- [ ] Claims that remain declared, planned, unknown, or environment-blocked.
- [ ] Skipped checks with reasons.
- [ ] Known documentation debt and risk.
- [ ] No broad statement such as “fully documented,” “all examples work,” or
  “production ready” unless the stated scope and evidence genuinely support it.

## 11. Failure-mode checklist from observed Codex sessions

These checks are distilled from the local `fontdone` and `image-star-slash`
session histories requested for this skill. They are project-agnostic lessons,
not assumptions about every repository.

### 11.1 Premature architecture and audience mismatch

- [ ] Do not begin with an advanced taxonomy before establishing the reader's
  concrete model and first goal.
- [ ] Do not assume domain terms such as channels, modes, codecs, buffers, or
  memory layout are familiar.
- [ ] Test whether a beginner can explain the simplest input-to-output flow
  before adding internals.
- [ ] Layer advanced details so experts can reach them without forcing beginners
  through them.
- [ ] Treat “this is above my head” as evidence that audience sequencing failed,
  not merely that more prose is needed.

### 11.2 Examples written before evidence

- [ ] Inspect the actual API and supported versions before drafting examples.
- [ ] Compile or run examples before describing them as working.
- [ ] Check imports, trait/interface requirements, configuration, output, and
  cleanup.
- [ ] Never use plausible-looking code as a substitute for repository evidence.

### 11.3 Circular and stale validation

- [ ] Never validate a generated count against the same checked-in count.
- [ ] Bind inventories and statistics to a revision and regeneration method.
- [ ] Detect when central docs, source exports, and packaged artifacts diverge.
- [ ] Remove vanity statistics whose maintenance cost exceeds reader value.

### 11.4 Hidden documentation gaps

- [ ] Treat missing-doc lint exceptions and generator exclusions as audit
  findings.
- [ ] Inspect central API pages for meaningful content, not just file existence.
- [ ] Verify public modules are discoverable from top-level navigation.
- [ ] Check whether private-looking but public symbols are intentionally part of
  the contract.

### 11.5 False completion

- [ ] After the normal validation pass, conduct a separate skeptical review
  looking specifically for counterexamples to completion claims.
- [ ] Re-open the packaged archive and published/generated docs after declaring
  the source tree clean.
- [ ] Check runtime, compatibility, and support claims against code and CI.
- [ ] Downgrade the completion statement immediately when material defects are
  found.

### 11.6 Source-tree success but distribution failure

- [ ] Ensure README links work from registry and archive views.
- [ ] Ensure critical contributor, license, security, schema, and usage files
  are shipped when the artifact refers to them.
- [ ] Test examples without workspace-only paths or unpublished packages.
- [ ] Treat packaging configuration as part of documentation correctness.

### 11.7 Weak trust routes

- [ ] A security page names a private reporting channel, supported versions, and
  expected information.
- [ ] A code of conduct names an enforcement/reporting route.
- [ ] Support and security routes are not conflated.
- [ ] Contacts and links are checked from a logged-out external perspective
  where possible.

### 11.8 CI and release mismatch

- [ ] Document commands actually run by CI, including feature matrices and
  generated-file checks.
- [ ] Document release steps actually represented by automation and permissions.
- [ ] Identify manual steps rather than implying full automation.
- [ ] Check that release artifacts contain what the docs promise.

### 11.9 Unsafe remediation and deletion

- [ ] Diagnose with read-only checks before deleting caches, generated output,
  state, or user data.
- [ ] Resolve exact targets; do not use broad paths, unvalidated variables, or
  globs for destructive commands.
- [ ] Prefer preview, backup, trash, or reversible moves.
- [ ] State what will be removed, what will persist, and how to recover.
- [ ] Require explicit user intent for destructive operations beyond the
  documented task.

## 12. Quality rubric

Use this rubric to prioritize work, not as a substitute for the required gates.
Score each applicable dimension from 0 to 3.

| Dimension | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Audience | Unknown | Implied | Named | Task journeys validated |
| First success | Missing | Incomplete | Works with assumptions | Works from clean state |
| Truth | Unsupported | Mostly declared | Material claims checked | Claim ledger and adversarial audit |
| Coverage | Front door only | Major gaps | Core surfaces covered | Public/source/distribution surfaces reconciled |
| Source docs | Missing | Presence-only | Most contracts useful | Complete, rendered, tested, discoverable |
| Examples | None | Plausible only | Core examples executed | Matrix and failure paths validated |
| Navigation | Unstructured | Search-dependent | Predictable | Audience routes and no dead ends |
| Operations | Missing | Happy path | Common failures | Recovery, rollback, observability validated |
| Trust | Missing | Boilerplate | Usable routes | Scope, policy, artifacts, and contacts verified |
| Accessibility | Ignored | Basic prose | Structure and alternatives | Rendered/manual checks at declared target |
| Lifecycle | Snapshot only | Version mentioned | Upgrade/deprecation | Release, support, EOL, migration coherent |
| Distribution | Untested | Source-only | Contents inspected | Install/use/uninstall tested from artifact |

Interpretation:

- Any failed **Required** gate blocks an unqualified completion claim regardless
  of score.
- A score of 3 does not mean perfect; it means the defined checks were supported
  by evidence within the stated scope.
- Not-applicable dimensions need a recorded reason.
- The report should optimize the reader's critical path before raising aggregate
  score.

## 13. Authoritative reference index

Use current, version-appropriate primary sources. The list below is a starting
index, not permission to copy their prose or treat conventions as universal.

### Repository, community, and security

- [GitHub README
  guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [GitHub community
  profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
- [OpenSSF OSPS Baseline
  2026-02-19](https://baseline.openssf.org/versions/2026-02-19)
- [OSI licenses](https://opensource.org/licenses)
- [REUSE specification](https://reuse.software/spec/)
- [Semantic Versioning](https://semver.org/)

### Information architecture and writing

- [Diátaxis](https://diataxis.fr/)
- [Diátaxis quality discussion](https://diataxis.fr/quality/)
- [Google developer-documentation style
  guide](https://developers.google.com/style)
- [Google code-sample
  guidance](https://developers.google.com/style/code-samples)
- [Google API-reference comment
  guidance](https://developers.google.com/style/api-reference-comments)

### Accessibility and safe examples

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI writing tips](https://www.w3.org/WAI/tips/writing/)
- [WAI alt-text decision
  tree](https://www.w3.org/WAI/tutorials/images/decision-tree/)
- [RFC 2606 example domains](https://www.rfc-editor.org/rfc/rfc2606)
- [RFC 5737 example IPv4
  addresses](https://www.rfc-editor.org/rfc/rfc5737)

### Interface specifications

- [OpenAPI latest specification](https://spec.openapis.org/oas/latest.html)
- [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0)
- [GraphQL September 2025](https://spec.graphql.org/September2025/)
- [JSON Schema specification](https://json-schema.org/specification)

### Language documentation

- [Rust rustdoc](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [Go doc comments](https://go.dev/doc/comment)
- [Python PEP 257](https://peps.python.org/pep-0257/)
- [JSDoc](https://jsdoc.app/)
- [TypeDoc](https://typedoc.org/documents/Doc_Comments.html)
- [Java Javadoc comment
  specification](https://docs.oracle.com/en/java/javase/26/docs/specs/javadoc/doc-comment-spec.html)
- [Kotlin KDoc](https://kotlinlang.org/docs/kotlin-doc.html)
- [Doxygen](https://www.doxygen.nl/manual/docblocks.html)
- [C# documentation
  comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-specification/documentation-comments)
- [F# XML
  documentation](https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/xml-documentation)
- [Apple DocC authoring](https://developer.apple.com/documentation/xcode/writing-documentation)
- [Dart documentation
  guidance](https://dart.dev/effective-dart/documentation)
- [Ruby RDoc authoring](https://ruby.github.io/rdoc/index.html)
- [phpDocumentor
  DocBlocks](https://docs.phpdoc.org/guide/guides/docblocks.html)
- [Elixir documentation](https://hexdocs.pm/elixir/writing-documentation.html)
- [Erlang documentation](https://www.erlang.org/doc/system/documentation.html)
- [Scala Scaladoc](https://docs.scala-lang.org/style/scaladoc.html)
- [Clojure Vars and doc metadata](https://clojure.org/reference/vars)
- [Haddock](https://www.haskell.org/haddock/)
- [OCaml odoc](https://ocaml.org/docs/generating-documentation)
- [R Writing
  Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html#Documenting-functions)
- [roxygen2 function
  documentation](https://roxygen2.r-lib.org/articles/rd.html)
- [Julia documentation](https://docs.julialang.org/en/v1/manual/documentation/)
- [Lua manuals](https://lua.org/manual/)
- [PowerShell comment-based
  help](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_comment_based_help)
- [Zig documentation](https://ziglang.org/documentation/master/)
- [Nim DocGen](https://nim-lang.org/docs/docgen.html)
- [Fortran documentation
  practice](https://fortran-lang.org/learn/best_practices/modules_programs/)
- [Solidity NatSpec](https://docs.soliditylang.org/en/latest/natspec-format.html)
