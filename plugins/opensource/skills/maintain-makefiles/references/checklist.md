# Makefile Maintenance Checklist

Use only the applicable checks. A Makefile is both executable input and a
timestamp-driven dependency graph; tidy formatting proves neither safety nor
correctness.

## Contents

- 1. Contract and dialect
- 2. Contributor target vocabulary
- 3. Dependency graph
- 4. Recipe semantics and failure
- 5. Variables, recursion, and portability
- 6. Safety and side effects
- 7. Ecosystem adapters
- 8. Multi-architecture and system support
- 9. Behavioral validation
- 10. Authoritative references

## 1. Contract and dialect

- [ ] Record supported implementation and minimum version: GNU Make, BSD make,
  POSIX make, or a tested set.
- [ ] If claiming POSIX portability, use `.POSIX`, the current POSIX grammar,
  portable shell recipes, and tests on each promised implementation.
- [ ] If using GNU features (`.PHONY`, `:=`, `$(shell ...)`, `$(wildcard ...)`,
  order-only prerequisites, grouped targets, `.ONESHELL`, `.SECONDEXPANSION`,
  `eval`, or `call`), state GNU Make and the minimum version required.
- [ ] Preserve existing public targets and their documented behavior. Prefer
  aliases over breaking renames.
- [ ] Make the default goal intentional (`.DEFAULT_GOAL` or a stable first
  target), useful, non-destructive, non-interactive, and non-publishing.
- [ ] Keep Make as an orchestration layer when another tool owns the real build
  graph. Do not reproduce Cargo/npm/Gradle/CMake/Meson logic in Make.
- [ ] Keep help and README commands aligned with actual names, variables,
  prerequisites, artifacts, exit behavior, and side effects.

## 2. Contributor target vocabulary

GNU Coding Standards define conventions for GNU packages, not all open-source
repositories. Modern names below are common interoperability conventions, not
specifications. Select by project need rather than filling a template.

| Target | Contract |
| --- | --- |
| `all` | Stable default aggregate; for GNU packages, build the program. |
| `build` | Build the normal local outputs through the native tool. |
| `test` / `check` | Run the supported test set; alias when both audiences use them. |
| `verify` | Read-only or source-nonmutating aggregate for CI-ready checks. |
| `lint` | Diagnose style/static issues without rewriting source. |
| `format` | Source-mutating formatter; never hide it inside `verify`. |
| `generate` / `update` | Source-mutating regeneration or checked-in updates. |
| `clean` | Remove ordinary build outputs owned by this project. |
| `distclean` | Additionally remove generated configuration; return toward distributed state. |
| `install` | Install under `PREFIX`; support staged install with `DESTDIR` when applicable. |
| `uninstall` | Remove only files installed by the matching install contract. |
| `installcheck` | Test the installed form, not the build-tree form. |
| `dist` | Build a source distribution when the project owns that workflow. |
| `package` | Produce a local artifact; no upload, tag, credential use, or release mutation. |
| `publish` | Explicit external side effect; authenticate and confirm separately. |
| `help` | List supported public targets, important overrides, and side effects. |

- [ ] Do not make `all`, `build`, or a bare `make` run tests, formatting, network
  setup, installation, or publishing unless the established project contract
  clearly requires it.
- [ ] Keep narrow targets composable; make aggregates depend on them rather than
  duplicating recipes.
- [ ] Add compatibility aliases with prerequisite-only rules where possible.
- [ ] Mark action aliases `.PHONY`; ensure a same-named file cannot suppress
  them.

## 3. Dependency graph

- [ ] Every real target names every file or generated state that can change its
  result. Headers, schemas, templates, lockfiles, tool configs, code generators,
  compiler/linker flags, and environment-derived inputs are common omissions.
- [ ] Recipes update `$@`; prerequisites and automatic variables (`$@`, `$<`,
  `$^`, `$+`, `$?`, `$|`, `$*`) match their actual semantics.
