#!/usr/bin/env python3
"""Statically audit active migration parity inputs without executing either system."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

FORBIDDEN_KEYS = {
    "actual",
    "baseline",
    "encoded_ref_bytes",
    "encoded_ref_path",
    "error",
    "expect_error",
    "expectation",
    "expected",
    "golden",
    "hash",
    "oracle",
    "output",
    "outputs",
    "pixels",
    "pixels_hex",
    "raw_path",
    "ref_bytes",
    "ref_path",
    "sha256",
    "status",
}
DOCUMENT_KEYS = {"version", "surface", "operation", "cases"}
CASE_KEYS = {"case_id", "operation", "inputs"}
INPUT_KEYS = {"assets", "params", "environment"}
REQUIRED_INPUT_KEYS = {"assets", "params"}
ASSET_KINDS = {
    "ref",
    "inline_bytes",
    "generated_input",
    "builtin",
    "missing_ref",
    "remote_mock",
}
CASE_ID_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_-]*"
    r"\.[A-Za-z][A-Za-z0-9_-]*"
    r"\.[A-Za-z][A-Za-z0-9_-]*"
    r"(?:\.[A-Za-z0-9_-]+)*$"
)
DATE_RE = re.compile(r"(?:19|20)\d{2}-[01]\d-[0-3]\d")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
EPOCH_RE = re.compile(r"(?:^|[._-])1[6-9]\d{8,}(?:$|[._-])")


def finding(
    severity: str,
    code: str,
    path: str,
    location: str,
    message: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "path": path,
        "location": location,
        "message": message,
    }


def location_child(location: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{location}[{key}]"
    return f"{location}.{key}" if location != "$" else f"$.{key}"


def find_forbidden_keys(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = location_child(location, str(key))
            if str(key).lower() in FORBIDDEN_KEYS:
                findings.append(
                    finding(
                        "error",
                        "forbidden_expected_key",
                        relative,
                        child_location,
                        f"Active input contains forbidden expected-behavior key '{key}'.",
                    )
                )
            find_forbidden_keys(child, relative, child_location, findings)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            find_forbidden_keys(
                child,
                relative,
                location_child(location, index),
                findings,
            )


def safe_asset_path(value: str) -> bool:
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    return bool(
        value
        and not posix.is_absolute()
        and not windows.is_absolute()
        and not windows.drive
        and ".." not in posix.parts
        and "\\" not in value
    )


def inspect_assets(
    value: Any,
    relative: str,
    location: str,
    assets_root: Path,
    findings: list[dict[str, str]],
) -> None:
    if isinstance(value, list):
        for index, child in enumerate(value):
            inspect_assets(
                child,
                relative,
                location_child(location, index),
                assets_root,
                findings,
            )
        return
    if not isinstance(value, dict):
        findings.append(
            finding(
                "error",
                "invalid_asset_descriptor",
                relative,
                location,
                "Asset entries must be named objects or descriptor objects.",
            )
        )
        return

    if "kind" not in value:
        for key, child in value.items():
            inspect_assets(
                child,
                relative,
                location_child(location, str(key)),
                assets_root,
                findings,
            )
        return

    kind = value.get("kind")
    if kind not in ASSET_KINDS:
        findings.append(
            finding(
                "error",
                "invalid_asset_kind",
                relative,
                location_child(location, "kind"),
                f"Unknown asset kind: {kind!r}.",
            )
        )

    path_value = value.get("path")
    if path_value is None:
        if kind in {"ref", "missing_ref", "generated_input", "remote_mock"}:
            findings.append(
                finding(
                    "error",
                    "missing_asset_path",
                    relative,
                    location,
                    f"Asset kind {kind!r} requires a relative path.",
                )
            )
        return
    if not isinstance(path_value, str) or not safe_asset_path(path_value):
        findings.append(
            finding(
                "error",
                "unsafe_asset_path",
                relative,
                location_child(location, "path"),
                "Asset path must be relative and remain beneath the fixture asset root.",
            )
        )
        return
    if kind == "ref" and not (assets_root / PurePosixPath(path_value)).is_file():
        findings.append(
            finding(
                "error",
                "missing_asset",
                relative,
                location_child(location, "path"),
                f"Tracked fixture asset does not exist: {path_value}.",
            )
        )


def inspect_input_file(
    root: Path,
    path: Path,
    assets_root: Path,
    seen_case_ids: dict[str, str],
) -> tuple[list[str], list[dict[str, str]]]:
    relative = path.relative_to(root).as_posix()
    findings: list[dict[str, str]] = []
    case_ids: list[str] = []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return case_ids, [
            finding("error", "invalid_json", relative, "$", str(error))
        ]

    find_forbidden_keys(payload, relative, "$", findings)
    if not isinstance(payload, dict):
        return case_ids, findings + [
            finding(
                "error",
                "invalid_document_shape",
                relative,
                "$",
                "Input document must be a JSON object.",
            )
        ]

    actual_document_keys = set(payload)
    if actual_document_keys != DOCUMENT_KEYS:
        findings.append(
            finding(
                "error",
                "invalid_document_keys",
                relative,
                "$",
                "Document keys must be exactly version, surface, operation, and cases.",
            )
        )
    if payload.get("version") != 1:
        findings.append(
            finding(
                "error",
                "unsupported_document_version",
                relative,
                "$.version",
                "Active input document version must be 1.",
            )
        )

    surface = payload.get("surface")
    operation = payload.get("operation")
    cases = payload.get("cases")
    if not isinstance(surface, str) or not surface:
        findings.append(
            finding(
                "error",
                "invalid_surface",
                relative,
                "$.surface",
                "Surface must be a non-empty string.",
            )
        )
    if not isinstance(operation, str) or not operation:
        findings.append(
            finding(
                "error",
                "invalid_operation",
                relative,
                "$.operation",
                "Operation must be a non-empty string.",
            )
        )
    if not isinstance(cases, list):
        findings.append(
            finding(
                "error",
                "invalid_cases",
                relative,
                "$.cases",
                "Cases must be an array.",
            )
        )
        return case_ids, findings

    for index, case in enumerate(cases):
        case_location = f"$.cases[{index}]"
        if not isinstance(case, dict):
            findings.append(
                finding(
                    "error",
                    "invalid_case_shape",
                    relative,
                    case_location,
                    "Case must be an object.",
                )
            )
            continue
        if set(case) != CASE_KEYS:
            findings.append(
                finding(
                    "error",
                    "invalid_case_keys",
                    relative,
                    case_location,
                    "Case keys must be exactly case_id, operation, and inputs.",
                )
            )

        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
            findings.append(
                finding(
                    "error",
                    "invalid_case_id",
                    relative,
                    location_child(case_location, "case_id"),
                    "Case ID must be deterministic Surface.operation.path notation.",
                )
            )
        if isinstance(case_id, str) and case_id:
            case_ids.append(case_id)
            if DATE_RE.search(case_id) or UUID_RE.search(case_id) or EPOCH_RE.search(case_id):
                findings.append(
                    finding(
                        "error",
                        "nondeterministic_case_id",
                        relative,
                        location_child(case_location, "case_id"),
                        "Case ID resembles a date, timestamp, or random UUID.",
                    )
                )
            previous = seen_case_ids.get(case_id)
            if previous is not None:
                findings.append(
                    finding(
                        "error",
                        "duplicate_case_id",
                        relative,
                        location_child(case_location, "case_id"),
                        f"Case ID already appears in {previous}.",
                    )
                )
            else:
                seen_case_ids[case_id] = relative

            if (
                isinstance(surface, str)
                and isinstance(operation, str)
                and not case_id.startswith(f"{surface}.{operation}.")
            ):
                findings.append(
                    finding(
                        "error",
                        "case_id_contract_mismatch",
                        relative,
                        location_child(case_location, "case_id"),
                        "Case ID prefix must match document surface and operation.",
                    )
                )

        if case.get("operation") != operation:
            findings.append(
                finding(
                    "error",
                    "case_operation_mismatch",
                    relative,
                    location_child(case_location, "operation"),
                    "Case operation must match its input document operation.",
                )
            )

        inputs = case.get("inputs")
        if not isinstance(inputs, dict):
            findings.append(
                finding(
                    "error",
                    "invalid_inputs_shape",
                    relative,
                    location_child(case_location, "inputs"),
                    "Inputs must be an object.",
                )
            )
            continue
        input_keys = set(inputs)
        if (
            not REQUIRED_INPUT_KEYS.issubset(input_keys)
            or not input_keys.issubset(INPUT_KEYS)
        ):
            findings.append(
                finding(
                    "error",
                    "invalid_inputs_keys",
                    relative,
                    location_child(case_location, "inputs"),
                    "Inputs require assets and params; only environment is optional.",
                )
            )
        for name in ("assets", "params", "environment"):
            if name in inputs and not isinstance(inputs[name], dict):
                findings.append(
                    finding(
                        "error",
                        f"invalid_{name}_shape",
                        relative,
                        location_child(
                            location_child(case_location, "inputs"),
                            name,
                        ),
                        f"{name} must be an object.",
                    )
                )
        if isinstance(inputs.get("assets"), dict):
            inspect_assets(
                inputs["assets"],
                relative,
                f"{case_location}.inputs.assets",
                assets_root,
                findings,
            )

    return case_ids, findings


def build_report(root: Path) -> dict[str, Any]:
    fixtures_root = root / "tests" / "fixtures"
    manifest = fixtures_root / "manifest.yaml"
    manifests = sorted(fixtures_root.rglob("manifest.yaml")) if fixtures_root.exists() else []
    inputs_root = fixtures_root / "inputs"
    assets_root = fixtures_root / "assets"
    input_files = sorted(inputs_root.rglob("*.json")) if inputs_root.exists() else []
    asset_files = sorted(path for path in assets_root.rglob("*") if path.is_file()) if assets_root.exists() else []
    findings: list[dict[str, str]] = []

    if not manifest.is_file():
        findings.append(
            finding(
                "error",
                "missing_manifest",
                "tests/fixtures/manifest.yaml",
                "$",
                "Canonical active migration manifest is missing.",
            )
        )
    if len(manifests) > 1:
        findings.append(
            finding(
                "error",
                "multiple_active_manifests",
                "tests/fixtures",
                "$",
                "More than one manifest.yaml exists beneath the active fixture root.",
            )
        )
    if not input_files:
        findings.append(
            finding(
                "review",
                "no_input_files",
                "tests/fixtures/inputs",
                "$",
                "No active input JSON files were discovered.",
            )
        )

    seen_case_ids: dict[str, str] = {}
    case_ids: list[str] = []
    for path in input_files:
        file_case_ids, file_findings = inspect_input_file(
            root,
            path,
            assets_root,
            seen_case_ids,
        )
        case_ids.extend(file_case_ids)
        findings.extend(file_findings)

    findings.sort(
        key=lambda item: (
            {"error": 0, "review": 1, "info": 2}[item["severity"]],
            item["path"],
            item["location"],
            item["code"],
        )
    )
    counts = Counter(item["severity"] for item in findings)
    return {
        "schema_version": 1,
        "root": str(root),
        "summary": {
            "errors": counts["error"],
            "review": counts["review"],
            "info": counts["info"],
        },
        "inventory": {
            "manifest": (
                manifest.relative_to(root).as_posix() if manifest.is_file() else None
            ),
            "input_files": [
                path.relative_to(root).as_posix() for path in input_files
            ],
            "asset_files": [
                path.relative_to(root).as_posix() for path in asset_files
            ],
            "case_count": len(case_ids),
            "case_ids": sorted(case_ids),
        },
        "findings": findings,
        "limits": [
            "This static audit does not parse manifest semantics.",
            "This static audit does not execute the source oracle or target.",
            "This static audit does not prove live parity or coverage.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    inventory = report["inventory"]
    print("Migration parity fixture audit")
    print(f"Manifest: {inventory['manifest'] or 'missing'}")
    print(f"Input files: {len(inventory['input_files'])}")
    print(f"Cases: {inventory['case_count']}")
    print(
        "Findings: "
        f"{summary['errors']} error(s), "
        f"{summary['review']} review item(s)"
    )
    for item in report["findings"]:
        print(
            f"- {item['severity'].upper()} {item['code']} "
            f"{item['path']} {item['location']} — {item['message']}"
        )
    print("Static validation does not prove live parity or coverage.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit active migration fixtures without executing either system."
    )
    parser.add_argument("repository", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return 1 when error-severity findings exist.",
    )
    args = parser.parse_args()

    root = args.repository.resolve()
    if not root.is_dir():
        print("error: repository is not a directory", file=sys.stderr)
        return 2
    report = build_report(root)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
