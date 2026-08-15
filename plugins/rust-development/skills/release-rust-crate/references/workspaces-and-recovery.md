# Workspaces, first publish, and recovery

Use this reference for Cargo workspaces, a crate's first registry upload,
registry delays, native binaries, ownership changes, failed publication, yanks,
or fix-forward recovery.

## Contents

1. Workspace release graph
2. First crates.io publication
3. Registry propagation and idempotency
4. Post-release consumer checks
5. Native binary releases
6. Ownership and credential hygiene
7. Failure and recovery matrix
8. Primary sources

## 1. Workspace release graph

Do not assume `cargo publish --workspace` alone provides a safe production
sequence. Build a graph of publishable workspace packages:

1. list workspace members with `cargo metadata --no-deps --format-version 1`;
2. exclude `publish = false` and packages restricted away from the target
   registry;
3. identify internal normal/build dependencies and optional dependencies;
4. ensure each publishable path dependency also has a registry version;
5. topologically order packages so dependencies publish before dependents;
6. detect cycles, which cannot be resolved by registry ordering;
7. decide whether all packages share one version/tag or release independently;
8. update internal version requirements so the packaged normalized manifests
   resolve to the versions being published.

For each package in order:

```bash
cargo package --locked -p <package>
cargo publish --locked -p <package>
cargo info '<package>@<version>' --registry crates-io
```

Wait for the dependency version to become visible to the target registry/index
before publishing its dependent. A fixed sleep is not evidence; use a bounded
query loop with clear timeout and retained response. Before every retry, query
the exact version.

Keep release state per package:

| Package | Version | Commit | Package verified | Published | Visible | Consumer verified |
| --- | --- | --- | --- | --- | --- | --- |
| `name` | `x.y.z` | SHA | yes/no | yes/no | yes/no | yes/no |

If a later package fails, never attempt to overwrite already published
dependencies. Fix the remaining source and choose new versions wherever the
public artifact must change.

## 2. First crates.io publication

Trusted Publishing configuration belongs to an existing crate, so bootstrap a
new name manually:

1. Confirm the crate name is available and appropriate. crates.io names are
   first-come, first-served and a published version is permanent.
2. Verify the maintainer's crates.io account and email.
3. Create a narrowly scoped API token that can create/publish the new crate.
   Prefer a short lifetime and minimum allowed scope.
4. Keep the token out of the repository, command history, logs, issue text,
   chat, CI secrets, build artifacts, and shell tracing.
5. If using `cargo login`, understand that the built-in token provider may
   write the token as plain text in the Cargo credentials file. Restrict file
   permissions and use `cargo logout`/revoke when finished. Prefer an operating
   system credential provider where repository policy supports it.
6. Require a clean release commit, green hosted CI on that commit, exact
   manifest/changelog/lockfile agreement, and clean `cargo package --locked`.
7. Publish from a separate clean checkout of that exact commit:

```bash
cargo publish --locked -p <package> --registry crates-io
```

8. Query `<package>@<version>` until it is visible, then perform the clean
   consumer test.
9. Configure the crate's crates.io Trusted Publisher with exact GitHub owner,
   repository, workflow filename, and optional environment.
10. Revoke or delete the bootstrap token. Do not migrate it into GitHub.
11. Create the annotated immutable tag on the exact published commit. A
    tag-driven release workflow should detect the already-published bootstrap
    version and skip duplicate upload while reproducing other release evidence.

Do not use `--allow-dirty` when Cargo reports modified files. Commit the exact
release contents, rerun gates, and publish the clean commit.

## 3. Registry propagation and idempotency

`cargo publish` uploads first and then polls for index visibility. A client-side
timeout can therefore be ambiguous.

Use this retry protocol:

1. Preserve the original stdout/stderr and exit status without exposing tokens.
2. Query the exact package/version with `cargo info` or the registry API.
3. If visible, treat upload as complete and continue consumer verification.
4. If the registry says the exact version is absent, distinguish propagation
   delay from a rejected upload. Retry bounded reads before another upload.