- [ ] Do not use automatic variables in prerequisite lists unless GNU
  secondary expansion (`.SECONDEXPANSION`) is enabled, escaped, and tested.
- [ ] Use order-only prerequisites for output directories or setup whose
  existence matters but whose timestamp should not trigger the target.
- [ ] Avoid phony prerequisites of real files: they make the real file rebuild
  every time.
- [ ] Represent multi-output recipes accurately (for supported GNU Make,
  consider grouped targets) so a missing sibling is recreated.
- [ ] Decide whether intermediate files should be deleted, preserved with
  `.SECONDARY`, or treated as ordinary outputs; avoid accidental rebuild loops.
- [ ] Generate dependency files atomically and include them without making a
  first clean build fail.
- [ ] Treat timestamp resolution, future timestamps, restored caches, and
  clock skew as correctness risks; content hashes or forced rebuilds need
  explicit justification.
- [ ] Repair missing prerequisite edges before using `.NOTPARALLEL`; serialization
  can conceal an incorrect graph.

## 4. Recipe semantics and failure

- [ ] Remember each recipe line normally gets a separate shell. Keep `cd`, shell
  variables, traps, and dependent commands on one logical line with failure
  propagation.
- [ ] With `.ONESHELL`, confirm the chosen shell flags and explicit checks catch
  every intermediate failure; Make otherwise sees only the final status.
- [ ] Distinguish Make variables (`$(NAME)`) from shell variables (`$$name`);
  quote paths and values for the receiving parser.
- [ ] Do not silence output or errors so aggressively that the failing command
  and target disappear. Never use `-`, `|| true`, or broad ignores without a
  documented expected failure.
- [ ] Write outputs to a temporary file then rename when interruption can leave
  a corrupt artifact. Use `.DELETE_ON_ERROR` when deleting a failed changed
  target is correct; review `.PRECIOUS` exceptions.
- [ ] Make recipes idempotent where practical, preserve exit status, and fail
  when their promised postcondition is absent.
- [ ] Keep logs understandable under a parallel build; output synchronization
  is presentation, not a dependency fix.

## 5. Variables, recursion, and portability

- [ ] Use `?=` only for genuine defaults and allow documented command-line
  variable overrides. Test at least one non-default path/tool/flag.
- [ ] Do not overwrite user `CFLAGS`, `CPPFLAGS`, `CXXFLAGS`, `LDFLAGS`, or
  ecosystem equivalents with mandatory project flags; combine them explicitly.
- [ ] Use `override` only to append truly mandatory values, with a reason.
- [ ] Use `$(MAKE)`, not literal `make`, for recursive invocations. Verify flags,
  command-line variables, working directory, failure status, and GNU jobserver
  propagation under `-j`.
- [ ] Prefer prerequisite edges between subdirectories over a shell loop; loops
  commonly lose parallelism or ignore a recursive failure.
- [ ] Set or document `SHELL` and shell flags deliberately. Do not assume the
  user's interactive shell or Bash when promising POSIX recipes.
- [ ] Inspect immediate and repeated expansion of `$(shell ...)`, `!=`,
  `$(file ...)`, `$(eval ...)`, recursive variables, wildcards, and includes.
- [ ] Avoid parse-time network access, file mutation, credential reads, or
  environment discovery that makes even help/database queries unsafe.
- [ ] Check generated and included Makefiles, not only the root file.

## 6. Safety and side effects

- [ ] Inspect statically before `make`, `make -n`, or `make -qp`; parsing can
  execute functions, remaking includes can run recipes, and recursive recipe
  lines are exceptions to no-op modes.
- [ ] Separate read-only `verify` from source-mutating `update`, `generate`, and
  `format`.
- [ ] Keep local artifact `package` separate from external side effect
  `publish`; neither publish nor deploy from a default aggregate.
- [ ] For `clean`, resolve and reject empty, `.`, `/`, source-root, home, and
  out-of-repository paths before recursive deletion. Quote operands and use `--`
  where supported.
