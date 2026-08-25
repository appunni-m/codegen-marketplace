---
name: run-coverage-campaign
description: Run high-throughput, input-driven coverage campaigns in Codex with GPT-5.6 Luna Max as the sole implementation, testing, and validation agent and GPT-5.6 Sol High as a read-only strategist. Use when adding batches of valid test or parity inputs, pruning zero-gain cases, recovering from stalled coverage work, or repeatedly measuring coverage through Coverage MCP without weakening tests or denominators. Do not use for ordinary one-off tests, generic bug fixing, or coverage work without a valid Coverage MCP project context.
---

# Run Coverage Campaign

Increase measured coverage through a bounded state machine. Keep one writer,
route difficult judgment to Sol High, and keep execution noise with Luna Max.

Read [packet-contracts.md](references/packet-contracts.md) before the first
strategist handoff. Apply the `coverage-review` workflow for approval, run,
snapshot, comparison, and response-budget rules throughout. This skill owns
campaign-specific batching and model routing; `coverage-review` owns the shared
managed-evidence workflow.

## Establish the execution boundary

1. Run the main Codex task with `gpt-5.6-luna` and reasoning effort `max`.
   Treat an explicit launch or turn override as the authority. If the active
   model and effort are unknown or different, stop before editing and ask for
   a Luna Max turn; never claim that routing is active when it is not.
2. Keep the main Luna agent as the only writer. Do not delegate edits, test
   generation, pruning, commits, or merges to a subagent.
3. Read every applicable `AGENTS.md` and repository-local skill before work.
   Use one repository and one checkout or worktree per campaign. Preserve
   existing changes and do not let another task write the same checkout.
4. Call `project_context(detailed=false)` first. Confirm that its repository,
   checkout, branch, revision, and Coverage MCP database belong to the current
   Git root. Stop with `BLOCKED_MCP_CONTEXT` on a mismatch or unavailable
   connector; do not silently replace managed evidence with raw commands.
5. Reuse a fresh matching baseline or run the immutable approved baseline
   command. Record the suite and baseline snapshot ID before editing. Register
   a changed command with `human_approved=true` only after the user approves
   its exact command, cwd, shell, artifacts, coverage format, and suite.

## Build a bounded strategy packet

1. Query only the evidence needed for the next campaign:
   `coverage_review(task="insight")` for the bounded ranked targets and
   `coverage_review(task="source")` when exact bounded source evidence is required;
   then inspect one weak file or bounded uncovered range and source context for
   those returned ranges. Include relevant public
   entry points, maintained input generators, neighboring test patterns, and
   exact registered fast and coverage command names. Use `null` for an unknown
   lane; do not ask the strategist to invent one.
2. Prefer reachable public behavior. Do not target generated code, unreachable
   guards, unsupported formats, private hooks, or defensive branches unless
   repository policy supplies a maintained public or approved coverage route.
3. Spawn one read-only strategist with:
   - model `gpt-5.6-sol`
   - reasoning effort `high`
   - no inherited conversation history (`fork_turns="none"`)
   - the bounded `STRATEGY_PACKET` request from the packet contract
4. Require a default batch of 100 candidate inputs grouped into 10 coherent
   families of 10. Each family must identify exact target regions, a public
   reachability argument, deterministic input construction, validation lanes,
   risks, and a stop condition. Permit another size only when the user or an
   applicable repository rule explicitly requires it.
5. Reject a strategy that embeds expected oracle output, guesses private
   reachability or command names, changes thresholds or denominators, or cannot
   map families to exact coverage targets. Ask Sol once to repair a malformed
   packet before classifying the strategy as blocked.

## Implement and validate with Luna

1. Implement the accepted families through maintained declarative generators,
   manifests, fixtures, or repository-native tests. Never hand-edit generated
   expectations, oracle output, hashes, thresholds, or coverage counts.
2. Generate the entire proposed batch before fixing discovered product bugs.
   Run the maintained fast non-coverage or parity lane in family-sized groups
   so failures remain attributable without one process per case.
3. Classify failures across the full batch. Consolidate identical defects into
   one bounded fix pass, retain the revealing input as a regression case, and
   rerun every affected family before measuring coverage.
4. Run the approved coverage command through Coverage MCP with
   `reuse_if_unchanged=true`, one stable `idempotency_key`, and the approved
   family arguments. Reuse the single registered command; do not register a
   command per family. Composite commands additionally register one required
   inventory and one descriptor per declared component/package variant; full
   and incremental runs reuse that same registration. For a fixed-base family
   measurement, pass `execution.mode="incremental"` and
   `baseline.kind="explicit"` with the recorded ordinary or composite baseline
   ID. The terminal run automatically returns `incremental_review`; inspect it
   instead of launching a second comparison run. If the server returns
   `submission_reused=true`, use that terminal run instead of launching
   duplicate work. Require a terminal run, successful artifact ingestion, and
   an explicit current snapshot ID, or `composite_snapshot_id` for a composite
   run. A green test without valid ordinary or composite evidence is not
   coverage evidence.
5. Use standalone `coverage_review(task="incremental")` only when comparing two
   matching ordinary or composite snapshots that already exist outside the run
   that produced them. Report line, branch, function, and region deltas only
   when supplied by the artifacts. For composite evidence, report canonical
   regions, component summaries, inventory completeness, and remediation
   reasons. First measure the full batch; use approved family slices only when
   their explicit arguments and baseline make unique gain attribution
   meaningful.
6. Remove a family only after evidence shows that it contributes no unique
   covered line, branch, function, or region and has no separately documented
   regression value. Do not claim per-case attribution from a batch-level
   snapshot. If attribution cannot be measured safely, retain the cases and
   report the uncertainty instead of guessing.
7. For large named-test inventories, use `find_duplicate_coverage_tests` to
   produce bounded exact-coverage candidate groups. It does not compare logic
   or prove interchangeability; review each candidate before pruning.

## Escalate stalled work to Sol

Escalate after one evidence-backed Luna attempt when implementation is blocked,
the intended region stays red, validation contradicts the reachability claim,
or the same failure survives a bounded fix.

1. Build a `NEEDS_SOL` packet containing exact run and snapshot IDs, changed
   files, bounded log literals, remaining ranges, observed behavior, and ruled-
   out hypotheses. Never send full logs or the accumulated main-thread history.
2. Send the packet to the same Sol High strategist as a follow-up. Sol remains
   read-only and must return a revised strategy, a new target, or an evidence-
   backed unsupported/unreachable classification.
3. Apply and validate the revision with Luna. Allow at most two Sol revision
   cycles for one target. Then stop that target, preserve the evidence, and
   move to another ranked reachable target or report the blocker.

## Finish the campaign

Run the repository's proportionate final gates and return:

- exact repository, checkout, branch, revision, suite, and command names
- baseline and final snapshot IDs plus supplied metric deltas
- proposed, generated, retained, removed, and failing case counts by family
- product bugs found and the bounded fixes or classifications
- Sol escalation count and decisions
- changed files, verification results, remaining targets, and blockers

Never claim a target percentage from changed denominators, stale artifacts,
foreign repositories, missing baselines, or unmeasured coverage.
