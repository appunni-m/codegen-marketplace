# Crate release readiness

Use this checklist for every crate release. Mark an item **proved**, **not
applicable**, **blocked**, or **not proven**; do not silently omit it.

## Contents

1. Release identity and authorization
2. Manifest and registry metadata
3. Version and compatibility policy
4. MSRV, targets, features, and dependencies
5. Documentation, licensing, and project trust
6. Verification matrix
7. Package archive inspection
8. Clean-consumer verification
9. Evidence record
10. Primary sources

## 1. Release identity and authorization

- Identify the exact workspace, package name, registry, release version, source
  commit, branch, and intended tag.
- Confirm whether the user authorized preparation only, repository commits,
  pushes, tag creation, registry publication, GitHub Release creation, owner
  changes, or yanking. These are distinct mutations.
- Read `AGENTS.md`, contributor/release policy, branch protection, workspace
  metadata, and prior release workflow before proposing a new process.
- Inspect `git status --short`, submodules, generated files, and ignored release
  inputs. Preserve unrelated changes. Release from a clean checkout or clean
  worktree of the reviewed commit.
- Query the exact crate name/version on the target registry. Do not assume an
  upload failed merely because Cargo timed out while polling the index.
- Confirm the intended crate name is owned by the expected account or is still
  available before preparing a first release.

Record a small identity ledger:

| Field | Evidence |
| --- | --- |
| Package | `cargo metadata --no-deps --format-version 1 --locked` |
| Version | selected package metadata and `Cargo.lock` package row |
| Commit | `git rev-parse HEAD` |
| Worktree | empty `git status --short` |
| Registry | explicit registry configuration or crates.io default |
| Tag | repository policy plus exact `v<version>` convention |
| CI | hosted run for the exact commit |

## 2. Manifest and registry metadata

For every publishable package, verify:

- `name`, `version`, `edition`, and `rust-version` are intentional.
- `description` is a concise user-facing purpose, not marketing without a
  testable boundary.
- exactly one of `license` or `license-file` accurately covers shipped code;
  include required license and notice files in the package.
- `repository`, `homepage`, `documentation`, and `readme` resolve and identify
  this package rather than only a monorepo with no package route.
- `keywords` and `categories` are valid and useful.
- `publish` prevents accidental publication or restricts the package to the
  intended registry when needed.
- library/bin/proc-macro/build-script targets and required features are
  intentional; examples and benches needed by users are packaged.
- `[package.metadata.docs.rs]` reflects required features, targets, cfg flags,
  and documentation targets when the default docs.rs build is insufficient.
- `include`/`exclude` rules do not hide license, readme, generated source,
  schemas, fixtures, templates, native libraries, or build-script inputs.
- path dependencies have registry versions and those versions are compatible
  with the dependency order. Cargo removes path overrides from published
  manifests.
- workspace-inherited metadata expands correctly in the normalized packaged
  manifest.

Use `cargo package --list --locked -p <package>` as the source-of-truth file
inventory. Do not infer package contents from Git tracking alone.

## 3. Version and compatibility policy

Inventory every supported public surface:

- Rust public API and trait implementations;
- exported macros, derive output, build-script behavior, and generated code;
- Cargo features, default features, dependency requirements, and re-exports;
- CLI commands, flags, exit codes, stdout/stderr, config and environment;
- wire protocols, schemas, files, persistence, migrations, and ABI/FFI;
- supported Rust toolchains, platforms, architecture, and external tools;
- safety, ordering, concurrency, timing, and performance commitments that users
  reasonably rely on.

Classify changes using the project's policy and Cargo SemVer guidance. In
particular:

- removing, renaming, moving, or feature-gating public items is normally
  breaking;
- adding required trait items, function parameters, or exhaustive enum
  variants can be breaking;
- changing default features, MSRV, platform requirements, unsafe contracts,
  layout, error behavior, CLI output, or serialized forms may be breaking even
  when Rust code still compiles;
- a public dependency or re-export can make dependency upgrades part of the
  crate's compatibility surface;