- [ ] Delete only owned outputs. Keep `clean` idempotent and separate increasingly
  destructive `distclean`/maintainer cleanup.
- [ ] Avoid implicit `sudo`, privilege changes, remote mutation, downloads, and
  interactive prompts in normal build/test targets.
- [ ] Pin or verify downloaded tools when bootstrap is explicitly in scope;
  prefer the repository's existing dependency mechanism.
- [ ] Keep secrets out of command echo, generated files, logs, and target names.

## 7. Ecosystem adapters

- [ ] C/C++: model headers and generated headers (compiler dependency files),
  preserve `CC`/`CXX` and standard flag overrides, and keep compile/link inputs
  separate.
- [ ] Rust: delegate to Cargo; propagate features, profile, target, and locked
  policy without inventing a second crate graph.
- [ ] Go: delegate package selection and caches to `go`; preserve `GOFLAGS`,
  version/CGO/build-tag inputs, and generated-source boundaries.
- [ ] Java/Kotlin/JVM: invoke the checked-in Gradle/Maven wrapper; do not mirror
  its task dependency graph.
- [ ] JavaScript/TypeScript: use the locked package manager and scripts; do not
  silently install or rewrite lockfiles in `build`, `test`, or `verify`.
- [ ] Python: delegate environment, build, and test semantics to declared
  project tools; distinguish editable installs from wheel/sdist verification.
- [ ] .NET: delegate to `dotnet`; propagate configuration/framework/runtime and
  keep restore policy explicit.
- [ ] Ruby/PHP: use Bundler/Composer project commands and lockfiles; avoid global
  dependency mutation.
- [ ] Documentation/data/codegen: separate check from write (`verify-*` versus
  `generate-*`) and model source templates, generator version, and outputs.
- [ ] Containers: keep image build, load, push, scan, and deploy distinct; `push`
  and deploy are external mutations.

## 8. Multi-architecture and system support

Keep Make's platform interface small and translate it into the repository's
native toolchain. A normal application's host system is where its output runs;
for compiler-like tools, the target system can be a distinct system for which
the output itself generates code.

