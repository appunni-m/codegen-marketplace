# Coverage MCP contract pointer

Status: the schema-9 seven-tool contract is implemented in the canonical
server. The canonical server's [README and repository](https://github.com/appunni-m/coverage-mcp)
are the stable public entry point.

The marketplace owns distribution and workflow guidance. The canonical Rust
server owns MCP semantics, validation, freshness, provenance, storage, and
response budgets.

## Public contract

The active MCP inventory contains exactly:

- `project_context`
- `register_test_command`
- `run_test`
- `run_review`
- `cancel_run`
- `coverage_import`
- `coverage_review`

The contract is schema revision 9. The exact tool-array digest is pinned in
`plugins/testing/compatibility.json` and checked against the live server by
the existing `pnpm check:coverage-mcp` command.

## Workflow boundary

The [`coverage-review` skill](../plugins/testing/skills/coverage-review/SKILL.md)
owns approval, polling, freshness, lineage, response-budget, and reporting
policy. The server owns wire-level validation and evidence rules, including
`max_bytes`, `source_resolution`, and identical HTTP/stdio behavior. The
server's `initialize` instructions and `tools/list` descriptions remain
sufficient for a client that does not load the marketplace skill.

Use `coverage_import` only for an external or historical repository-relative
report. Use `coverage_review` for bounded change, history, insight, source,
audit, or combined analysis.

## Verification

```sh
pnpm check
pnpm check:coverage-mcp
```

Plugin files and runtime configuration contain only the schema-9 contract.