5. If authentication, DNS, rate limiting, or registry health is uncertain,
   stop and diagnose; do not issue repeated publishes blindly.
6. If the exact version already exists unexpectedly, do not proceed until
   ownership and source identity are understood. Versions cannot be replaced.

An idempotent tag workflow may skip uploading an exact already-published
version, but should still verify that the tag/manifest/version are expected and
run non-publish evidence jobs. Do not interpret “already exists” as proof that
the current commit produced it.

## 4. Post-release consumer checks

Create isolated temporary roots; never repurpose the user's normal Cargo home
or delete broad directories. For a binary crate:

```bash
tmp_root=$(mktemp -d)
cargo install <package> --version '=<version>' --locked \
  --root "$tmp_root" --registry crates-io
"$tmp_root/bin/<binary>" --version
```

For a library crate, create a new sample project, add the exact registry
version and intended features, compile/tests with the claimed MSRV and current
stable, and exercise one public success path.

Verify:

- package source is the target registry rather than a path/Git override;
- default and documented feature modes behave as advertised;
- README/rustdoc examples compile;
- docs.rs resolves and builds the intended targets/features;
- CLI help/version, exit codes, config, files, network/listener lifecycle, and
  install/uninstall paths work where applicable;
- checksums, Git tag, release notes, and binaries identify the same version;
- no build requires an undeclared repository file, secret, network fetch,
  native library, or unsupported tool.

Keep the temporary root path narrow and explicit. Remove it only when cleanup
is authorized and safe; otherwise report it.

## 5. Native binary releases

Publishing a binary crate to crates.io still means `cargo install` compiles it.
If fast installation requires prebuilt binaries, design a separate artifact or
installer contract rather than implying Cargo downloads an executable.

For prebuilt artifacts:

- define supported target triples and minimum OS/runtime requirements;
- build in isolated target-specific jobs from the release tag;
- distinguish native execution from cross-compilation;
- smoke test archive extraction, executable permissions, `--version`, help,
  startup/shutdown, dynamic-library dependencies, and one real operation;
- include licenses/notices/readme and deterministic artifact names;
- generate SHA-256 checksums after final archive creation;
- consider signatures, SBOMs, and GitHub artifact attestations;
- verify installer architecture detection, checksum enforcement, atomic
  installation, concurrency lock, stale-lock recovery, cache/version isolation,
  proxy/TLS behavior, and rollback/failure cleanup;
- never run an unverified downloaded binary or use curl-to-shell as the only
  documented path;
- document that crates.io and GitHub artifacts are distinct distribution
  channels with distinct verification.

If a plugin or wrapper bootstraps with `cargo install`, allow enough first-run
time for native dependencies, serialize only installation, release that lock
before normal clients connect, cache by exact version, validate the installed
binary's reported version, and test two concurrent clean-cache launches.

## 6. Ownership and credential hygiene

- Keep at least two trusted human owners or an appropriate team when project
  governance supports it, while minimizing publish authority.
- Review `cargo owner --list` and crates.io team access periodically. Adding an
  owner grants powerful publish/yank/owner-management capability.
- Do not add an owner, team, or trusted publisher without explicit user
  authorization.
- Use Trusted Publishing for automation; do not retain a long-lived
  `CARGO_REGISTRY_TOKEN` in repository or GitHub secrets.
- Pin the authentication action and every other third-party action to full
  commit SHAs.
- Keep local credentials in approved credential providers. Never read or print
  token values during an audit.
- Revoke tokens after bootstrap, suspected exposure, maintainer departure, or
  scope/lifetime misuse.
- Protect the GitHub environment and release workflow because compromising
  either can authorize short-lived registry credentials.

## 7. Failure and recovery matrix

### Cargo reports a dirty worktree

- Inspect `git status --short` and package file list.
- Decide which changes belong to the release; preserve unrelated work.
- Commit the exact release contents and rerun branch/local gates.
- Do not use `cargo publish --allow-dirty`.