- [ ] Record the **build system** (where compilation runs), **host system**
  (where the built program runs), and, when applicable, **target system** (where
  a compiler-like program's generated code runs). Do not use the three terms
  interchangeably in variable names, help, packages, or reports.
- [ ] Expose overridable canonical inputs such as `TARGET_OS`, `TARGET_ARCH`, and
  optional `TARGET_VARIANT` or target triple. Translate them at one boundary to
  Cargo targets, Go `GOOS`/`GOARCH`, CMake toolchain settings, Docker platform
  values, compiler triples, or the project's existing native vocabulary.
- [ ] Do not infer the target exclusively from `uname`; it observes the build
  system. It may supply a documented native default, but cross-compilation needs
  an explicit target and unsupported or ambiguous values must fail clearly.
- [ ] Normalize architecture aliases deliberately (for example `x86_64` versus
  `amd64`, or `aarch64` versus `arm64`) without assuming differently named
  ecosystems accept the same spelling. Preserve CPU variant, ABI, libc,
  endianness, word size, and instruction-baseline distinctions when relevant.
- [ ] Use a per-target output root for objects, dependency files, generated
  sources, caches, binaries, stamps, and packages. Concurrent targets must not
  overwrite or falsely reuse one another's state.
- [ ] Keep compiler, linker, archiver, sysroot, SDK, `pkg-config`, code generator,
  and toolchain selection target-aware. Build-system utilities must still run
  on the build system; do not accidentally replace them with target binaries.
- [ ] Do not run a target binary during a cross build unless a compatible native
  environment, emulator, or explicit runner is configured. Keep build, artifact
  inspection, and target execution as separable verification stages.
- [ ] Test Linux, macOS, and Windows contracts actually promised by the project,
  including executable/library suffixes, path and shell behavior, filesystem
  case rules, archive formats, SDK/linker selection, and native-tool differences.
- [ ] Make package names include the operating system and architecture, plus ABI
  or variant when it affects compatibility. Ensure matrix jobs cannot publish or
  overwrite the same path or artifact name.
- [ ] Verify at least one native build, one representative cross build, and
  artifact inspection of OS/architecture/format metadata. Run behavior tests
  natively or through the declared runner, and report unexecuted combinations
  as build-only evidence rather than proven support.

## 9. Behavioral validation

Use a disposable checkout or fixture when cleanup/failure tests could damage
work. Record exact Make implementation, version, environment, and goals.

- [ ] **Default goal:** a fresh checkout plus required bootstrap reaches the
  documented result without surprising mutation.
- [ ] **No-op rebuild:** a second invocation runs no recipe for current real
  outputs; explain intentionally phony work.
- [ ] **Selective rebuild:** touch one representative source, header/schema,
  config, and generated input; rebuild exactly the affected closure.
- [ ] **Parallel build:** run a bounded `-j` from clean state repeatedly; compare
  outputs and status with serial execution. Do not accept `.NOTPARALLEL` as a
  substitute for graph correctness.
- [ ] **Failure cleanup:** inject or reproduce a mid-recipe failure; no partial
  target is accepted as current and retry succeeds.
- [ ] **Clean safety:** run twice in a disposable tree with normal and adversarial
  path overrides; sources, VCS metadata, external paths, and config survive.
- [ ] **Variable override:** change output directory, tool, and representative
  flags on the command line; values reach sub-makes and recipes.
- [ ] **Staged install:** run `make DESTDIR=<temporary-absolute-path> install`;
  inspect the staged tree, permissions, and absence of writes to the real
  `PREFIX`. Test uninstall/installcheck only where promised.
- [ ] **Alias parity:** old and new aliases delegate to the same native command,
  artifacts, exit status, and supported argument surface.
- [ ] **Help truth:** every advertised target exists; internal/dangerous targets
  are labeled or omitted and examples preserve `$` and quoting.
- [ ] **Portability:** parse and execute representative targets on every promised
  Make and shell implementation; lint alone is insufficient.
- [ ] **Platform matrix:** override each supported platform tuple, confirm
  per-target output isolation and package identity, inspect artifact metadata,
  and distinguish native execution, runner-backed execution, and build-only
  cross-compilation evidence.

## 10. Authoritative references

- GNU Make manual: <https://www.gnu.org/software/make/manual/make.html>
- GNU Make `-n` exceptions:
  <https://www.gnu.org/software/make/manual/html_node/Instead-of-Execution.html>
- GNU Coding Standards, Makefile conventions:
  <https://www.gnu.org/prep/standards/html_node/Makefile-Conventions.html>
- GNU standard targets:
  <https://www.gnu.org/prep/standards/html_node/Standard-Targets.html>
- GNU staged installs:
  <https://www.gnu.org/prep/standards/html_node/DESTDIR.html>
- POSIX.1-2024 `make`:
  <https://pubs.opengroup.org/onlinepubs/9799919799.2024edition/utilities/make.html>
- Autoconf portable Make guidance:
  <https://www.gnu.org/software/autoconf/manual/autoconf-2.71/html_node/Portable-Make.html>
- Autoconf build, host, and target system types:
  <https://www.gnu.org/software/autoconf/manual/autoconf-2.72/html_node/System-Types.html>
- Cargo target, linker, and runner configuration:
  <https://doc.rust-lang.org/cargo/reference/config.html>
- Go target and host operating-system/architecture pairs:
  <https://go.dev/doc/install/source>
- CMake cross-compiling toolchains:
  <https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html#cross-compiling>
- Docker build and target platform arguments:
  <https://docs.docker.com/build/building/variables/#multi-platform-build-arguments>
- Current target-interface examples:
  <https://github.com/kubernetes/kubernetes/blob/master/build/root/Makefile>,
  <https://github.com/prometheus/prometheus/blob/main/Makefile.common>,
  <https://github.com/moby/moby/blob/master/Makefile>