- for `0.y.z`, Cargo treats changes to the left-most non-zero component as the
  incompatible boundary; document the project's pre-1.0 policy explicitly.

Use a public API diff tool such as `cargo-semver-checks` when repository policy
already provides it or the user authorizes installation. Treat its result as
one signal: it cannot prove runtime, CLI, schema, feature, or platform
compatibility.

Synchronize the selected version in:

- each package manifest and internal dependency requirement;
- `Cargo.lock` workspace package rows;
- changelog/release notes and migration documentation;
- generated client/schema/version constants when authoritative;
- examples, install commands, compatibility tables, downstream pins, and tag
  workflow assertions.

Never hand-edit a lockfile merely to change a version. Use Cargo or the
repository's release tool, then inspect the diff.

## 4. MSRV, targets, features, and dependencies

### MSRV

- Set `package.rust-version` when the project claims an MSRV.
- Run metadata, build/check, tests needed by the contract, and rustdoc with the
  exact MSRV. Pin local and CI toolchains consistently.
- Ensure dependencies resolve to MSRV-compatible releases; a lockfile produced
  by current stable can select a dependency that no longer supports the crate's
  MSRV.
- Treat an MSRV increase as a compatibility change and document it.
- Do not claim MSRV support if only the library compiles while examples,
  binaries, build scripts, proc macros, or advertised features fail.

### Features

At minimum, exercise the applicable rows independently:

| Mode | Typical command |
| --- | --- |
| Default | `cargo test --workspace --all-targets --locked` |
| No default | `cargo test --workspace --all-targets --no-default-features --locked` |
| All features | `cargo test --workspace --all-targets --all-features --locked` |
| Selected combinations | repository matrix or feature powerset tool |
| Docs | `RUSTDOCFLAGS='-D warnings' cargo doc ... --no-deps --locked` |

Do not assume `--all-features` represents a valid simultaneous configuration;
some projects intentionally define mutually exclusive features. Encode and
test those rules explicitly.

### Targets and native dependencies

- Test every claimed tier/platform/architecture or state exactly what CI does
  and does not verify.
- Cross-check `cfg` branches, path separators, signal/process behavior,
  filesystem semantics, endianness, pointer widths, TLS roots, linker/runtime
  libraries, and native package requirements.
- Verify build scripts work from the packaged archive without repository-only
  files, network assumptions, or undeclared tools.
- For FFI/ABI crates, validate headers/bindings, layout, calling convention,
  ownership, unwind behavior, symbol exports, and supported toolchains.

### Dependencies and supply chain

- Inspect direct dependencies and enabled features with `cargo tree` and
  `cargo tree -e features`; remove unused direct dependencies before release.
- Explain large transitive graphs from the actual dependency paths. Avoid
  cosmetic dependency removal that moves the same cost into build scripts or
  downloads.
- Review duplicate versions with `cargo tree -d` and justify material
  compile/runtime cost.
- Run the repository's advisory, license, source, and ban policy (for example
  `cargo deny`) when present. A clean advisory scan is time-bound and is not a
  proof of security.
- Verify source restrictions: unexpected Git/path dependencies, unreviewed
  registries, yanked packages, and license exceptions.
- Keep a committed lockfile for reproducible applications/binaries and release
  automation. Cargo packages include a lockfile by default; do not exclude it
  casually because `cargo install --locked` relies on it.

## 5. Documentation, licensing, and project trust

- Put crate purpose, supported status, install/add command, minimal example,
  feature table, MSRV, platforms, and links in the README or rustdoc front page.
- Document every supported public item and applicable errors, panics, safety
  requirements, lifecycle, side effects, cancellation, concurrency, and
  examples. Run doctests and warnings-denied rustdoc.
- Verify README commands against the package archive, not only the checkout.
- Add a dated, curated changelog entry with upgrade/migration guidance and known
  limitations. Mention security fixes without disclosing an uncoordinated
  vulnerability prematurely.
- Ensure `LICENSE*`, `NOTICE`, third-party attribution, generated/vendored code,
  assets, fixtures, models, and native libraries have compatible terms and are
  included when required.
