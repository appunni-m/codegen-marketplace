#!/usr/bin/env python3
"""Validate migration-parity/manifest@2 and its indexed input specifications."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

MANIFEST_SCHEMA = "migration-parity/manifest@2"
LANES = ("parity", "coverage", "benchmark")
INPUT_SCHEMAS = {
    "parity": "migration-parity/parity-input@1",
    "coverage": "migration-parity/coverage-input@1",
    "benchmark": "migration-parity/benchmark-input@1",
}
RESULT_SCHEMAS = {
    "parity": "migration-parity/parity-result@1",
    "coverage": "migration-parity/coverage-result@1",
    "benchmark": "migration-parity/benchmark-result@1",
}
AGGREGATE_SCHEMA = "migration-parity/status-report@1"

SURFACE_KINDS = {"namespace", "type", "format", "abi", "cli", "protocol", "service"}
OPERATION_KINDS = {
    "function",
    "method",
    "constructor",
    "property_get",
    "property_set",
    "command",
    "abi_function",
    "protocol_operation",
    "format_operation",
    "constant",
    "type",
    "enum",
    "enum_variant",
    "flag",
    "macro",
    "record",
    "tag",
    "error",
    "namespace",
}
CLASSIFICATIONS = {"endpoint", "non_endpoint"}
SUPPORT_STATUSES = {
    "supported",
    "partial",
    "unimplemented",
    "intentionally_unsupported",
    "out_of_scope",
    "not_applicable",
}
PARAMETER_STYLES = {
    "receiver",
    "positional",
    "positional_or_keyword",
    "keyword",
    "variadic_positional",
    "variadic_keyword",
    "input_asset",
    "stdin",
    "environment",
    "option",
}
VALUE_TYPES = {
    "null",
    "boolean",
    "integer",
    "number",
    "string",
    "bytes",
    "path",
    "enum",
    "sequence",
    "mapping",
    "record",
    "image",
    "font",
    "stream",
    "handle",
    "any_json",
}
RESULT_SHAPES = {
    "none",
    "scalar",
    "sequence",
    "mapping",
    "record",
    "bytes",
    "image",
    "mask",
    "encoded_file",
    "metrics",
    "handle",
    "iterator",
    "stream",
    "cli",
    "protocol",
    "filesystem",
}
OBSERVATION_COMPARISONS = {
    "exact",
    "ordered",
    "unordered",
    "numeric",
    "text",
    "bytes",
    "image",
    "filesystem",
}
TEXT_TRANSFORMS = {
    "normalize_newlines",
    "normalize_path_separators",
    "strip_runtime_addresses",
    "unicode_nfc",
}
ERROR_FIELDS = {"class", "kind", "message", "stage", "code"}
REQUIREMENT_DIMENSIONS = {
    "parameter",
    "parameter_combination",
    "input_family",
    "success_path",
    "error_path",
    "mode",
    "format",
    "protocol_variant",
    "abi_variant",
    "asset_family",
    "boundary",
    "backend",
    "runtime",
    "feature",
    "historical_divergence",
    "code_path",
    "performance",
    "documentation",
}
COVERAGE_DIMENSIONS = {"function", "line", "branch", "region"}
BENCHMARK_METRICS = {
    "latency",
    "throughput",
    "allocations",
    "peak_memory",
    "resident_memory",
    "artifact_size",
    "encoded_size",
    "startup_time",
    "cpu_time",
}
BUDGET_KINDS = {"absolute", "relative"}
BUDGET_STATISTICS = {
    "min",
    "median",
    "mean",
    "p95",
    "p99",
    "max",
    "total",
    "weighted_mean",
}
BUDGET_OPERATORS = {"less_than_or_equal", "greater_than_or_equal"}
MEASUREMENT_BOUNDARIES = {
    "observed_steps",
    "whole_workflow",
    "process",
    "artifact",
}
CACHE_STATES = {"cold", "warm", "mixed"}
CORRECTNESS_GATES = {
    "parity_pass",
    "source_target_match",
    "successful_execution",
    "not_applicable",
}
ASSET_KINDS = {"ref", "inline", "generated", "builtin", "missing", "remote_mock"}

PUBLIC_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")
LOCAL_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"(?:19|20)\d{2}-[01]\d-[0-3]\d")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
EPOCH_RE = re.compile(r"(?:^|[._:-])1[6-9]\d{8,}(?:$|[._:-])")


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


def child(location: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{location}[{key}]"
    return f"{location}.{key}" if location != "$" else f"$.{key}"


def add(
    findings: list[dict[str, str]],
    code: str,
    relative: str,
    location: str,
    message: str,
    severity: str = "error",
) -> None:
    findings.append(finding(severity, code, relative, location, message))


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def unique_string_list(value: Any, *, non_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not non_empty)
        and all(non_empty_string(item) for item in value)
        and len(value) == len(set(value))
    )


def exact_object(
    value: Any,
    required: set[str],
    optional: set[str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        add(findings, "invalid_object", relative, location, "Expected an object.")
        return None
    for field in sorted(required - set(value)):
        add(
            findings,
            "missing_required_field",
            relative,
            child(location, field),
            f"Required field {field!r} is missing.",
        )
    for field in sorted(set(value) - required - optional):
        add(
            findings,
            "unknown_schema_field",
            relative,
            child(location, field),
            f"Field {field!r} is not defined by this fixed schema.",
        )
    return value


def validate_id(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
    *,
    public: bool = False,
) -> str | None:
    pattern = PUBLIC_ID_RE if public else LOCAL_ID_RE
    if not non_empty_string(value) or pattern.fullmatch(value) is None:
        add(
            findings,
            "invalid_identifier",
            relative,
            location,
            "Identifier contains unsupported characters or is empty.",
        )
        return None
    return value


def validate_stable_id(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> str | None:
    item_id = validate_id(value, relative, location, findings)
    if item_id is None:
        return None
    if DATE_RE.search(item_id) or UUID_RE.search(item_id) or EPOCH_RE.search(item_id):
        add(
            findings,
            "nondeterministic_identifier",
            relative,
            location,
            "Identifier resembles a timestamp, date, or UUID.",
        )
    return item_id


def safe_relative_path(value: Any, *, allow_dot: bool = False) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if allow_dot and value == ".":
        return True
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    return (
        not posix.is_absolute()
        and not windows.is_absolute()
        and not windows.drive
        and ".." not in posix.parts
        and "\\" not in value
        and value != "."
    )


def validate_relative_path(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
    *,
    allow_dot: bool = False,
) -> str | None:
    if not safe_relative_path(value, allow_dot=allow_dot):
        add(
            findings,
            "unsafe_relative_path",
            relative,
            location,
            "Path must be repository-relative and cannot traverse.",
        )
        return None
    return value


def register(
    registry: dict[str, Any],
    item_id: str | None,
    value: Any,
    kind: str,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    if item_id is None:
        return
    if item_id in registry:
        add(
            findings,
            f"duplicate_{kind}_id",
            relative,
            location,
            f"Duplicate {kind} ID {item_id!r}.",
        )
    else:
        registry[item_id] = value


def load_document(
    path: Path,
    root: Path,
    findings: list[dict[str, str]],
    *,
    yaml_allowed: bool,
) -> Any:
    relative = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        add(findings, "read_error", relative, "$", str(error))
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        if not yaml_allowed:
            add(findings, "invalid_json", relative, "$", str(json_error))
            return None
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        add(
            findings,
            "yaml_parser_unavailable",
            relative,
            "$",
            "Block-style YAML requires PyYAML; JSON-form YAML needs no dependency.",
        )
        return None
    try:
        return yaml.safe_load(text)
    except Exception as error:  # PyYAML exposes several exception classes.
        add(findings, "invalid_yaml", relative, "$", str(error))
        return None


def validate_command(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> str | None:
    command = exact_object(
        value,
        {"id", "argv", "cwd", "timeout_seconds"},
        set(),
        relative,
        location,
        findings,
    )
    if command is None:
        return None
    command_id = validate_id(command.get("id"), relative, child(location, "id"), findings)
    if not unique_string_list(command.get("argv"), non_empty=True):
        add(
            findings,
            "invalid_command_argv",
            relative,
            child(location, "argv"),
            "argv must be a non-empty string array.",
        )
    validate_relative_path(
        command.get("cwd"),
        relative,
        child(location, "cwd"),
        findings,
        allow_dot=True,
    )
    timeout = command.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        add(
            findings,
            "invalid_command_timeout",
            relative,
            child(location, "timeout_seconds"),
            "timeout_seconds must be a positive integer.",
        )
    return command_id


def validate_support(
    value: Any,
    classification: Any,
    requirements: set[str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> str | None:
    if not isinstance(value, dict):
        add(findings, "invalid_support", relative, location, "support must be an object.")
        return None
    status = value.get("status")
    if status == "supported":
        expected = {"status"}
    elif status == "partial":
        expected = {"status", "reason", "missing_requirements"}
    elif status == "unimplemented":
        expected = {"status", "reason", "blocker"}
    elif status in {"intentionally_unsupported", "out_of_scope"}:
        expected = {"status", "reason", "authority"}
    elif status == "not_applicable":
        expected = {"status"}
    else:
        expected = {"status"}
    exact_object(value, expected, set(), relative, location, findings)
    if status not in SUPPORT_STATUSES:
        add(
            findings,
            "invalid_support_status",
            relative,
            child(location, "status"),
            f"Support status must be one of {sorted(SUPPORT_STATUSES)}.",
        )
        return None
    if classification == "endpoint" and status == "not_applicable":
        add(
            findings,
            "endpoint_support_not_applicable",
            relative,
            child(location, "status"),
            "Endpoint support cannot be not_applicable.",
        )
    if classification == "non_endpoint" and status != "not_applicable":
        add(
            findings,
            "non_endpoint_support_applicable",
            relative,
            child(location, "status"),
            "Non-endpoint support must be not_applicable.",
        )
    for field in ("reason", "blocker", "authority"):
        if field in expected and not non_empty_string(value.get(field)):
            add(
                findings,
                "invalid_support_explanation",
                relative,
                child(location, field),
                f"{field} must be non-empty.",
            )
    if status == "partial":
        missing = value.get("missing_requirements")
        if not unique_string_list(missing, non_empty=True):
            add(
                findings,
                "invalid_missing_requirements",
                relative,
                child(location, "missing_requirements"),
                "missing_requirements must be a non-empty unique ID array.",
            )
        elif not set(missing).issubset(requirements):
            add(
                findings,
                "unknown_missing_requirement",
                relative,
                child(location, "missing_requirements"),
                "Partial support names an unknown operation requirement.",
            )
    return status


def validate_observation_comparison(
    value: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    if not isinstance(value, dict):
        add(findings, "invalid_observation_comparison", relative, location, "comparison must be a fixed variant object.")
        return
    kind = value.get("kind")
    if kind in {"exact", "ordered", "unordered", "bytes"}:
        exact_object(value, {"kind"}, set(), relative, location, findings)
    elif kind == "numeric":
        comparison = exact_object(
            value,
            {"kind", "absolute_tolerance", "relative_tolerance", "nan_policy"},
            set(),
            relative,
            location,
            findings,
        )
        if comparison is not None:
            for field in ("absolute_tolerance", "relative_tolerance"):
                tolerance = comparison.get(field)
                if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
                    add(findings, "invalid_numeric_tolerance", relative, child(location, field), f"{field} must be non-negative.")
            if comparison.get("nan_policy") not in {"forbidden", "equal", "unequal"}:
                add(findings, "invalid_nan_policy", relative, child(location, "nan_policy"), "nan_policy must be forbidden, equal, or unequal.")
    elif kind == "text":
        comparison = exact_object(value, {"kind", "transforms", "reason"}, set(), relative, location, findings)
        if comparison is not None:
            transforms = comparison.get("transforms")
            if not unique_string_list(transforms) or not set(transforms or []).issubset(TEXT_TRANSFORMS):
                add(findings, "invalid_text_transforms", relative, child(location, "transforms"), f"transforms must be a unique subset of {sorted(TEXT_TRANSFORMS)}.")
                transforms = []
            reason = comparison.get("reason")
            if transforms and not non_empty_string(reason):
                add(findings, "missing_text_comparison_reason", relative, child(location, "reason"), "Text transforms require a durable reason.")
            if not transforms and reason is not None:
                add(findings, "unused_text_comparison_reason", relative, child(location, "reason"), "Exact text comparison uses null reason.")
    elif kind == "image":
        comparison = exact_object(
            value,
            {"kind", "pixel_mode", "maximum_channel_delta", "metadata_mode", "reason"},
            set(),
            relative,
            location,
            findings,
        )
        if comparison is not None:
            pixel_mode = comparison.get("pixel_mode")
            delta = comparison.get("maximum_channel_delta")
            metadata_mode = comparison.get("metadata_mode")
            if pixel_mode not in {"exact", "bounded_delta"}:
                add(findings, "invalid_image_pixel_mode", relative, child(location, "pixel_mode"), "pixel_mode must be exact or bounded_delta.")
            if not isinstance(delta, int) or isinstance(delta, bool) or not 0 <= delta <= 255:
                add(findings, "invalid_image_delta", relative, child(location, "maximum_channel_delta"), "maximum_channel_delta must be an integer from 0 through 255.")
            elif pixel_mode == "exact" and delta != 0:
                add(findings, "exact_image_has_delta", relative, child(location, "maximum_channel_delta"), "Exact pixels require zero channel delta.")
            elif pixel_mode == "bounded_delta" and delta == 0:
                add(findings, "bounded_image_without_delta", relative, child(location, "maximum_channel_delta"), "bounded_delta requires a positive channel delta.")
            if metadata_mode not in {"exact", "declared_only", "ignored"}:
                add(findings, "invalid_image_metadata_mode", relative, child(location, "metadata_mode"), "metadata_mode must be exact, declared_only, or ignored.")
            relaxed = pixel_mode == "bounded_delta" or metadata_mode != "exact"
            reason = comparison.get("reason")
            if relaxed and not non_empty_string(reason):
                add(findings, "missing_image_comparison_reason", relative, child(location, "reason"), "Relaxed image comparison requires a durable reason.")
            if not relaxed and reason is not None:
                add(findings, "unused_image_comparison_reason", relative, child(location, "reason"), "Exact image comparison uses null reason.")
    elif kind == "filesystem":
        comparison = exact_object(
            value,
            {"kind", "path_mode", "ordering", "content_mode"},
            set(),
            relative,
            location,
            findings,
        )
        if comparison is not None:
            if comparison.get("path_mode") not in {"relative", "portable_relative"}:
                add(findings, "invalid_filesystem_path_mode", relative, child(location, "path_mode"), "path_mode must be relative or portable_relative.")
            if comparison.get("ordering") not in {"declared", "sorted"}:
                add(findings, "invalid_filesystem_ordering", relative, child(location, "ordering"), "ordering must be declared or sorted.")
            if comparison.get("content_mode") != "exact":
                add(findings, "invalid_filesystem_content_mode", relative, child(location, "content_mode"), "content_mode must be exact.")
    else:
        exact_object(value, {"kind"}, set(), relative, location, findings)
        add(findings, "invalid_observation_comparison", relative, child(location, "kind"), f"comparison kind must be one of {sorted(OBSERVATION_COMPARISONS)}.")


def validate_result_contract(
    value: Any,
    classification: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    result = exact_object(
        value,
        {"shape", "observations", "error"},
        set(),
        relative,
        location,
        findings,
    )
    if result is None:
        return
    if result.get("shape") not in RESULT_SHAPES:
        add(
            findings,
            "invalid_result_shape",
            relative,
            child(location, "shape"),
            f"shape must be one of {sorted(RESULT_SHAPES)}.",
        )
    observations = result.get("observations")
    if not isinstance(observations, list):
        add(
            findings,
            "invalid_observations",
            relative,
            child(location, "observations"),
            "observations must be an array.",
        )
        observations = []
    if classification == "endpoint" and not observations:
        add(
            findings,
            "endpoint_without_observations",
            relative,
            child(location, "observations"),
            "Endpoint result requires at least one public observation.",
        )
    paths: set[str] = set()
    for index, observation in enumerate(observations):
        item_location = child(child(location, "observations"), index)
        item = exact_object(
            observation,
            {"path", "value_types", "comparison"},
            set(),
            relative,
            item_location,
            findings,
        )
        if item is None:
            continue
        path = item.get("path")
        if not non_empty_string(path):
            add(findings, "invalid_observation_path", relative, child(item_location, "path"), "path must be non-empty.")
        elif path in paths:
            add(findings, "duplicate_observation_path", relative, child(item_location, "path"), f"Duplicate observation path {path!r}.")
        else:
            paths.add(path)
        value_types = item.get("value_types")
        if (
            not unique_string_list(value_types, non_empty=True)
            or not set(value_types or []).issubset(VALUE_TYPES)
        ):
            add(
                findings,
                "invalid_observation_type",
                relative,
                child(item_location, "value_types"),
                f"value_types must be a non-empty unique subset of {sorted(VALUE_TYPES)}.",
            )
        validate_observation_comparison(
            item.get("comparison"),
            relative,
            child(item_location, "comparison"),
            findings,
        )

    error = exact_object(
        result.get("error"),
        {"fields", "message"},
        set(),
        relative,
        child(location, "error"),
        findings,
    )
    if error is None:
        return
    fields = error.get("fields")
    if not unique_string_list(fields) or not set(fields or []).issubset(ERROR_FIELDS):
        add(
            findings,
            "invalid_error_fields",
            relative,
            child(child(location, "error"), "fields"),
            f"fields must be a unique subset of {sorted(ERROR_FIELDS)}.",
        )
    message = exact_object(
        error.get("message"),
        {"mode", "transforms", "reason"},
        set(),
        relative,
        child(child(location, "error"), "message"),
        findings,
    )
    if message is None:
        return
    message_mode = message.get("mode")
    if message_mode not in {"exact", "normalized", "ignored"}:
        add(
            findings,
            "invalid_error_message_mode",
            relative,
            child(child(child(location, "error"), "message"), "mode"),
            "message mode must be exact, normalized, or ignored.",
        )
    transforms = message.get("transforms")
    if not unique_string_list(transforms) or not set(transforms or []).issubset(TEXT_TRANSFORMS):
        add(
            findings,
            "invalid_error_message_transforms",
            relative,
            child(child(child(location, "error"), "message"), "transforms"),
            f"transforms must be a unique subset of {sorted(TEXT_TRANSFORMS)}.",
        )
        transforms = []
    reason = message.get("reason")
    if message_mode == "exact":
        if transforms:
            add(
                findings,
                "exact_message_has_transforms",
                relative,
                child(child(child(location, "error"), "message"), "transforms"),
                "Exact message comparison cannot transform text.",
            )
        if reason is not None:
            add(
                findings,
                "exact_message_has_reason",
                relative,
                child(child(child(location, "error"), "message"), "reason"),
                "Exact message comparison uses null reason.",
            )
    elif message_mode == "normalized":
        if not transforms:
            add(
                findings,
                "normalized_message_without_transforms",
                relative,
                child(child(child(location, "error"), "message"), "transforms"),
                "Normalized message comparison requires transforms.",
            )
        if not non_empty_string(reason):
            add(
                findings,
                "missing_error_normalization_reason",
                relative,
                child(child(child(location, "error"), "message"), "reason"),
                "Normalized messages require a durable reason.",
            )
    elif message_mode == "ignored":
        if transforms:
            add(
                findings,
                "ignored_message_has_transforms",
                relative,
                child(child(child(location, "error"), "message"), "transforms"),
                "Ignored message comparison cannot transform text.",
            )
        if not non_empty_string(reason):
            add(
                findings,
                "missing_error_normalization_reason",
                relative,
                child(child(child(location, "error"), "message"), "reason"),
                "Ignored messages require a durable reason.",
            )


def validate_parameter_omission(
    value: Any,
    value_types: Any,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> str | None:
    if not isinstance(value, dict):
        add(findings, "invalid_parameter_omission", relative, location, "omission must be a fixed variant object.")
        return None
    kind = value.get("kind")
    if kind == "required":
        expected = {"kind"}
    elif kind == "literal":
        expected = {"kind", "value"}
    elif kind == "sentinel":
        expected = {"kind", "name", "semantics"}
    else:
        expected = {"kind"}
    exact_object(value, expected, set(), relative, location, findings)
    if kind not in {"required", "literal", "sentinel"}:
        add(
            findings,
            "invalid_parameter_omission_kind",
            relative,
            child(location, "kind"),
            "omission kind must be required, literal, or sentinel.",
        )
        return None
    declared_types = set(value_types) if unique_string_list(value_types, non_empty=True) else set()
    if (
        kind == "literal"
        and declared_types
        and declared_types.issubset(VALUE_TYPES)
        and not any(validate_literal_type(value.get("value"), value_type) for value_type in declared_types)
    ):
        add(
            findings,
            "parameter_default_type_mismatch",
            relative,
            child(location, "value"),
            f"Default literal does not match declared types {sorted(declared_types)}.",
        )
    if kind == "sentinel":
        for field in ("name", "semantics"):
            if not non_empty_string(value.get(field)):
                add(
                    findings,
                    "invalid_parameter_sentinel",
                    relative,
                    child(location, field),
                    f"Sentinel {field} must be non-empty.",
                )
    return kind


def validate_budget(
    value: Any,
    lane_names: set[str],
    known_subjects: set[str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    budget = exact_object(
        value,
        {
            "kind",
            "metric",
            "statistic",
            "operator",
            "value",
            "unit",
            "baseline_subject",
        },
        set(),
        relative,
        location,
        findings,
    )
    if budget is None:
        return
    if "benchmark" not in lane_names:
        add(findings, "budget_without_benchmark_lane", relative, location, "Budget requires the benchmark lane.")
    if budget.get("kind") not in BUDGET_KINDS:
        add(findings, "invalid_budget_kind", relative, child(location, "kind"), f"kind must be one of {sorted(BUDGET_KINDS)}.")
    if budget.get("metric") not in BENCHMARK_METRICS:
        add(findings, "invalid_budget_metric", relative, child(location, "metric"), f"metric must be one of {sorted(BENCHMARK_METRICS)}.")
    if budget.get("statistic") not in BUDGET_STATISTICS:
        add(findings, "invalid_budget_statistic", relative, child(location, "statistic"), f"statistic must be one of {sorted(BUDGET_STATISTICS)}.")
    if budget.get("operator") not in BUDGET_OPERATORS:
        add(findings, "invalid_budget_operator", relative, child(location, "operator"), f"operator must be one of {sorted(BUDGET_OPERATORS)}.")
    measured = budget.get("value")
    if not isinstance(measured, (int, float)) or isinstance(measured, bool):
        add(findings, "invalid_budget_value", relative, child(location, "value"), "value must be numeric.")
    if not non_empty_string(budget.get("unit")):
        add(findings, "invalid_budget_unit", relative, child(location, "unit"), "unit must be non-empty.")
    baseline = budget.get("baseline_subject")
    if budget.get("kind") == "absolute" and baseline is not None:
        add(findings, "absolute_budget_has_baseline", relative, child(location, "baseline_subject"), "Absolute budget baseline_subject must be null.")
    if budget.get("kind") == "relative":
        if not non_empty_string(baseline):
            add(findings, "relative_budget_without_baseline", relative, child(location, "baseline_subject"), "Relative budget requires baseline_subject.")
        elif baseline not in known_subjects:
            add(findings, "unknown_budget_baseline", relative, child(location, "baseline_subject"), f"Unknown benchmark subject {baseline!r}.")


def validate_lane(
    lane_name: str,
    value: Any,
    classification: Any,
    profile_ids: set[str],
    component_ids: set[str],
    operation_target_ids: set[str],
    profile_targets: dict[str, str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    lane = value if isinstance(value, dict) else {}
    applicability = lane.get("applicability")
    if applicability == "not_applicable":
        exact_object(
            value,
            {"applicability", "reason"},
            set(),
            relative,
            location,
            findings,
        )
        if not non_empty_string(lane.get("reason")):
            add(findings, "missing_lane_reason", relative, child(location, "reason"), "not_applicable requires a reason.")
        return {
            "applicability": applicability,
            "profiles": set(),
            "component_ids": set(),
            "metrics": set(),
        }

    required = {"applicability", "target_profiles"}
    if lane_name == "coverage":
        required.add("component_ids")
    if lane_name == "benchmark":
        required.add("metrics")
    exact_object(value, required, set(), relative, location, findings)
    if applicability != "required":
        add(findings, "invalid_lane_applicability", relative, child(location, "applicability"), "applicability must be required or not_applicable.")
    profiles = lane.get("target_profiles")
    if not unique_string_list(profiles, non_empty=True):
        add(findings, "invalid_lane_profiles", relative, child(location, "target_profiles"), "Required lane needs unique target profiles.")
        profiles = []
    unknown_profiles = set(profiles) - profile_ids
    if unknown_profiles:
        add(findings, "unknown_lane_profile", relative, child(location, "target_profiles"), f"Unknown target profiles: {sorted(unknown_profiles)}.")
    for profile in profiles:
        target_id = profile_targets.get(profile)
        if target_id is not None and target_id not in operation_target_ids:
            add(
                findings,
                "lane_profile_without_target_binding",
                relative,
                child(location, "target_profiles"),
                f"Profile {profile!r} uses target {target_id!r}, which has no operation binding.",
            )
    if classification == "non_endpoint":
        add(findings, "non_endpoint_required_lane", relative, child(location, "applicability"), "Non-endpoint lanes must be not_applicable.")
    if lane_name == "coverage":
        components = lane.get("component_ids")
        if not unique_string_list(components, non_empty=True):
            add(findings, "invalid_lane_components", relative, child(location, "component_ids"), "Coverage requires component IDs.")
            components = []
        unknown = set(components) - component_ids
        if unknown:
            add(findings, "unknown_lane_component", relative, child(location, "component_ids"), f"Unknown coverage components: {sorted(unknown)}.")
    else:
        components = []
    if lane_name == "benchmark":
        metrics = lane.get("metrics")
        if not unique_string_list(metrics, non_empty=True) or not set(metrics or []).issubset(BENCHMARK_METRICS):
            add(findings, "invalid_lane_metrics", relative, child(location, "metrics"), f"metrics must be a non-empty subset of {sorted(BENCHMARK_METRICS)}.")
    else:
        metrics = []
    return {
        "applicability": applicability,
        "profiles": set(profiles),
        "component_ids": set(components),
        "metrics": set(metrics),
    }


def validate_manifest(
    payload: Any,
    root: Path,
    manifest_path: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    relative = manifest_path.relative_to(root).as_posix()
    index: dict[str, Any] = {
        "mode": None,
        "commands": {},
        "oracles": {},
        "targets": {},
        "profiles": {},
        "profile_targets": {},
        "components": {},
        "operations": {},
        "requirements": {},
        "input_paths": {lane: {} for lane in LANES},
        "documentation_outputs": 0,
        "endpoint_count": 0,
        "complete_endpoint_count": 0,
        "operation_count": 0,
    }
    top = exact_object(
        payload,
        {
            "schema",
            "scope",
            "oracles",
            "targets",
            "target_profiles",
            "commands",
            "interfaces",
            "input_index",
            "coverage_components",
            "surfaces",
            "documentation",
        },
        set(),
        relative,
        "$",
        findings,
    )
    if top is None:
        return index
    if top.get("schema") != MANIFEST_SCHEMA:
        add(findings, "unsupported_manifest_schema", relative, "$.schema", f"Expected {MANIFEST_SCHEMA!r}.")

    scope = exact_object(top.get("scope"), {"id", "mode", "inventory"}, set(), relative, "$.scope", findings)
    if scope is not None:
        validate_id(scope.get("id"), relative, "$.scope.id", findings)
        mode = scope.get("mode")
        if mode not in {"slice", "full"}:
            add(findings, "invalid_scope_mode", relative, "$.scope.mode", "mode must be slice or full.")
        else:
            index["mode"] = mode
        inventory = exact_object(scope.get("inventory"), {"authority", "revision", "command_id"}, set(), relative, "$.scope.inventory", findings)
        if inventory is not None:
            for field in ("authority", "revision", "command_id"):
                if not non_empty_string(inventory.get(field)):
                    add(findings, "invalid_inventory_field", relative, f"$.scope.inventory.{field}", f"{field} must be non-empty.")

    commands = top.get("commands")
    if not isinstance(commands, list) or not commands:
        add(findings, "invalid_commands", relative, "$.commands", "commands must be a non-empty array.")
        commands = []
    for position, command in enumerate(commands):
        location = f"$.commands[{position}]"
        command_id = validate_command(command, relative, location, findings)
        register(index["commands"], command_id, command, "command", relative, child(location, "id"), findings)

    oracles = top.get("oracles")
    if not isinstance(oracles, list) or not oracles:
        add(findings, "invalid_oracles", relative, "$.oracles", "oracles must be a non-empty array.")
        oracles = []
    for position, value in enumerate(oracles):
        location = f"$.oracles[{position}]"
        oracle = exact_object(value, {"id", "name", "version", "runtime", "identity_command_id", "contract", "components"}, set(), relative, location, findings)
        if oracle is None:
            continue
        oracle_id = validate_id(oracle.get("id"), relative, child(location, "id"), findings)
        for field in ("name", "version", "runtime", "contract"):
            if not non_empty_string(oracle.get(field)):
                add(findings, "invalid_oracle_field", relative, child(location, field), f"{field} must be non-empty.")
        components = oracle.get("components")
        if not isinstance(components, list):
            add(findings, "invalid_oracle_components", relative, child(location, "components"), "components must be an array.")
            components = []
        component_names: set[str] = set()
        for component_position, component_value in enumerate(components):
            component_location = child(child(location, "components"), component_position)
            component = exact_object(component_value, {"id", "name", "version"}, set(), relative, component_location, findings)
            if component is None:
                continue
            component_id = validate_id(component.get("id"), relative, child(component_location, "id"), findings)
            if component_id in component_names:
                add(findings, "duplicate_oracle_component", relative, child(component_location, "id"), f"Duplicate oracle component {component_id!r}.")
            elif component_id is not None:
                component_names.add(component_id)
            for field in ("name", "version"):
                if not non_empty_string(component.get(field)):
                    add(findings, "invalid_oracle_component_field", relative, child(component_location, field), f"{field} must be non-empty.")
        register(index["oracles"], oracle_id, oracle, "oracle", relative, child(location, "id"), findings)

    targets = top.get("targets")
    if not isinstance(targets, list) or not targets:
        add(findings, "invalid_targets", relative, "$.targets", "targets must be a non-empty array.")
        targets = []
    for position, value in enumerate(targets):
        location = f"$.targets[{position}]"
        target = exact_object(value, {"id", "name", "runtime", "identity_command_id", "contract"}, set(), relative, location, findings)
        if target is None:
            continue
        target_id = validate_id(target.get("id"), relative, child(location, "id"), findings)
        for field in ("name", "runtime", "contract"):
            if not non_empty_string(target.get(field)):
                add(findings, "invalid_target_field", relative, child(location, field), f"{field} must be non-empty.")
        register(index["targets"], target_id, target, "target", relative, child(location, "id"), findings)

    profiles = top.get("target_profiles")
    if not isinstance(profiles, list) or not profiles:
        add(findings, "invalid_target_profiles", relative, "$.target_profiles", "target_profiles must be a non-empty array.")
        profiles = []
    for position, value in enumerate(profiles):
        location = f"$.target_profiles[{position}]"
        profile = exact_object(value, {"id", "target_id", "backend", "features"}, set(), relative, location, findings)
        if profile is None:
            continue
        profile_id = validate_id(profile.get("id"), relative, child(location, "id"), findings)
        target_id = profile.get("target_id")
        if target_id not in index["targets"]:
            add(findings, "unknown_profile_target", relative, child(location, "target_id"), f"Unknown target {target_id!r}.")
        if not non_empty_string(profile.get("backend")):
            add(findings, "invalid_profile_backend", relative, child(location, "backend"), "backend must be non-empty.")
        if not unique_string_list(profile.get("features")):
            add(findings, "invalid_profile_features", relative, child(location, "features"), "features must be a unique string array.")
        register(index["profiles"], profile_id, profile, "target_profile", relative, child(location, "id"), findings)
        if profile_id is not None and isinstance(target_id, str):
            index["profile_targets"][profile_id] = target_id

    command_ids = set(index["commands"])
    for oracle_id, oracle in index["oracles"].items():
        command_id = oracle.get("identity_command_id")
        if command_id not in command_ids:
            add(findings, "unknown_oracle_identity_command", relative, "$.oracles", f"Oracle {oracle_id!r} references unknown command {command_id!r}.")
    for target_id, target in index["targets"].items():
        command_id = target.get("identity_command_id")
        if command_id not in command_ids:
            add(findings, "unknown_target_identity_command", relative, "$.targets", f"Target {target_id!r} references unknown command {command_id!r}.")
    inventory_command = ((scope or {}).get("inventory") or {}).get("command_id") if isinstance((scope or {}).get("inventory"), dict) else None
    if inventory_command not in command_ids:
        add(findings, "unknown_inventory_command", relative, "$.scope.inventory.command_id", f"Unknown command {inventory_command!r}.")

    interfaces = exact_object(top.get("interfaces"), {"parity", "coverage", "benchmark", "aggregation"}, set(), relative, "$.interfaces", findings)
    if interfaces is not None:
        for lane in LANES:
            lane_interface = exact_object(interfaces.get(lane), {"input_schema", "result_schema", "command_id"}, set(), relative, f"$.interfaces.{lane}", findings)
            if lane_interface is None:
                continue
            if lane_interface.get("input_schema") != INPUT_SCHEMAS[lane]:
                add(findings, "invalid_input_schema_interface", relative, f"$.interfaces.{lane}.input_schema", f"Expected {INPUT_SCHEMAS[lane]!r}.")
            if lane_interface.get("result_schema") != RESULT_SCHEMAS[lane]:
                add(findings, "invalid_result_schema_interface", relative, f"$.interfaces.{lane}.result_schema", f"Expected {RESULT_SCHEMAS[lane]!r}.")
            if lane_interface.get("command_id") not in command_ids:
                add(findings, "unknown_interface_command", relative, f"$.interfaces.{lane}.command_id", "Interface command_id must resolve through commands.")
        aggregation = exact_object(interfaces.get("aggregation"), {"input_schemas", "result_schema", "command_id"}, set(), relative, "$.interfaces.aggregation", findings)
        if aggregation is not None:
            schemas = aggregation.get("input_schemas")
            if not unique_string_list(schemas, non_empty=True) or set(schemas or []) != set(RESULT_SCHEMAS.values()):
                add(findings, "invalid_aggregation_inputs", relative, "$.interfaces.aggregation.input_schemas", "Aggregation must consume exactly the three lane result schemas.")
            if aggregation.get("result_schema") != AGGREGATE_SCHEMA:
                add(findings, "invalid_aggregate_schema", relative, "$.interfaces.aggregation.result_schema", f"Expected {AGGREGATE_SCHEMA!r}.")
            if aggregation.get("command_id") not in command_ids:
                add(findings, "unknown_interface_command", relative, "$.interfaces.aggregation.command_id", "Aggregation command_id must resolve through commands.")

    input_index = exact_object(top.get("input_index"), set(LANES), set(), relative, "$.input_index", findings)
    if input_index is not None:
        for lane in LANES:
            paths = input_index.get(lane)
            if not unique_string_list(paths):
                add(findings, "invalid_input_index", relative, f"$.input_index.{lane}", "Input index must be a unique string array.")
                continue
            for path_value in paths:
                if not safe_relative_path(path_value) or not path_value.startswith(f"inputs/{lane}/") or not path_value.endswith(".json"):
                    add(findings, "invalid_indexed_input_path", relative, f"$.input_index.{lane}", f"{path_value!r} must be JSON beneath inputs/{lane}/.")
                    continue
                if path_value in index["input_paths"][lane]:
                    add(findings, "duplicate_indexed_input", relative, f"$.input_index.{lane}", f"Duplicate indexed path {path_value!r}.")
                index["input_paths"][lane][path_value] = True

    coverage_components = top.get("coverage_components")
    if not isinstance(coverage_components, list):
        add(findings, "invalid_coverage_components", relative, "$.coverage_components", "coverage_components must be an array.")
        coverage_components = []
    for position, value in enumerate(coverage_components):
        location = f"$.coverage_components[{position}]"
        component = exact_object(value, {"id", "target_profile", "paths", "dimensions", "thresholds"}, set(), relative, location, findings)
        if component is None:
            continue
        component_id = validate_id(component.get("id"), relative, child(location, "id"), findings)
        profile = component.get("target_profile")
        if profile not in index["profiles"]:
            add(findings, "unknown_component_profile", relative, child(location, "target_profile"), f"Unknown target profile {profile!r}.")
        paths = component.get("paths")
        if not unique_string_list(paths, non_empty=True):
            add(findings, "invalid_component_paths", relative, child(location, "paths"), "paths must be a non-empty unique array.")
        else:
            for path_position, path_value in enumerate(paths):
                validate_relative_path(path_value, relative, child(child(location, "paths"), path_position), findings)
        dimensions = component.get("dimensions")
        if not unique_string_list(dimensions, non_empty=True) or not set(dimensions or []).issubset(COVERAGE_DIMENSIONS):
            add(findings, "invalid_component_dimensions", relative, child(location, "dimensions"), f"dimensions must be a non-empty subset of {sorted(COVERAGE_DIMENSIONS)}.")
        thresholds = component.get("thresholds")
        if not isinstance(thresholds, list):
            add(findings, "invalid_component_thresholds", relative, child(location, "thresholds"), "thresholds must be an array.")
            thresholds = []
        threshold_dimensions: set[str] = set()
        for threshold_position, threshold_value in enumerate(thresholds):
            threshold_location = child(child(location, "thresholds"), threshold_position)
            threshold = exact_object(threshold_value, {"dimension", "minimum_percent"}, set(), relative, threshold_location, findings)
            if threshold is None:
                continue
            dimension = threshold.get("dimension")
            if dimension not in set(dimensions or []):
                add(findings, "threshold_without_dimension", relative, child(threshold_location, "dimension"), "Threshold dimension must be declared by the component.")
            if dimension in threshold_dimensions:
                add(findings, "duplicate_component_threshold", relative, child(threshold_location, "dimension"), f"Duplicate threshold for {dimension!r}.")
            elif isinstance(dimension, str):
                threshold_dimensions.add(dimension)
            minimum = threshold.get("minimum_percent")
            if not isinstance(minimum, (int, float)) or isinstance(minimum, bool) or not 0 <= minimum <= 100:
                add(findings, "invalid_threshold_percent", relative, child(threshold_location, "minimum_percent"), "minimum_percent must be from 0 through 100.")
        register(index["components"], component_id, component, "coverage_component", relative, child(location, "id"), findings)

    profile_ids = set(index["profiles"])
    component_ids = set(index["components"])
    known_subjects = set(index["oracles"]) | profile_ids
    surfaces = top.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        add(findings, "invalid_surfaces", relative, "$.surfaces", "surfaces must be a non-empty array.")
        surfaces = []
    surface_ids: set[str] = set()
    for surface_position, surface_value in enumerate(surfaces):
        surface_location = f"$.surfaces[{surface_position}]"
        surface = exact_object(surface_value, {"id", "kind", "source_path", "storage_slug", "operations"}, set(), relative, surface_location, findings)
        if surface is None:
            continue
        surface_id = validate_id(surface.get("id"), relative, child(surface_location, "id"), findings, public=True)
        if surface_id in surface_ids:
            add(findings, "duplicate_surface_id", relative, child(surface_location, "id"), f"Duplicate surface {surface_id!r}.")
        elif surface_id is not None:
            surface_ids.add(surface_id)
        if surface.get("kind") not in SURFACE_KINDS:
            add(findings, "invalid_surface_kind", relative, child(surface_location, "kind"), f"kind must be one of {sorted(SURFACE_KINDS)}.")
        if not non_empty_string(surface.get("source_path")):
            add(findings, "invalid_surface_source_path", relative, child(surface_location, "source_path"), "source_path must be non-empty.")
        if not isinstance(surface.get("storage_slug"), str) or SLUG_RE.fullmatch(surface.get("storage_slug")) is None:
            add(findings, "invalid_storage_slug", relative, child(surface_location, "storage_slug"), "storage_slug must be lowercase hyphen-case.")
        operations = surface.get("operations")
        if not isinstance(operations, list) or not operations:
            add(findings, "invalid_operations", relative, child(surface_location, "operations"), "operations must be a non-empty array.")
            operations = []
        operation_ids: set[str] = set()
        for operation_position, operation_value in enumerate(operations):
            operation_location = child(child(surface_location, "operations"), operation_position)
            operation_finding_start = len(findings)
            if isinstance(operation_value, dict) and operation_value.get("classification") == "endpoint":
                index["endpoint_count"] += 1
            operation = exact_object(
                operation_value,
                {"id", "kind", "classification", "lifecycle", "source", "targets", "requirements", "parity", "coverage", "benchmark"},
                set(),
                relative,
                operation_location,
                findings,
            )
            if operation is None or surface_id is None:
                continue
            operation_id = validate_id(operation.get("id"), relative, child(operation_location, "id"), findings, public=True)
            if operation_id in operation_ids:
                add(findings, "duplicate_operation_id", relative, child(operation_location, "id"), f"Duplicate operation {operation_id!r} in surface.")
                continue
            if operation_id is None:
                continue
            operation_ids.add(operation_id)
            operation_key = (surface_id, operation_id)
            index["operation_count"] += 1
            if operation.get("kind") not in OPERATION_KINDS:
                add(findings, "invalid_operation_kind", relative, child(operation_location, "kind"), f"kind must be one of {sorted(OPERATION_KINDS)}.")
            classification = operation.get("classification")
            if classification not in CLASSIFICATIONS:
                add(findings, "invalid_classification", relative, child(operation_location, "classification"), f"classification must be one of {sorted(CLASSIFICATIONS)}.")

            lifecycle = operation.get("lifecycle")
            if isinstance(lifecycle, dict) and lifecycle.get("status") == "current":
                exact_object(lifecycle, {"status"}, set(), relative, child(operation_location, "lifecycle"), findings)
            elif isinstance(lifecycle, dict) and lifecycle.get("status") == "deprecated":
                exact_object(lifecycle, {"status", "authority", "replacement"}, set(), relative, child(operation_location, "lifecycle"), findings)
                if not non_empty_string(lifecycle.get("authority")):
                    add(findings, "invalid_lifecycle_authority", relative, child(child(operation_location, "lifecycle"), "authority"), "Deprecated lifecycle requires authority.")
                if lifecycle.get("replacement") is not None and not non_empty_string(lifecycle.get("replacement")):
                    add(findings, "invalid_lifecycle_replacement", relative, child(child(operation_location, "lifecycle"), "replacement"), "replacement must be non-empty or null.")
            else:
                exact_object(lifecycle, {"status"}, set(), relative, child(operation_location, "lifecycle"), findings)
                add(findings, "invalid_lifecycle_status", relative, child(child(operation_location, "lifecycle"), "status"), "Lifecycle status must be current or deprecated.")

            source = exact_object(operation.get("source"), {"oracle_id", "path", "signature", "parameters", "result"}, set(), relative, child(operation_location, "source"), findings)
            parameters: dict[str, dict[str, Any]] = {}
            if source is not None:
                if source.get("oracle_id") not in index["oracles"]:
                    add(findings, "unknown_operation_oracle", relative, child(child(operation_location, "source"), "oracle_id"), f"Unknown oracle {source.get('oracle_id')!r}.")
                for field in ("path", "signature"):
                    if not non_empty_string(source.get(field)):
                        add(findings, "invalid_source_binding", relative, child(child(operation_location, "source"), field), f"{field} must be non-empty.")
                parameter_values = source.get("parameters")
                if not isinstance(parameter_values, list):
                    add(findings, "invalid_parameters", relative, child(child(operation_location, "source"), "parameters"), "parameters must be an array.")
                    parameter_values = []
                for parameter_position, parameter_value in enumerate(parameter_values):
                    parameter_location = child(child(child(operation_location, "source"), "parameters"), parameter_position)
                    parameter = exact_object(parameter_value, {"id", "style", "value_types", "omission"}, set(), relative, parameter_location, findings)
                    if parameter is None:
                        continue
                    parameter_id = validate_id(parameter.get("id"), relative, child(parameter_location, "id"), findings)
                    if parameter_id in parameters:
                        add(findings, "duplicate_parameter_id", relative, child(parameter_location, "id"), f"Duplicate parameter {parameter_id!r}.")
                    elif parameter_id is not None:
                        parameters[parameter_id] = parameter
                    if parameter.get("style") not in PARAMETER_STYLES:
                        add(findings, "invalid_parameter_style", relative, child(parameter_location, "style"), f"style must be one of {sorted(PARAMETER_STYLES)}.")
                    value_types = parameter.get("value_types")
                    if (
                        not unique_string_list(value_types, non_empty=True)
                        or not set(value_types or []).issubset(VALUE_TYPES)
                    ):
                        add(
                            findings,
                            "invalid_parameter_type",
                            relative,
                            child(parameter_location, "value_types"),
                            f"value_types must be a non-empty unique subset of {sorted(VALUE_TYPES)}.",
                        )
                    omission_kind = validate_parameter_omission(
                        parameter.get("omission"),
                        value_types,
                        relative,
                        child(parameter_location, "omission"),
                        findings,
                    )
                    if parameter.get("style") == "receiver" and omission_kind != "required":
                        add(
                            findings,
                            "optional_receiver",
                            relative,
                            child(parameter_location, "omission"),
                            "Receiver omission kind must be required.",
                        )
                    if parameter.get("style") in {"variadic_positional", "variadic_keyword"} and omission_kind == "required":
                        add(
                            findings,
                            "required_variadic_parameter",
                            relative,
                            child(parameter_location, "omission"),
                            "Variadic parameter omission must describe its empty literal default.",
                        )
                receiver_count = sum(1 for parameter in parameters.values() if parameter.get("style") == "receiver")
                if receiver_count > 1:
                    add(findings, "multiple_receiver_parameters", relative, child(child(operation_location, "source"), "parameters"), "An operation may declare at most one receiver.")
                validate_result_contract(source.get("result"), classification, relative, child(child(operation_location, "source"), "result"), findings)

            requirements_value = operation.get("requirements")
            if not isinstance(requirements_value, list):
                add(findings, "invalid_requirements", relative, child(operation_location, "requirements"), "requirements must be an array.")
                requirements_value = []
            if classification == "endpoint" and not requirements_value:
                add(findings, "endpoint_without_requirements", relative, child(operation_location, "requirements"), "Every endpoint requires semantic requirements.")
            if classification == "non_endpoint" and requirements_value:
                add(findings, "non_endpoint_has_requirements", relative, child(operation_location, "requirements"), "Non-endpoint cannot declare executable requirements.")
            operation_requirements: set[str] = set()
            requirement_records: list[tuple[str, set[str], set[str], str]] = []
            for requirement_position, requirement_value in enumerate(requirements_value):
                requirement_location = child(child(operation_location, "requirements"), requirement_position)
                requirement = exact_object(requirement_value, {"id", "dimension", "description", "lanes", "target_profiles"}, {"budget"}, relative, requirement_location, findings)
                if requirement is None:
                    continue
                requirement_id = validate_stable_id(requirement.get("id"), relative, child(requirement_location, "id"), findings)
                if requirement_id is not None and requirement_id in index["requirements"]:
                    add(findings, "duplicate_requirement_id", relative, child(requirement_location, "id"), f"Duplicate global requirement {requirement_id!r}.")
                    requirement_id = None
                if requirement_id is not None:
                    operation_requirements.add(requirement_id)
                if requirement.get("dimension") not in REQUIREMENT_DIMENSIONS:
                    add(findings, "invalid_requirement_dimension", relative, child(requirement_location, "dimension"), f"dimension must be one of {sorted(REQUIREMENT_DIMENSIONS)}.")
                if not non_empty_string(requirement.get("description")):
                    add(findings, "invalid_requirement_description", relative, child(requirement_location, "description"), "description must be non-empty.")
                lane_names = requirement.get("lanes")
                if not unique_string_list(lane_names, non_empty=True) or not set(lane_names or []).issubset(LANES):
                    add(findings, "invalid_requirement_lanes", relative, child(requirement_location, "lanes"), f"lanes must be a non-empty subset of {LANES}.")
                    lane_names = []
                requirement_profiles = requirement.get("target_profiles")
                if not unique_string_list(requirement_profiles, non_empty=True):
                    add(findings, "invalid_requirement_profiles", relative, child(requirement_location, "target_profiles"), "target_profiles must be a non-empty unique array.")
                    requirement_profiles = []
                unknown_profiles = set(requirement_profiles) - profile_ids
                if unknown_profiles:
                    add(findings, "unknown_requirement_profile", relative, child(requirement_location, "target_profiles"), f"Unknown profiles: {sorted(unknown_profiles)}.")
                if "budget" in requirement:
                    validate_budget(requirement.get("budget"), set(lane_names), known_subjects, relative, child(requirement_location, "budget"), findings)
                if requirement_id is not None:
                    record = {
                        "operation": operation_key,
                        "lanes": set(lane_names),
                        "profiles": set(requirement_profiles),
                        "budget": requirement.get("budget"),
                        "location": requirement_location,
                    }
                    index["requirements"][requirement_id] = record
                    requirement_records.append((requirement_id, set(lane_names), set(requirement_profiles), requirement_location))

            target_bindings = operation.get("targets")
            if not isinstance(target_bindings, list) or not target_bindings:
                add(findings, "invalid_target_bindings", relative, child(operation_location, "targets"), "operations require at least one target binding.")
                target_bindings = []
            operation_target_ids: set[str] = set()
            pending_support: list[tuple[dict[str, Any], str]] = []
            for target_position, target_value in enumerate(target_bindings):
                target_location = child(child(operation_location, "targets"), target_position)
                target = exact_object(target_value, {"target_id", "path", "signature", "support"}, set(), relative, target_location, findings)
                if target is None:
                    continue
                target_id = target.get("target_id")
                if target_id not in index["targets"]:
                    add(findings, "unknown_operation_target", relative, child(target_location, "target_id"), f"Unknown target {target_id!r}.")
                if target_id in operation_target_ids:
                    add(findings, "duplicate_operation_target", relative, child(target_location, "target_id"), f"Duplicate binding for target {target_id!r}.")
                elif isinstance(target_id, str):
                    operation_target_ids.add(target_id)
                for field in ("path", "signature"):
                    field_value = target.get(field)
                    if field_value is not None and not non_empty_string(field_value):
                        add(findings, "invalid_target_binding_field", relative, child(target_location, field), f"{field} must be non-empty or null.")
                pending_support.append((target, child(target_location, "support")))

            lane_specs: dict[str, dict[str, Any]] = {}
            for lane in LANES:
                lane_specs[lane] = validate_lane(
                    lane,
                    operation.get(lane),
                    classification,
                    profile_ids,
                    component_ids,
                    operation_target_ids,
                    index["profile_targets"],
                    relative,
                    child(operation_location, lane),
                    findings,
                )
            coverage_lane = lane_specs["coverage"]
            for component_id in coverage_lane["component_ids"]:
                component = index["components"].get(component_id)
                if (
                    component is not None
                    and component.get("target_profile")
                    not in coverage_lane["profiles"]
                ):
                    add(
                        findings,
                        "lane_component_profile_mismatch",
                        relative,
                        child(operation_location, "coverage"),
                        f"Component {component_id!r} belongs to profile "
                        f"{component.get('target_profile')!r}, which the lane does not select.",
                    )
            for requirement_id, lane_names, requirement_profiles, requirement_location in requirement_records:
                for lane in lane_names:
                    lane_spec = lane_specs[lane]
                    if lane_spec["applicability"] != "required":
                        add(findings, "requirement_for_inapplicable_lane", relative, child(requirement_location, "lanes"), f"Requirement names non-applicable {lane} lane.")
                    missing_profiles = requirement_profiles - lane_spec["profiles"]
                    if missing_profiles:
                        add(findings, "requirement_profile_outside_lane", relative, child(requirement_location, "target_profiles"), f"Profiles not selected by {lane}: {sorted(missing_profiles)}.")
            for lane, lane_spec in lane_specs.items():
                if lane_spec["applicability"] != "required":
                    continue
                covered_profiles = set().union(
                    *(
                        profiles
                        for _, lanes, profiles, _ in requirement_records
                        if lane in lanes
                    ),
                    set(),
                )
                missing = lane_spec["profiles"] - covered_profiles
                if missing:
                    add(findings, "lane_profile_without_requirement", relative, child(operation_location, "requirements"), f"{lane} profiles lack requirements: {sorted(missing)}.")
            for target, support_location in pending_support:
                status = validate_support(target.get("support"), classification, operation_requirements, relative, support_location, findings)
                binding_location = support_location.rsplit(".support", 1)[0]
                if status in {"supported", "partial"}:
                    if target.get("path") is None:
                        add(
                            findings,
                            "implemented_target_without_path",
                            relative,
                            child(binding_location, "path"),
                            "Supported and partial targets require a public path.",
                        )
                    if target.get("signature") is None:
                        add(
                            findings,
                            "implemented_target_without_signature",
                            relative,
                            child(binding_location, "signature"),
                            "Supported and partial targets require a signature.",
                        )
                elif status in {
                    "unimplemented",
                    "intentionally_unsupported",
                    "out_of_scope",
                    "not_applicable",
                }:
                    if target.get("signature") is not None:
                        add(
                            findings,
                            "nonendpoint_claim_has_signature",
                            relative,
                            child(binding_location, "signature"),
                            f"{status} target signature must be null.",
                        )

            index["operations"][operation_key] = {
                "classification": classification,
                "parameters": parameters,
                "target_ids": operation_target_ids,
                "lanes": lane_specs,
                "requirements": operation_requirements,
                "location": operation_location,
            }
            if classification == "endpoint" and len(findings) == operation_finding_start:
                index["complete_endpoint_count"] += 1

    documentation = exact_object(top.get("documentation"), {"command_id", "specification_outputs", "evidence_outputs"}, set(), relative, "$.documentation", findings)
    if documentation is not None:
        if documentation.get("command_id") not in command_ids:
            add(findings, "unknown_documentation_command", relative, "$.documentation.command_id", "Documentation command_id must resolve through commands.")
        outputs: list[str] = []
        for field in ("specification_outputs", "evidence_outputs"):
            values = documentation.get(field)
            if not unique_string_list(values, non_empty=True):
                add(findings, "invalid_documentation_outputs", relative, f"$.documentation.{field}", f"{field} must be a non-empty unique array.")
                continue
            outputs.extend(values)
            for position, path_value in enumerate(values):
                validate_relative_path(path_value, relative, child(f"$.documentation.{field}", position), findings)
        if len(outputs) != len(set(outputs)):
            add(findings, "duplicate_documentation_output", relative, "$.documentation", "Documentation output paths must be globally unique.")
        index["documentation_outputs"] = len(outputs)

    return index


def validate_literal_type(value: Any, value_type: str) -> bool:
    if value_type == "any_json":
        return True
    if value_type == "null":
        return value is None
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if value_type in {"string", "path", "enum", "bytes"}:
        return isinstance(value, str)
    if value_type == "sequence":
        return isinstance(value, list)
    if value_type in {"mapping", "record"}:
        return isinstance(value, dict)
    return False


def validate_value_descriptor(
    value: Any,
    expected_types: set[str] | None,
    asset_ids: set[str],
    prior_steps: set[str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> None:
    if not isinstance(value, dict):
        add(findings, "invalid_value_descriptor", relative, location, "Argument values must be discriminated objects.")
        return
    kind = value.get("kind")
    if kind == "literal":
        exact_object(value, {"kind", "value"}, set(), relative, location, findings)
        if expected_types and not any(validate_literal_type(value.get("value"), value_type) for value_type in expected_types):
            add(findings, "literal_type_mismatch", relative, child(location, "value"), f"Literal does not match declared types {sorted(expected_types)}.")
    elif kind == "asset":
        exact_object(value, {"kind", "asset_id"}, set(), relative, location, findings)
        if value.get("asset_id") not in asset_ids:
            add(findings, "unknown_asset_reference", relative, child(location, "asset_id"), f"Unknown asset {value.get('asset_id')!r}.")
        asset_types = {"any_json", "bytes", "path", "image", "font", "stream"}
        if expected_types and not expected_types.intersection(asset_types):
            add(findings, "asset_type_mismatch", relative, location, f"Asset cannot satisfy declared types {sorted(expected_types)}.")
    elif kind == "binding":
        exact_object(value, {"kind", "step_id"}, set(), relative, location, findings)
        if value.get("step_id") not in prior_steps:
            add(findings, "invalid_binding_reference", relative, child(location, "step_id"), "Binding must reference an earlier step.")
    else:
        exact_object(value, {"kind"}, set(), relative, location, findings)
        add(findings, "invalid_value_kind", relative, child(location, "kind"), "Value kind must be literal, asset, or binding.")


def resolve_asset_path(assets_root: Path, path_value: str) -> Path:
    return assets_root.joinpath(*PurePosixPath(path_value).parts)


def validate_assets(
    values: Any,
    commands: set[str],
    assets_root: Path,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> set[str]:
    if not isinstance(values, list):
        add(findings, "invalid_assets", relative, location, "assets must be an array.")
        return set()
    asset_ids: set[str] = set()
    for position, value in enumerate(values):
        asset_location = child(location, position)
        if not isinstance(value, dict):
            add(findings, "invalid_asset", relative, asset_location, "Asset must be an object.")
            continue
        kind = value.get("kind")
        fields_by_kind = {
            "ref": {"id", "kind", "path", "sha256", "media_type"},
            "inline": {"id", "kind", "encoding", "data", "sha256", "media_type"},
            "generated": {"id", "kind", "path", "command_id", "seed", "sha256", "media_type"},
            "builtin": {"id", "kind", "name"},
            "missing": {"id", "kind", "path"},
            "remote_mock": {"id", "kind", "path", "command_id", "endpoint", "sha256", "media_type"},
        }
        expected = fields_by_kind.get(kind, {"id", "kind"})
        asset = exact_object(value, expected, set(), relative, asset_location, findings)
        if asset is None:
            continue
        asset_id = validate_id(asset.get("id"), relative, child(asset_location, "id"), findings)
        if asset_id in asset_ids:
            add(findings, "duplicate_asset_id", relative, child(asset_location, "id"), f"Duplicate asset {asset_id!r}.")
        elif asset_id is not None:
            asset_ids.add(asset_id)
        if kind not in ASSET_KINDS:
            add(findings, "invalid_asset_kind", relative, child(asset_location, "kind"), f"kind must be one of {sorted(ASSET_KINDS)}.")
            continue
        if kind in {"ref", "generated", "missing", "remote_mock"}:
            path_value = validate_relative_path(asset.get("path"), relative, child(asset_location, "path"), findings)
            if path_value is not None:
                resolved = resolve_asset_path(assets_root, path_value)
                if kind in {"ref", "remote_mock"} and not resolved.is_file():
                    add(findings, "missing_asset_file", relative, child(asset_location, "path"), f"Asset file does not exist beneath the asset root: {path_value}.")
                if kind == "missing" and resolved.exists():
                    add(findings, "missing_asset_exists", relative, child(asset_location, "path"), f"missing asset unexpectedly exists: {path_value}.")
        if kind in {"ref", "inline", "generated", "remote_mock"}:
            digest = asset.get("sha256")
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                add(findings, "invalid_asset_digest", relative, child(asset_location, "sha256"), "sha256 must be 64 lowercase hexadecimal characters.")
            if not non_empty_string(asset.get("media_type")):
                add(findings, "invalid_asset_media_type", relative, child(asset_location, "media_type"), "media_type must be non-empty.")
            if kind in {"ref", "remote_mock"} and isinstance(asset.get("path"), str):
                resolved = resolve_asset_path(assets_root, asset["path"])
                if resolved.is_file() and SHA256_RE.fullmatch(str(digest or "")):
                    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
                    if actual != digest:
                        add(findings, "asset_digest_mismatch", relative, child(asset_location, "sha256"), f"Expected {digest}, found {actual}.")
        if kind == "inline":
            encoding = asset.get("encoding")
            data = asset.get("data")
            if encoding not in {"base64", "utf8"}:
                add(findings, "invalid_inline_encoding", relative, child(asset_location, "encoding"), "encoding must be base64 or utf8.")
            if not isinstance(data, str):
                add(findings, "invalid_inline_data", relative, child(asset_location, "data"), "data must be a string.")
            elif encoding in {"base64", "utf8"} and SHA256_RE.fullmatch(str(asset.get("sha256") or "")):
                try:
                    raw = base64.b64decode(data, validate=True) if encoding == "base64" else data.encode("utf-8")
                except (binascii.Error, ValueError):
                    add(findings, "invalid_inline_data", relative, child(asset_location, "data"), "data does not match its declared encoding.")
                else:
                    actual = hashlib.sha256(raw).hexdigest()
                    if actual != asset.get("sha256"):
                        add(findings, "asset_digest_mismatch", relative, child(asset_location, "sha256"), f"Expected {asset.get('sha256')}, found {actual}.")
        if kind == "generated":
            if asset.get("command_id") not in commands:
                add(findings, "unknown_asset_command", relative, child(asset_location, "command_id"), f"Unknown command {asset.get('command_id')!r}.")
            if not isinstance(asset.get("seed"), int) or isinstance(asset.get("seed"), bool):
                add(findings, "invalid_generated_seed", relative, child(asset_location, "seed"), "seed must be an integer.")
        if kind == "builtin" and not non_empty_string(asset.get("name")):
            add(findings, "invalid_builtin_name", relative, child(asset_location, "name"), "name must be non-empty.")
        if kind == "remote_mock":
            if asset.get("command_id") not in commands:
                add(findings, "unknown_asset_command", relative, child(asset_location, "command_id"), f"Unknown command {asset.get('command_id')!r}.")
            endpoint = asset.get("endpoint")
            if not non_empty_string(endpoint) or not re.match(r"^https?://(?:127\.0\.0\.1|localhost)(?::\d+)?(?:/|$)", endpoint):
                add(findings, "invalid_mock_endpoint", relative, child(asset_location, "endpoint"), "remote_mock endpoint must be deterministic localhost HTTP(S).")
    return asset_ids


def validate_workflow(
    assets: Any,
    steps: Any,
    observations: Any,
    target_profiles: set[str],
    manifest_index: dict[str, Any],
    assets_root: Path,
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    asset_ids = validate_assets(
        assets,
        set(manifest_index["commands"]),
        assets_root,
        relative,
        child(location, "assets"),
        findings,
    )
    if not isinstance(steps, list) or not steps:
        add(findings, "invalid_steps", relative, child(location, "steps"), "steps must be a non-empty array.")
        steps = []
    step_ids: set[str] = set()
    ordered_steps: set[str] = set()
    step_operations: dict[str, tuple[str, str]] = {}
    for position, step_value in enumerate(steps):
        step_location = child(child(location, "steps"), position)
        step = exact_object(step_value, {"step_id", "surface", "operation", "receiver", "arguments"}, set(), relative, step_location, findings)
        if step is None:
            continue
        step_id = validate_id(step.get("step_id"), relative, child(step_location, "step_id"), findings)
        if step_id in step_ids:
            add(findings, "duplicate_step_id", relative, child(step_location, "step_id"), f"Duplicate step {step_id!r}.")
        elif step_id is not None:
            step_ids.add(step_id)
        surface = step.get("surface")
        operation = step.get("operation")
        operation_spec = manifest_index["operations"].get((surface, operation))
        if operation_spec is None:
            add(findings, "unknown_step_operation", relative, step_location, f"Unknown manifest operation {surface!r}.{operation!r}.")
            parameters: dict[str, dict[str, Any]] = {}
        else:
            parameters = operation_spec["parameters"]
            for profile in target_profiles:
                target_id = manifest_index["profile_targets"].get(profile)
                if target_id is not None and target_id not in operation_spec["target_ids"]:
                    add(findings, "step_missing_target_binding", relative, step_location, f"Step operation has no target binding for profile {profile!r}.")
        receiver_parameters = [parameter for parameter in parameters.values() if parameter.get("style") == "receiver"]
        receiver = step.get("receiver")
        if receiver_parameters:
            if receiver is None:
                add(findings, "missing_step_receiver", relative, child(step_location, "receiver"), "Operation declares a receiver.")
            else:
                validate_value_descriptor(receiver, set(receiver_parameters[0].get("value_types") or []), asset_ids, ordered_steps, relative, child(step_location, "receiver"), findings)
        elif receiver is not None:
            add(findings, "unexpected_step_receiver", relative, child(step_location, "receiver"), "Operation does not declare a receiver.")
            validate_value_descriptor(receiver, None, asset_ids, ordered_steps, relative, child(step_location, "receiver"), findings)
        arguments = step.get("arguments")
        if not isinstance(arguments, dict):
            add(findings, "invalid_step_arguments", relative, child(step_location, "arguments"), "arguments must be an object keyed by declared parameter ID.")
            arguments = {}
        argument_names = set(arguments)
        receiver_names = {parameter_id for parameter_id, parameter in parameters.items() if parameter.get("style") == "receiver"}
        unknown = argument_names - set(parameters)
        if unknown:
            add(findings, "unknown_step_argument", relative, child(step_location, "arguments"), f"Unknown operation parameters: {sorted(unknown)}.")
        if argument_names & receiver_names:
            add(findings, "receiver_in_arguments", relative, child(step_location, "arguments"), "Receiver must use the receiver field, not arguments.")
        missing = {
            parameter_id
            for parameter_id, parameter in parameters.items()
            if (
                isinstance(parameter.get("omission"), dict)
                and parameter["omission"].get("kind") == "required"
            )
            and parameter.get("style") != "receiver"
            and parameter_id not in argument_names
        }
        if missing:
            add(findings, "missing_required_argument", relative, child(step_location, "arguments"), f"Missing required parameters: {sorted(missing)}.")
        for argument_name, argument_value in arguments.items():
            parameter = parameters.get(argument_name)
            expected_types = set(parameter.get("value_types") or []) if parameter else None
            validate_value_descriptor(argument_value, expected_types, asset_ids, ordered_steps, relative, child(child(step_location, "arguments"), argument_name), findings)
        if step_id is not None:
            ordered_steps.add(step_id)
            if isinstance(surface, str) and isinstance(operation, str):
                step_operations[step_id] = (surface, operation)

    if not unique_string_list(observations, non_empty=True):
        add(findings, "invalid_workflow_observations", relative, child(location, "observations"), "observations must be a non-empty unique step-ID array.")
        observations = []
    unknown_observations = set(observations) - step_ids
    if unknown_observations:
        add(findings, "unknown_observation_step", relative, child(location, "observations"), f"Unknown observed steps: {sorted(unknown_observations)}.")
    return {
        "step_ids": step_ids,
        "observations": set(observations),
        "step_operations": step_operations,
    }


def validate_covers(
    values: Any,
    lane: str,
    manifest_index: dict[str, Any],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
    *,
    operation: tuple[str, str] | None = None,
    profiles: set[str] | None = None,
) -> set[str]:
    if not unique_string_list(values, non_empty=True):
        add(findings, "invalid_covers", relative, location, "covers must be a non-empty unique requirement-ID array.")
        return set()
    valid: set[str] = set()
    for requirement_id in values:
        requirement = manifest_index["requirements"].get(requirement_id)
        if requirement is None:
            add(findings, "unknown_requirement", relative, location, f"Unknown requirement {requirement_id!r}.")
            continue
        if lane not in requirement["lanes"]:
            add(findings, "cross_lane_requirement", relative, location, f"Requirement {requirement_id!r} does not include {lane}.")
            continue
        if operation is not None and requirement["operation"] != operation:
            add(findings, "cross_operation_requirement", relative, location, f"Requirement {requirement_id!r} belongs to {requirement['operation']}.")
            continue
        if profiles is not None:
            missing = profiles - requirement["profiles"]
            if missing:
                add(findings, "requirement_profile_mismatch", relative, location, f"Requirement {requirement_id!r} does not apply to profiles {sorted(missing)}.")
                continue
        valid.add(requirement_id)
    return valid


def inspect_parity_file(
    path: Path,
    root: Path,
    manifest_root: Path,
    manifest_index: dict[str, Any],
    seen_ids: dict[str, str],
    parity_cases: dict[str, dict[str, Any]],
    mapped: dict[str, dict[str, set[str]]],
    findings: list[dict[str, str]],
) -> int:
    payload = load_document(path, root, findings, yaml_allowed=False)
    relative = path.relative_to(root).as_posix()
    document = exact_object(payload, {"schema", "cases"}, set(), relative, "$", findings)
    if document is None:
        return 0
    schema_valid = document.get("schema") == INPUT_SCHEMAS["parity"]
    if not schema_valid:
        add(findings, "invalid_parity_schema", relative, "$.schema", f"Expected {INPUT_SCHEMAS['parity']!r}.")
    cases = document.get("cases")
    if not isinstance(cases, list):
        add(findings, "invalid_cases", relative, "$.cases", "cases must be an array.")
        return 0
    count = 0
    for position, case_value in enumerate(cases):
        location = f"$.cases[{position}]"
        item_finding_start = len(findings)
        case = exact_object(case_value, {"case_id", "surface", "operation", "covers", "target_profiles", "assets", "steps", "observations"}, set(), relative, location, findings)
        if case is None:
            continue
        case_id = validate_stable_id(case.get("case_id"), relative, child(location, "case_id"), findings)
        register(seen_ids, case_id, relative, "case", relative, child(location, "case_id"), findings)
        surface = case.get("surface")
        operation = case.get("operation")
        operation_key = (surface, operation)
        operation_spec = manifest_index["operations"].get(operation_key)
        if operation_spec is None:
            add(findings, "unknown_case_operation", relative, location, f"Unknown manifest operation {surface!r}.{operation!r}.")
        if case_id is not None and isinstance(surface, str) and isinstance(operation, str) and not case_id.startswith(f"{surface}.{operation}."):
            add(findings, "case_id_prefix_mismatch", relative, child(location, "case_id"), "case_id must start with the canonical surface and operation.")
        profiles_value = case.get("target_profiles")
        if not unique_string_list(profiles_value, non_empty=True):
            add(findings, "invalid_case_profiles", relative, child(location, "target_profiles"), "target_profiles must be a non-empty unique array.")
            profiles_value = []
        profiles = set(profiles_value)
        unknown_profiles = profiles - set(manifest_index["profiles"])
        if unknown_profiles:
            add(findings, "unknown_case_profile", relative, child(location, "target_profiles"), f"Unknown profiles: {sorted(unknown_profiles)}.")
        if operation_spec is not None:
            lane = operation_spec["lanes"]["parity"]
            if lane["applicability"] != "required":
                add(findings, "case_for_inapplicable_parity", relative, location, "Case targets a parity-not-applicable operation.")
            outside = profiles - lane["profiles"]
            if outside:
                add(findings, "case_profile_outside_lane", relative, child(location, "target_profiles"), f"Profiles not selected by operation parity: {sorted(outside)}.")
        covers = validate_covers(case.get("covers"), "parity", manifest_index, relative, child(location, "covers"), findings, profiles=profiles)
        workflow = validate_workflow(case.get("assets"), case.get("steps"), case.get("observations"), profiles, manifest_index, manifest_root / "assets", relative, location, findings)
        observed_operations = {workflow["step_operations"].get(step_id) for step_id in workflow["observations"]}
        if operation_key not in observed_operations:
            add(findings, "primary_operation_not_observed", relative, child(location, "observations"), "At least one observed step must call the case surface and operation.")
        for requirement_id in covers:
            requirement = manifest_index["requirements"].get(requirement_id)
            if requirement is not None and requirement["operation"] not in observed_operations:
                add(
                    findings,
                    "covered_operation_not_observed",
                    relative,
                    child(location, "covers"),
                    f"Requirement {requirement_id!r} belongs to an operation with no observed step.",
                )
        if case_id is not None:
            parity_cases[case_id] = {
                "operation": operation_key,
                "profiles": profiles,
                "observations": workflow["observations"],
                "step_operations": workflow["step_operations"],
                "covers": covers,
            }
        if schema_valid and len(findings) == item_finding_start:
            for requirement_id in covers:
                mapped["parity"][requirement_id].update(profiles)
        count += 1
    return count


def inspect_coverage_file(
    path: Path,
    root: Path,
    manifest_index: dict[str, Any],
    seen_ids: dict[str, str],
    parity_cases: dict[str, dict[str, Any]],
    mapped: dict[str, dict[str, set[str]]],
    findings: list[dict[str, str]],
) -> int:
    payload = load_document(path, root, findings, yaml_allowed=False)
    relative = path.relative_to(root).as_posix()
    document = exact_object(payload, {"schema", "plans"}, set(), relative, "$", findings)
    if document is None:
        return 0
    schema_valid = document.get("schema") == INPUT_SCHEMAS["coverage"]
    if not schema_valid:
        add(findings, "invalid_coverage_schema", relative, "$.schema", f"Expected {INPUT_SCHEMAS['coverage']!r}.")
    plans = document.get("plans")
    if not isinstance(plans, list):
        add(findings, "invalid_plans", relative, "$.plans", "plans must be an array.")
        return 0
    count = 0
    for position, plan_value in enumerate(plans):
        location = f"$.plans[{position}]"
        item_finding_start = len(findings)
        plan = exact_object(plan_value, {"plan_id", "covers", "target_profile", "selectors", "component_ids", "command_id"}, set(), relative, location, findings)
        if plan is None:
            continue
        plan_id = validate_stable_id(plan.get("plan_id"), relative, child(location, "plan_id"), findings)
        register(seen_ids, plan_id, relative, "plan", relative, child(location, "plan_id"), findings)
        profile = plan.get("target_profile")
        if profile not in manifest_index["profiles"]:
            add(findings, "unknown_plan_profile", relative, child(location, "target_profile"), f"Unknown target profile {profile!r}.")
        covers = validate_covers(plan.get("covers"), "coverage", manifest_index, relative, child(location, "covers"), findings, profiles={profile} if isinstance(profile, str) else set())
        selectors = exact_object(plan.get("selectors"), {"parity_case_ids", "command_ids"}, set(), relative, child(location, "selectors"), findings)
        selected_case_covers: set[str] = set()
        if selectors is not None:
            case_ids = selectors.get("parity_case_ids")
            command_ids = selectors.get("command_ids")
            if not unique_string_list(case_ids) or not unique_string_list(command_ids):
                add(findings, "invalid_coverage_selectors", relative, child(location, "selectors"), "Selector values must be unique string arrays.")
                case_ids = []
                command_ids = []
            if not case_ids and not command_ids:
                add(findings, "empty_coverage_selectors", relative, child(location, "selectors"), "Coverage plan must select parity cases and/or commands.")
            for case_id in case_ids:
                case = parity_cases.get(case_id)
                if case is None:
                    add(findings, "unknown_coverage_case", relative, child(child(location, "selectors"), "parity_case_ids"), f"Unknown parity case {case_id!r}.")
                elif profile not in case["profiles"]:
                    add(findings, "coverage_case_profile_mismatch", relative, child(child(location, "selectors"), "parity_case_ids"), f"Parity case {case_id!r} does not select profile {profile!r}.")
                else:
                    selected_case_covers.update(case["covers"])
            unknown_commands = set(command_ids) - set(manifest_index["commands"])
            if unknown_commands:
                add(findings, "unknown_coverage_selector_command", relative, child(child(location, "selectors"), "command_ids"), f"Unknown commands: {sorted(unknown_commands)}.")
            if not command_ids:
                unexercised = covers - selected_case_covers
                if unexercised:
                    add(
                        findings,
                        "coverage_requirement_not_selected",
                        relative,
                        child(location, "covers"),
                        f"Requirements are not covered by any selected parity case: {sorted(unexercised)}.",
                    )
        component_ids = plan.get("component_ids")
        if not unique_string_list(component_ids, non_empty=True):
            add(findings, "invalid_plan_components", relative, child(location, "component_ids"), "component_ids must be a non-empty unique array.")
            component_ids = []
        for component_id in component_ids:
            component = manifest_index["components"].get(component_id)
            if component is None:
                add(findings, "unknown_plan_component", relative, child(location, "component_ids"), f"Unknown component {component_id!r}.")
            elif component.get("target_profile") != profile:
                add(findings, "component_profile_mismatch", relative, child(location, "component_ids"), f"Component {component_id!r} belongs to profile {component.get('target_profile')!r}.")
        for requirement_id in covers:
            requirement = manifest_index["requirements"].get(requirement_id)
            if requirement is None:
                continue
            operation = manifest_index["operations"].get(requirement["operation"])
            if operation is None:
                continue
            undeclared_components = set(component_ids) - operation["lanes"]["coverage"]["component_ids"]
            if undeclared_components:
                add(
                    findings,
                    "plan_component_outside_operation",
                    relative,
                    child(location, "component_ids"),
                    f"Components not declared by {requirement['operation']}: "
                    f"{sorted(undeclared_components)}.",
                )
        if plan.get("command_id") not in manifest_index["commands"]:
            add(findings, "unknown_plan_command", relative, child(location, "command_id"), f"Unknown command {plan.get('command_id')!r}.")
        if schema_valid and len(findings) == item_finding_start and isinstance(profile, str):
            for requirement_id in covers:
                mapped["coverage"][requirement_id].add(profile)
        count += 1
    return count


def validate_measurement(
    value: Any,
    input_kind: Any,
    workflow_observations: set[str],
    relative: str,
    location: str,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    measurement = exact_object(
        value,
        {"boundary", "step_ids", "metrics", "warmup_iterations", "measurement_iterations", "samples", "concurrency", "cache_state", "correctness_gate"},
        set(),
        relative,
        location,
        findings,
    )
    if measurement is None:
        return {}
    boundary = measurement.get("boundary")
    if boundary not in MEASUREMENT_BOUNDARIES:
        add(findings, "invalid_measurement_boundary", relative, child(location, "boundary"), f"boundary must be one of {sorted(MEASUREMENT_BOUNDARIES)}.")
    step_ids = measurement.get("step_ids")
    if not unique_string_list(step_ids):
        add(findings, "invalid_measurement_steps", relative, child(location, "step_ids"), "step_ids must be a unique string array.")
        step_ids = []
    if boundary == "observed_steps":
        if not step_ids:
            add(findings, "missing_measurement_steps", relative, child(location, "step_ids"), "observed_steps boundary requires step IDs.")
        unknown = set(step_ids) - workflow_observations
        if unknown:
            add(findings, "unknown_measurement_step", relative, child(location, "step_ids"), f"Unknown observed steps: {sorted(unknown)}.")
    elif step_ids:
        add(findings, "unexpected_measurement_steps", relative, child(location, "step_ids"), "Only observed_steps boundary accepts step_ids.")
    if boundary == "process" and input_kind != "command":
        add(findings, "process_boundary_input_mismatch", relative, child(location, "boundary"), "process boundary requires command input.")
    if boundary == "artifact" and input_kind != "artifact":
        add(findings, "artifact_boundary_input_mismatch", relative, child(location, "boundary"), "artifact boundary requires artifact input.")
    metrics = measurement.get("metrics")
    if not unique_string_list(metrics, non_empty=True) or not set(metrics or []).issubset(BENCHMARK_METRICS):
        add(findings, "invalid_measurement_metrics", relative, child(location, "metrics"), f"metrics must be a non-empty subset of {sorted(BENCHMARK_METRICS)}.")
    for field in ("warmup_iterations", "measurement_iterations", "samples", "concurrency"):
        measured = measurement.get(field)
        minimum = 0 if field == "warmup_iterations" else 1
        if not isinstance(measured, int) or isinstance(measured, bool) or measured < minimum:
            add(findings, "invalid_measurement_count", relative, child(location, field), f"{field} must be an integer >= {minimum}.")
    if measurement.get("cache_state") not in CACHE_STATES:
        add(findings, "invalid_cache_state", relative, child(location, "cache_state"), f"cache_state must be one of {sorted(CACHE_STATES)}.")
    gate = measurement.get("correctness_gate")
    if gate not in CORRECTNESS_GATES:
        add(findings, "invalid_correctness_gate", relative, child(location, "correctness_gate"), f"correctness_gate must be one of {sorted(CORRECTNESS_GATES)}.")
    if gate == "not_applicable" and not (input_kind == "artifact" and boundary == "artifact"):
        add(findings, "invalid_not_applicable_gate", relative, child(location, "correctness_gate"), "not_applicable is valid only for artifact measurement.")
    if gate == "parity_pass" and input_kind != "parity_case":
        add(findings, "parity_gate_input_mismatch", relative, child(location, "correctness_gate"), "parity_pass requires parity_case input.")
    return measurement


def inspect_benchmark_file(
    path: Path,
    root: Path,
    manifest_root: Path,
    manifest_index: dict[str, Any],
    seen_ids: dict[str, str],
    parity_cases: dict[str, dict[str, Any]],
    mapped: dict[str, dict[str, set[str]]],
    findings: list[dict[str, str]],
) -> tuple[int, int]:
    payload = load_document(path, root, findings, yaml_allowed=False)
    relative = path.relative_to(root).as_posix()
    document = exact_object(payload, {"schema", "workloads", "suites"}, set(), relative, "$", findings)
    if document is None:
        return 0, 0
    schema_valid = document.get("schema") == INPUT_SCHEMAS["benchmark"]
    if not schema_valid:
        add(findings, "invalid_benchmark_schema", relative, "$.schema", f"Expected {INPUT_SCHEMAS['benchmark']!r}.")
    workloads = document.get("workloads")
    suites = document.get("suites")
    if not isinstance(workloads, list):
        add(findings, "invalid_workloads", relative, "$.workloads", "workloads must be an array.")
        workloads = []
    if not isinstance(suites, list):
        add(findings, "invalid_suites", relative, "$.suites", "suites must be an array.")
        suites = []
    workload_ids: set[str] = set()
    for position, workload_value in enumerate(workloads):
        location = f"$.workloads[{position}]"
        item_finding_start = len(findings)
        workload = exact_object(workload_value, {"workload_id", "covers", "subjects", "input", "measurement"}, set(), relative, location, findings)
        if workload is None:
            continue
        workload_id = validate_stable_id(workload.get("workload_id"), relative, child(location, "workload_id"), findings)
        register(seen_ids, workload_id, relative, "workload", relative, child(location, "workload_id"), findings)
        if workload_id is not None:
            workload_ids.add(workload_id)
        subjects = workload.get("subjects")
        subject_pairs: set[tuple[str, str]] = set()
        target_profiles: set[str] = set()
        if not isinstance(subjects, list) or not subjects:
            add(findings, "invalid_benchmark_subjects", relative, child(location, "subjects"), "subjects must be a non-empty array.")
            subjects = []
        for subject_position, subject_value in enumerate(subjects):
            subject_location = child(child(location, "subjects"), subject_position)
            subject = exact_object(subject_value, {"kind", "id"}, set(), relative, subject_location, findings)
            if subject is None:
                continue
            kind = subject.get("kind")
            subject_id = subject.get("id")
            pair = (kind, subject_id)
            if pair in subject_pairs:
                add(findings, "duplicate_benchmark_subject", relative, subject_location, f"Duplicate subject {pair!r}.")
            else:
                subject_pairs.add(pair)
            if kind == "oracle":
                if subject_id not in manifest_index["oracles"]:
                    add(findings, "unknown_benchmark_oracle", relative, child(subject_location, "id"), f"Unknown oracle {subject_id!r}.")
            elif kind == "target_profile":
                if subject_id not in manifest_index["profiles"]:
                    add(findings, "unknown_benchmark_profile", relative, child(subject_location, "id"), f"Unknown target profile {subject_id!r}.")
                elif isinstance(subject_id, str):
                    target_profiles.add(subject_id)
            else:
                add(findings, "invalid_benchmark_subject_kind", relative, child(subject_location, "kind"), "Subject kind must be oracle or target_profile.")
        if not target_profiles:
            add(findings, "benchmark_without_target_subject", relative, child(location, "subjects"), "Benchmark requires at least one target_profile subject.")
        covers = validate_covers(workload.get("covers"), "benchmark", manifest_index, relative, child(location, "covers"), findings, profiles=target_profiles)

        input_value = workload.get("input")
        if not isinstance(input_value, dict):
            add(findings, "invalid_benchmark_input", relative, child(location, "input"), "input must be a fixed variant object.")
            input_value = {}
        input_kind = input_value.get("kind")
        workflow_observations: set[str] = set()
        workflow_step_operations: dict[str, tuple[str, str]] = {}
        parity_case_covers: set[str] | None = None
        if input_kind == "parity_case":
            exact_object(input_value, {"kind", "case_id"}, set(), relative, child(location, "input"), findings)
            case = parity_cases.get(input_value.get("case_id"))
            if case is None:
                add(findings, "unknown_benchmark_case", relative, child(child(location, "input"), "case_id"), f"Unknown parity case {input_value.get('case_id')!r}.")
            else:
                workflow_observations = case["observations"]
                workflow_step_operations = case["step_operations"]
                parity_case_covers = case["covers"]
                outside = target_profiles - case["profiles"]
                if outside:
                    add(findings, "benchmark_case_profile_mismatch", relative, child(child(location, "input"), "case_id"), f"Parity case does not select profiles {sorted(outside)}.")
        elif input_kind == "workflow":
            exact_object(input_value, {"kind", "assets", "steps", "observations"}, set(), relative, child(location, "input"), findings)
            workflow = validate_workflow(input_value.get("assets"), input_value.get("steps"), input_value.get("observations"), target_profiles, manifest_index, manifest_root / "assets", relative, child(location, "input"), findings)
            workflow_observations = workflow["observations"]
            workflow_step_operations = workflow["step_operations"]
        elif input_kind == "command":
            exact_object(input_value, {"kind", "command_id"}, set(), relative, child(location, "input"), findings)
            if input_value.get("command_id") not in manifest_index["commands"]:
                add(findings, "unknown_benchmark_command", relative, child(child(location, "input"), "command_id"), f"Unknown command {input_value.get('command_id')!r}.")
        elif input_kind == "artifact":
            exact_object(input_value, {"kind", "path"}, set(), relative, child(location, "input"), findings)
            validate_relative_path(input_value.get("path"), relative, child(child(location, "input"), "path"), findings)
        else:
            exact_object(input_value, {"kind"}, set(), relative, child(location, "input"), findings)
            add(findings, "invalid_benchmark_input_kind", relative, child(child(location, "input"), "kind"), "Input kind must be parity_case, workflow, command, or artifact.")
        measurement = validate_measurement(workload.get("measurement"), input_kind, workflow_observations, relative, child(location, "measurement"), findings)
        measured_metrics = set(measurement.get("metrics", []))
        if parity_case_covers is not None:
            unbacked = covers - parity_case_covers
            if unbacked:
                add(
                    findings,
                    "benchmark_requirement_not_in_case",
                    relative,
                    child(location, "covers"),
                    f"Requirements are not covered by the selected parity case: {sorted(unbacked)}.",
                )
        measured_step_ids = (
            set(measurement.get("step_ids", []))
            if measurement.get("boundary") == "observed_steps"
            else set(workflow_step_operations)
        )
        measured_operations = {
            workflow_step_operations[step_id]
            for step_id in measured_step_ids
            if step_id in workflow_step_operations
        }
        for requirement_id in covers:
            requirement = manifest_index["requirements"].get(requirement_id)
            if requirement is None:
                continue
            if workflow_step_operations and requirement["operation"] not in measured_operations:
                add(
                    findings,
                    "benchmark_operation_not_measured",
                    relative,
                    child(location, "covers"),
                    f"Requirement {requirement_id!r} belongs to an operation outside the measurement boundary.",
                )
            operation = manifest_index["operations"].get(requirement["operation"])
            if operation is not None:
                benchmark_lane = operation["lanes"]["benchmark"]
                if benchmark_lane["applicability"] != "required":
                    add(findings, "workload_for_inapplicable_benchmark", relative, location, f"Requirement {requirement_id!r} belongs to non-applicable benchmark.")
                undeclared_metrics = measured_metrics - benchmark_lane["metrics"]
                if undeclared_metrics:
                    add(
                        findings,
                        "workload_metric_outside_operation",
                        relative,
                        child(location, "measurement"),
                        f"Metrics not declared by {requirement['operation']}: "
                        f"{sorted(undeclared_metrics)}.",
                    )
                budget = requirement.get("budget")
                if (
                    isinstance(budget, dict)
                    and budget.get("metric") not in measured_metrics
                ):
                    add(
                        findings,
                        "budget_metric_not_measured",
                        relative,
                        child(location, "measurement"),
                        f"Requirement {requirement_id!r} budget metric "
                        f"{budget.get('metric')!r} is not measured.",
                    )
        if schema_valid and len(findings) == item_finding_start:
            for requirement_id in covers:
                mapped["benchmark"][requirement_id].update(target_profiles)

    suite_ids: set[str] = set()
    for position, suite_value in enumerate(suites):
        location = f"$.suites[{position}]"
        suite = exact_object(suite_value, {"suite_id", "description", "members"}, set(), relative, location, findings)
        if suite is None:
            continue
        suite_id = validate_stable_id(suite.get("suite_id"), relative, child(location, "suite_id"), findings)
        register(seen_ids, suite_id, relative, "suite", relative, child(location, "suite_id"), findings)
        if suite_id in suite_ids:
            add(findings, "duplicate_suite_id", relative, child(location, "suite_id"), f"Duplicate suite {suite_id!r}.")
        elif suite_id is not None:
            suite_ids.add(suite_id)
        if not non_empty_string(suite.get("description")):
            add(findings, "invalid_suite_description", relative, child(location, "description"), "description must be non-empty.")
        members = suite.get("members")
        if not isinstance(members, list) or not members:
            add(findings, "invalid_suite_members", relative, child(location, "members"), "members must be a non-empty array.")
            members = []
        member_ids: set[str] = set()
        for member_position, member_value in enumerate(members):
            member_location = child(child(location, "members"), member_position)
            member = exact_object(member_value, {"workload_id", "weight"}, set(), relative, member_location, findings)
            if member is None:
                continue
            member_id = member.get("workload_id")
            if member_id not in workload_ids:
                add(findings, "unknown_suite_workload", relative, child(member_location, "workload_id"), f"Unknown workload {member_id!r} in this document.")
            if member_id in member_ids:
                add(findings, "duplicate_suite_member", relative, child(member_location, "workload_id"), f"Duplicate suite workload {member_id!r}.")
            elif isinstance(member_id, str):
                member_ids.add(member_id)
            weight = member.get("weight")
            if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
                add(findings, "invalid_suite_weight", relative, child(member_location, "weight"), "weight must be positive.")
    return len(workloads), len(suites)


def build_report(root: Path, manifest_relative: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    manifest_path = root / manifest_relative
    manifest_root = manifest_path.parent
    if not manifest_path.is_file():
        add(findings, "missing_manifest", manifest_relative, "$", "Active migration manifest is missing.")
    manifests = sorted(manifest_root.rglob("manifest.yaml")) if manifest_root.exists() else []
    if manifest_path.name == "manifest.yaml" and len(manifests) > 1:
        add(findings, "multiple_active_manifests", manifest_root.relative_to(root).as_posix(), "$", "More than one manifest.yaml exists beneath the active manifest root.")

    index: dict[str, Any] = {
        "mode": None,
        "commands": {},
        "oracles": {},
        "targets": {},
        "profiles": {},
        "profile_targets": {},
        "components": {},
        "operations": {},
        "requirements": {},
        "input_paths": {lane: {} for lane in LANES},
        "documentation_outputs": 0,
        "endpoint_count": 0,
        "complete_endpoint_count": 0,
        "operation_count": 0,
    }
    if manifest_path.is_file():
        payload = load_document(manifest_path, root, findings, yaml_allowed=True)
        if payload is not None:
            index = validate_manifest(payload, root, manifest_path, findings)

    lane_files: dict[str, list[Path]] = {}
    for lane in LANES:
        lane_root = manifest_root / "inputs" / lane
        lane_files[lane] = sorted(lane_root.rglob("*.json")) if lane_root.exists() else []
        discovered = {path.relative_to(manifest_root).as_posix() for path in lane_files[lane]}
        declared = set(index["input_paths"][lane])
        for path_value in sorted(declared - discovered):
            add(findings, "missing_indexed_input", manifest_relative, f"$.input_index.{lane}", f"Indexed input does not exist: {path_value}.")
        for path_value in sorted(discovered - declared):
            add(findings, "unindexed_input_file", (manifest_root / path_value).relative_to(root).as_posix(), "$", f"Discovered {lane} input is absent from input_index.")

    inputs_root = manifest_root / "inputs"
    recognized = {path.resolve() for files in lane_files.values() for path in files}
    if inputs_root.exists():
        for path in sorted(inputs_root.rglob("*.json")):
            if path.resolve() not in recognized:
                add(findings, "unknown_input_lane", path.relative_to(root).as_posix(), "$", "Input JSON must live beneath parity, coverage, or benchmark.")

    seen_ids: dict[str, str] = {}
    parity_cases: dict[str, dict[str, Any]] = {}
    mapped: dict[str, dict[str, set[str]]] = {
        lane: defaultdict(set) for lane in LANES
    }
    counts = Counter()
    for path in lane_files["parity"]:
        counts["parity"] += inspect_parity_file(path, root, manifest_root, index, seen_ids, parity_cases, mapped, findings)
    for path in lane_files["coverage"]:
        counts["coverage"] += inspect_coverage_file(path, root, index, seen_ids, parity_cases, mapped, findings)
    for path in lane_files["benchmark"]:
        workload_count, suite_count = inspect_benchmark_file(path, root, manifest_root, index, seen_ids, parity_cases, mapped, findings)
        counts["benchmark"] += workload_count
        counts["suite"] += suite_count

    requirement_totals = Counter()
    mapping_counts = Counter()
    for requirement_id, requirement in index["requirements"].items():
        for lane in requirement["lanes"]:
            requirement_totals[lane] += 1
            missing_profiles = requirement["profiles"] - mapped[lane][requirement_id]
            if not missing_profiles:
                mapping_counts[lane] += 1
            else:
                add(
                    findings,
                    "unmapped_requirement",
                    manifest_relative,
                    requirement["location"],
                    f"Requirement {requirement_id!r} lacks {lane} input mapping "
                    f"for profiles {sorted(missing_profiles)}.",
                )

    findings.sort(
        key=lambda item: (
            {"error": 0, "review": 1, "info": 2}[item["severity"]],
            item["path"],
            item["location"],
            item["code"],
        )
    )
    finding_counts = Counter(item["severity"] for item in findings)
    return {
        "schema": "migration-parity/static-audit@2",
        "root": str(root),
        "manifest": manifest_relative if manifest_path.is_file() else None,
        "summary": {
            "errors": finding_counts["error"],
            "review": finding_counts["review"],
            "info": finding_counts["info"],
        },
        "inventory": {
            "scope_mode": index["mode"],
            "oracles": len(index["oracles"]),
            "targets": len(index["targets"]),
            "target_profiles": len(index["profiles"]),
            "surfaces": len({surface for surface, _ in index["operations"]}),
            "operations": index["operation_count"],
            "endpoints": index["endpoint_count"],
            "requirements": len(index["requirements"]),
            "coverage_components": len(index["components"]),
            "input_files": {lane: len(lane_files[lane]) for lane in LANES},
            "items": {
                "parity_cases": counts["parity"],
                "coverage_plans": counts["coverage"],
                "benchmark_workloads": counts["benchmark"],
                "benchmark_suites": counts["suite"],
            },
            "documentation_outputs": index["documentation_outputs"],
        },
        "specification_completeness": {
            "operation_contracts": {
                "numerator": index["complete_endpoint_count"],
                "denominator": index["endpoint_count"],
            },
            "input_mapping": {
                lane: {
                    "numerator": mapping_counts[lane],
                    "denominator": requirement_totals[lane],
                }
                for lane in LANES
            },
        },
        "findings": findings,
        "limits": [
            "Static validation cannot prove the authority-defined inventory count.",
            "Static validation cannot prove repository-native runner registry bijection.",
            "Static validation does not execute oracles, targets, managed coverage, or benchmarks.",
            "Static validation does not validate generated lane results, aggregation compatibility, or documentation freshness.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    inventory = report["inventory"]
    summary = report["summary"]
    print("Migration parity specification audit")
    print(f"Manifest: {report['manifest'] or 'missing'}")
    print(f"Scope: {inventory['scope_mode'] or 'unknown'}")
    print(
        "Contract: "
        f"{inventory['operations']} operations, "
        f"{inventory['requirements']} requirements, "
        f"{inventory['target_profiles']} target profiles"
    )
    items = inventory["items"]
    print(
        "Inputs: "
        f"{items['parity_cases']} parity cases, "
        f"{items['coverage_plans']} coverage plans, "
        f"{items['benchmark_workloads']} benchmark workloads, "
        f"{items['benchmark_suites']} benchmark suites"
    )
    for lane, fraction in report["specification_completeness"]["input_mapping"].items():
        print(f"{lane.capitalize()} input mapping: {fraction['numerator']}/{fraction['denominator']}")
    print(f"Findings: {summary['errors']} error(s), {summary['review']} review item(s)")
    for item in report["findings"]:
        print(f"- {item['severity'].upper()} {item['code']} {item['path']} {item['location']} — {item['message']}")
    print("Static validation does not prove live parity, coverage, benchmarks, result compatibility, or documentation freshness.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a fixed migration parity manifest and its indexed inputs.")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--manifest", default="tests/fixtures/manifest.yaml", help="Repository-relative active manifest path.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Return 1 when error findings exist.")
    args = parser.parse_args()

    root = args.repository.resolve()
    if not root.is_dir():
        print("error: repository is not a directory", file=sys.stderr)
        return 2
    if not safe_relative_path(args.manifest):
        print("error: --manifest must be repository-relative", file=sys.stderr)
        return 2
    report = build_report(root, args.manifest)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