### Upload timed out or lost connection

- Preserve logs, redact credentials, and query the exact version.
- If visible, do not retry; run clean consumer verification.
- If absent, check registry status/network/authentication and retry only after
  bounded evidence says the upload was not accepted.

### Version already exists

- A version cannot be overwritten. Verify whether it is the expected release.
- If expected, skip duplicate upload and continue verification.
- If unexpected or wrong, stop, assess ownership/security, and release a new
  corrected version after review. Never retarget the version or tag.

### Trusted Publishing authentication fails

- Compare GitHub owner, repository, workflow filename, environment, event/tag,
  and OIDC claims with the crates.io publisher configuration.
- Confirm `id-token: write` is on the publish job and the job entered the named
  environment.
- Confirm the official auth action is pinned and its token output is passed to
  Cargo only in the publish step.
- Do not fall back to adding a permanent GitHub secret merely to make CI green.

### First release cannot authenticate

- Verify account email, token scope/lifetime, intended registry, Cargo
  credential provider, and crate-name availability.
- Do not paste the token into commands that will be logged or ask another agent
  to locate it.
- Revoke any token whose exposure is uncertain and create a replacement.

### Package verification fails after repository tests pass

- Inspect normalized manifest and archive inventory.
- Add missing packaged inputs or correct include/exclude/path-dependency rules.
- Re-run package extraction/build and affected repository gates.
- Do not publish with `--no-verify` as a workaround.

### docs.rs fails

- Inspect the docs.rs build log and reproduce its target/features/toolchain as
  closely as practical.
- Correct metadata, cfg, native dependency, or documentation warnings and
  release a new version. The uploaded version remains immutable.

### Bad published crate

- Assess severity, affected versions/users, exploitability/data impact, and
  whether yanking reduces new adoption without breaking locked users.
- Publish a corrected version as soon as safely verified.
- Yank only with explicit authorization and a clear reason. A yank prevents
  new resolution but does not delete downloads or remove the version from
  existing lockfiles.
- Publish an advisory/migration note when appropriate; coordinate sensitive
  security disclosure.

### Wrong or moved tag

- Before publication, correct an unpublished local/remote tag only under
  explicit repository policy and authorization.
- After registry upload, GitHub Release, artifact distribution, or public use,
  do not move the tag. Create a new version/tag and explain the correction.

### Token appears in a repository, log, or chat

- Stop using it, revoke it immediately, and rotate affected automation.
- Remove it from current files/log artifacts where the platform permits, but
  assume exposed history/caches were copied.
- Audit registry owners/releases and GitHub workflow/environment changes.
- Do not repeat the token while reporting the incident.

### Native installer lock is stale

- Distinguish a one-time installation lock from a runtime ownership lock.
- Verify owner identity and liveness before recovery; do not delete arbitrary
  lock/database/WAL files.
- Bound wait time, preserve diagnostics, clean only owner-specific temporary
  paths, and atomically publish a fully verified cached version.
- Release the install lock before launching normal runtime clients so it never
  serializes ordinary connections.

## 8. Primary sources

- [Cargo: Publishing on crates.io](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [Cargo: `cargo publish`](https://doc.rust-lang.org/cargo/commands/cargo-publish.html)
- [Cargo: `cargo package`](https://doc.rust-lang.org/cargo/commands/cargo-package.html)
- [Cargo: `cargo yank`](https://doc.rust-lang.org/cargo/commands/cargo-yank.html)
- [Cargo: Registry authentication](https://doc.rust-lang.org/cargo/reference/registry-authentication.html)
- [Cargo: Manifest format](https://doc.rust-lang.org/cargo/reference/manifest.html)
- [crates.io authentication action](https://github.com/rust-lang/crates-io-auth-action)
- [Rust RFC 3691: Trusted Publishing](https://rust-lang.github.io/rfcs/3691-trusted-publishing-cratesio.html)
