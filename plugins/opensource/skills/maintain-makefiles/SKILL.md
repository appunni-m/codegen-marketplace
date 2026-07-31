---
name: maintain-makefiles
description: Improve and audit Makefile command interfaces, standardize contributor commands, and repair build-graph behavior without replacing project-native tooling. Use when Codex needs to create or maintain a Makefile, add compatible target aliases, diagnose stale or excessive rebuilds, make recipes safe and parallel-correct, preserve GNU or POSIX portability claims, support multi-architecture or cross-compilation workflows, or verify clean, install, package, and recursive Make behavior.
---

# Maintain Makefiles

Use Make as a thin, predictable contributor interface and an accurate
incremental dependency graph. Preserve local conventions unless changing them
has a demonstrated interoperability or correctness benefit.

## Boundaries

This skill owns the Makefile and its contributor-facing command surface; it is
not a general application-code, CI, packaging, or build-system redesign.

- Inspect delegated scripts and native tool manifests only to determine the
  Make contract and verify its commands.
- Report out-of-scope blockers separately and minimally. Do not review or
  redesign unrelated code.
- Do not replace a repository's native build tool. Make should normally
  delegate to Cargo, Go, npm/pnpm, Gradle, CMake, Meson, or equivalent.
- Preserve working project-native targets and CI entry points; add aliases
  before considering a rename or removal.

## Workflow

### 1. Protect and inspect

1. Read repository instructions and worktree state; preserve user changes.
2. Inspect Makefiles as executable input before invoking Make. Check includes,
   immediate assignments, `$(shell ...)`, `!=`, `$(file ...)`, `$(eval ...)`,
   recursive calls, destructive recipes, downloads, privilege changes, and
   environment-sensitive defaults.
3. Run the deterministic preflight:

```bash
python3 <skill-root>/scripts/audit_makefile.py <repository>
```

Use `--format json` for machine evidence and `--strict` to fail on high-risk
findings. The output is static evidence; it does not prove semantic correctness.

`make -n` is not a safety boundary: recursive lines and recipes that remake
included makefiles can still run, while parse-time side effects happen during
expansion. Run `make -qp` only after static inspection; it is parse-capable.
Do not execute destructive, networked, privileged, interactive, or publishing
targets without the required authority.

### 2. Establish the contract

1. Identify the supported Make implementation and version. Choose GNU Make
   deliberately, or enforce a real POSIX-portable subset; never imply both.
2. Inventory current targets, callers in docs and CI, variables, outputs,
   prerequisites, generated files, and delegated tools.
3. For multi-system work, record the build, host, and target systems explicitly,
   including operating system, architecture, ABI or variant, toolchain, runner,
   and whether each supported combination is native or cross-compiled.
4. Choose only applicable aliases from the checklist. GNU Coding Standards
   targets are conventions for GNU-compatible packages, not universal
requirements. Common modern aliases are interoperability conventions, not
specifications. Treat modern aliases as conventions, not specifications.
5. Keep `verify` non-mutating and separate source-mutating `format`, `generate`,
   and `update`. Keep `package` local; make `publish` explicit and non-default.
6. Make the default goal unsurprising and give `help` one-line target purposes,
   important overrides, prerequisites, side effects, and examples.

### 3. Repair semantics, then presentation

- Model generated outputs as real targets with complete prerequisites. Avoid
  stamp files unless they represent the exact completed state.
- Mark action targets `.PHONY`, but never phony real outputs or included
  makefiles.
- Use order-only prerequisites for required directories or setup state whose
  timestamp must not force rebuilds.
- Use `$(MAKE)` for recursion so flags, command-line variables, and GNU
  jobserver behavior propagate.
- Remember that recipe lines use separate shells unless `.ONESHELL` applies;
  join dependent commands safely. Under `.ONESHELL`, ensure an intermediate
  failure cannot be hidden.
- Keep Make expansion distinct from shell expansion, including doubled `$$`.
- Preserve user command-line variable overrides; append mandatory flags
  separately and use `override` only with a stated reason.
- Never treat build-machine discovery as the requested target. Canonicalize
  platform inputs once, translate them to the native tool's vocabulary, and
  reject unsupported combinations instead of silently falling back.
- Use separate output roots for each target tuple so objects, caches, generated
  state, packages, and concurrent native and cross builds cannot collide.
- Build and inspect a cross-compiled target without executing it unless an
  explicit compatible runner, emulator, or native test environment is declared.
- Prefer atomic output creation and consider `.DELETE_ON_ERROR` where partial
  targets would otherwise appear current.
- Guard cleanup paths against empty, root, source, and out-of-repository values.

Read [the compact checklist](references/checklist.md) for the target contract,
semantic traps, ecosystem adapters, and exact validation matrix.

### 4. Verify behavior

After static inspection, select the smallest safe commands that prove:

1. the default goal and each changed alias work from a fresh checkout;
2. a second invocation is a no-op rebuild for real outputs;
3. touch one representative input and confirm a selective rebuild of every
   affected output and nothing unrelated;
4. a bounded parallel build produces the same result without hidden races;
5. a failed recipe leaves no corrupt output that a retry accepts as current;
6. clean is idempotent, bounded, and preserves source and configuration;
7. documented variable overrides propagate, including through recursion;
8. install stages into a temporary root when the project supports installation;
9. each promised platform has a native build or cross build, artifact inspection,
   isolated outputs, package identity, and execution tests only on a declared
   compatible runner.

Use temporary copies or fixtures for destructive tests. Run repository-native
tests under its managed test policy; do not bypass an approved test ledger.

## Completion report

Report the target contract preserved or added, dialect and minimum version,
files changed, static findings, commands and fixtures used, no-op/selective/
parallel/failure/clean/install results, skipped checks with reasons, and
remaining Makefile risks. Do not claim portability, reproducibility, or
parallel safety beyond the environments and cases actually verified.