- Keep contribution, security-reporting, support, and release ownership routes
  accurate. Do not publish a maintainer's personal secret-handling procedure as
  an automated contract.
- Confirm docs.rs can build the package's documentation under the chosen
  features and targets; treat a docs.rs failure as a release defect to fix
  forward.

## 6. Verification matrix

Prefer repository-native gates. A strong default matrix is:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
cargo test --workspace --doc --all-features --locked
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps --locked
cargo package --list --locked -p <package>
cargo package --locked -p <package>
git diff --check
```

Adapt rather than blindly copy:

- run the exact MSRV separately from current stable if both are claimed;
- add default/no-default/selected feature lanes;
- use `cargo check` for targets that cannot execute on the runner, but do not
  call that runtime verification;
- test examples, benches, proc-macro consumers, CLI behavior, migrations,
  protocol compatibility, install/uninstall, and release binaries as relevant;
- bound CI concurrency, compilation jobs, polling loops, and job timeouts so a
  lost runner or process cannot block all later releases indefinitely;
- retain failure logs and the exact target/feature/toolchain evidence.

Never delete, ignore, denominator-reduce, suppress, or loosen a gate simply to
make the release green. Diagnose the first divergence.

## 7. Package archive inspection

Run package verification from the clean release commit:

```bash
cargo package --list --locked -p <package>
cargo package --locked -p <package>
```

Then inspect:

- all and only intended files;
- `.crate` compressed size and registry limits;
- normalized `Cargo.toml` and included `Cargo.lock`;
- license/readme/notice, generated source, templates, schemas, and native files;
- absence of credentials, private test data, local databases, logs, coverage,
  target artifacts, editor state, and oversized unrelated assets;
- a clean extracted build under the MSRV and claimed features.

`cargo publish --dry-run` and `cargo package` perform the upload preparation and
verification without publishing. Use `--no-verify` only when an earlier job
verified the same source archive and the reason is explicit; never combine it
with an unproven or dirty source tree.

## 8. Clean-consumer verification

After publication and registry propagation, test the exact registry artifact:

- use a newly created temporary `CARGO_HOME`, install root, target directory,
  and sample crate;
- specify the exact version and intended registry;
- for a binary, run `--version`, `--help`, one successful workflow, one expected
  error, and platform-specific startup/shutdown behavior;
- for a library, compile and run a minimal downstream example using only public
  APIs and advertised features;
- verify default and no-default behavior where supported;
- verify generated docs and package links;
- compare reported version, tag, checksum, GitHub artifacts, and release notes.

A local path install, Git dependency, or checkout build is not proof that the
registry artifact works.

## 9. Evidence record

Record:

- package/version/registry, commit, annotated tag, and CI run;
- Rust/Cargo versions, MSRV, host/targets, feature matrix, and external tools;
- exact commands with pass/fail/duration and intentionally skipped checks;
- package file count, compressed size, checksum, and inspection result;
- dependency/advisory/license evidence and its date;
- authentication mode without secret values;
- registry visibility, docs.rs, clean consumer, binaries/checksums/attestations;
- unsupported platforms, known limitations, and recovery owner.

Use precise state language: prepared, CI-proven, published, registry-visible,
consumer-verified, and released are not synonyms.

## 10. Primary sources

- [Cargo: Publishing on crates.io](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [Cargo: `cargo package`](https://doc.rust-lang.org/cargo/commands/cargo-package.html)
- [Cargo: `cargo publish`](https://doc.rust-lang.org/cargo/commands/cargo-publish.html)
- [Cargo: SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html)
- [Cargo: Rust version / MSRV](https://doc.rust-lang.org/cargo/reference/rust-version.html)
- [Cargo: Features](https://doc.rust-lang.org/cargo/reference/features.html)
- [Cargo: Registry authentication](https://doc.rust-lang.org/cargo/reference/registry-authentication.html)
- [rustdoc: How to write documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [rustdoc: Documentation tests](https://doc.rust-lang.org/rustdoc/documentation-tests.html)
- [rustdoc: Lints](https://doc.rust-lang.org/rustdoc/lints.html)
