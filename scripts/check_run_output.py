#!/usr/bin/env python3
"""Validate cross-agent runtime invariants for a product-dev-bus run output."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


E2E_SCOPES = {"full", "e2e", "e2e-only"}
RESOLVED_STATUSES = {"accepted", "resolved", "superseded"}
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"
AGENT_OUTPUTS = {
    "architect-agent": "architect_output",
    "pm-agent": "pm_output",
    "data-agent": "data_output",
    "backend-agent": "backend_output",
    "frontend-agent": "frontend_output",
    "qa-agent": "qa_output",
}
DISPATCH_AGENTS = {
    "data-agent": "data",
    "backend-agent": "backend",
    "frontend-agent": "frontend",
    "qa-agent": "qa",
}


def fail(message: str) -> None:
    print(f"check_run_output: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"run output must be a JSON object: {path}")
    return data


def load_schema(path: Path) -> dict[str, Any]:
    return load_json(path)


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{path} must be an object")
    return value


def optional_object(root: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = root.get(key)
    if value is None:
        return None
    return require_object(value, key)


def contract_version(contract: Any, path: str) -> str | None:
    if contract is None:
        return None
    obj = require_object(contract, path)
    version = obj.get("contract_version")
    if version is None:
        fail(f"{path}.contract_version is required")
    return str(version)


def validate_run_schema(run: dict[str, Any]) -> None:
    schema = load_schema(SCHEMA_ROOT / "run_output.schema.json")
    validate_json_schema(run, schema, "$", SCHEMA_ROOT / "run_output.schema.json")


def validate_json_schema(value: Any, schema: dict[str, Any], path: str, schema_path: Path) -> None:
    schema, schema_path = resolve_schema(schema, schema_path)

    if "allOf" in schema:
        for index, item in enumerate(require_schema_list(schema["allOf"], f"{path}.allOf")):
            validate_json_schema(value, item, path, schema_path)

    if "oneOf" in schema:
        matches = 0
        for item in require_schema_list(schema["oneOf"], f"{path}.oneOf"):
            try:
                validate_json_schema(value, item, path, schema_path)
            except ValueError:
                continue
            matches += 1
        if matches != 1:
            raise_schema_error(f"{path} must match exactly one oneOf schema, matched {matches}")

    if "const" in schema and value != schema["const"]:
        raise_schema_error(f"{path} must equal {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise_schema_error(f"{path} must be one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not type_matches(value, expected_type):
        raise_schema_error(f"{path} must be {expected_type}, got {type(value).__name__}")

    if schema.get("minLength") is not None and isinstance(value, str):
        if len(value) < int(schema["minLength"]):
            raise_schema_error(f"{path} is shorter than minLength {schema['minLength']}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise_schema_error(f"{path}.required must be a list")
        for key in required:
            if key not in value:
                raise_schema_error(f"{path}.{key} is required")

        properties = schema.get("properties", {})
        if properties is not None and not isinstance(properties, dict):
            raise_schema_error(f"{path}.properties must be an object")
        for key, item in value.items():
            if key in properties:
                child_schema = properties[key]
            else:
                additional = schema.get("additionalProperties", True)
                if additional is False:
                    raise_schema_error(f"{path}.{key} is not allowed")
                if additional is True:
                    continue
                if not isinstance(additional, dict):
                    raise_schema_error(f"{path}.additionalProperties must be boolean or object")
                child_schema = additional
            if not isinstance(child_schema, dict):
                raise_schema_error(f"{path}.{key} schema must be an object")
            validate_json_schema(item, child_schema, f"{path}.{key}", schema_path)

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                validate_json_schema(item, items, f"{path}[{index}]", schema_path)
        if schema.get("uniqueItems") is True:
            seen = set()
            for item in value:
                marker = json.dumps(item, sort_keys=True)
                if marker in seen:
                    raise_schema_error(f"{path} items must be unique")
                seen.add(marker)


def require_schema_list(value: Any, path: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise_schema_error(f"{path} must be a list of schemas")
    return value


def resolve_schema(schema: dict[str, Any], schema_path: Path) -> tuple[dict[str, Any], Path]:
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema, schema_path
    ref_file, _, fragment = ref.partition("#")
    target_path = schema_path if not ref_file else schema_path.parent / ref_file
    target = load_schema(target_path)
    if fragment:
        if not fragment.startswith("/"):
                return schema, schema_path
        current: Any = target
        for part in fragment.lstrip("/").split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or part not in current:
                raise_schema_error(f"unresolvable $ref {ref} from {schema_path}")
            current = current[part]
        if not isinstance(current, dict):
            raise_schema_error(f"$ref {ref} does not resolve to a schema object")
        target = current
    return target, target_path


def type_matches(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
        return any(type_matches(value, item) for item in expected_type)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise_schema_error(f"unsupported schema type {expected_type!r}")


def raise_schema_error(message: str) -> None:
    raise ValueError(message)


def check_contract_versions(run: dict[str, Any]) -> None:
    backend_output = optional_object(run, "backend_output")
    frontend_output = optional_object(run, "frontend_output")
    qa_output = optional_object(run, "qa_output")
    data_output = optional_object(run, "data_output")

    backend_api_version = None
    if backend_output is not None:
        backend_api_version = contract_version(
            backend_output.get("api_contract"),
            "backend_output.api_contract",
        )

    if backend_api_version is not None and frontend_output is not None:
        consumed = str(frontend_output.get("api_contract_version_consumed"))
        if consumed != backend_api_version:
            fail(
                "frontend_output.api_contract_version_consumed "
                f"({consumed}) does not match backend output ({backend_api_version})"
            )

    if backend_api_version is not None and qa_output is not None:
        consumed = str(qa_output.get("api_contract_version_consumed"))
        if consumed != backend_api_version:
            fail(
                "qa_output.api_contract_version_consumed "
                f"({consumed}) does not match backend output ({backend_api_version})"
            )

    data_version = None
    if data_output is not None:
        data_version = contract_version(data_output.get("data_contract"), "data_output.data_contract")
    if data_version is not None and qa_output is not None:
        consumed = qa_output.get("data_contract_version_consumed")
        if consumed is not None and str(consumed) != data_version:
            fail(
                "qa_output.data_contract_version_consumed "
                f"({consumed}) does not match data output ({data_version})"
            )

    pm_output = require_object(run.get("pm_output"), "pm_output")
    dispatches = require_object(pm_output.get("dispatches"), "pm_output.dispatches")
    for agent, dispatch in dispatches.items():
        dispatch_obj = require_object(dispatch, f"pm_output.dispatches.{agent}")
        api_version = contract_version(
            dispatch_obj.get("api_contract"),
            f"pm_output.dispatches.{agent}.api_contract",
        )
        if api_version is not None and backend_api_version is not None and api_version != backend_api_version:
            fail(
                f"pm_output.dispatches.{agent}.api_contract.contract_version "
                f"({api_version}) does not match backend output ({backend_api_version})"
            )


def check_frontend_e2e_handoff(run: dict[str, Any]) -> None:
    frontend_output = optional_object(run, "frontend_output")
    if frontend_output is None:
        return

    pm_output = require_object(run.get("pm_output"), "pm_output")
    dispatches = require_object(pm_output.get("dispatches"), "pm_output.dispatches")
    qa_dispatch = dispatches.get("qa")
    if not isinstance(qa_dispatch, dict) or qa_dispatch.get("scope") not in E2E_SCOPES:
        return

    qa_handoff = require_object(frontend_output.get("qa_handoff"), "frontend_output.qa_handoff")
    routes = qa_handoff.get("routes")
    selectors = qa_handoff.get("selectors")
    if not isinstance(routes, list) or not routes:
        fail("frontend_output.qa_handoff.routes is required for QA E2E scope")
    if not isinstance(selectors, list) or not selectors:
        fail("frontend_output.qa_handoff.selectors is required for QA E2E scope")


def check_mock_policy(run: dict[str, Any]) -> None:
    frontend_output = optional_object(run, "frontend_output")
    if frontend_output is None:
        return
    pm_output = require_object(run.get("pm_output"), "pm_output")
    dispatches = require_object(pm_output.get("dispatches"), "pm_output.dispatches")
    frontend_dispatch = dispatches.get("frontend")
    if not isinstance(frontend_dispatch, dict):
        return
    if frontend_dispatch.get("mock_policy") != "forbidden":
        return
    mock_usage = frontend_output.get("mock_usage")
    if not isinstance(mock_usage, dict):
        return
    if mock_usage.get("used_mocks") is True:
        fail("frontend_output.mock_usage.used_mocks violates frontend dispatch mock_policy=forbidden")


def check_blocking_issues(run: dict[str, Any]) -> None:
    for path, issue in walk_issues(run):
        if issue.get("blocking") is True and issue.get("status") not in RESOLVED_STATUSES:
            issue_id = issue.get("id", "<missing id>")
            fail(f"unresolved blocking issue at {path}: {issue_id}")


def check_run_state(run: dict[str, Any]) -> None:
    pm_output = require_object(run.get("pm_output"), "pm_output")
    bus_output = require_object(run.get("bus_output"), "bus_output")
    run_state = require_object(bus_output.get("run_state"), "bus_output.run_state")
    agent_states = require_object(run_state.get("agent_states"), "bus_output.run_state.agent_states")

    if bus_output.get("final_summary") != pm_output.get("summary"):
        fail("bus_output.final_summary must equal pm_output.summary")

    activated = bus_output.get("agents_activated")
    if not isinstance(activated, list):
        fail("bus_output.agents_activated must be a list")
    skipped_entries = bus_output.get("agents_skipped")
    if not isinstance(skipped_entries, list):
        fail("bus_output.agents_skipped must be a list")
    skipped = []
    for index, entry in enumerate(skipped_entries):
        entry_obj = require_object(entry, f"bus_output.agents_skipped[{index}]")
        agent = entry_obj.get("agent")
        if not isinstance(agent, str):
            fail(f"bus_output.agents_skipped[{index}].agent must be a string")
        skipped.append(agent)

    for agent in activated:
        if not isinstance(agent, str):
            fail("bus_output.agents_activated entries must be strings")
        output_key = AGENT_OUTPUTS.get(agent)
        if output_key is not None and output_key not in run:
            fail(f"{agent} is activated but {output_key} is missing")
        if agent not in agent_states:
            fail(f"bus_output.run_state.agent_states missing activated agent {agent}")

    for agent in skipped:
        if agent not in agent_states:
            fail(f"bus_output.run_state.agent_states missing skipped agent {agent}")

    activated_set = set(activated)
    for agent, output_key in AGENT_OUTPUTS.items():
        if output_key in run and agent not in activated_set:
            fail(f"{output_key} is present but {agent} is not activated")

    if run_state.get("status") == "completed":
        for agent in activated:
            if agent_states.get(agent) != "completed":
                fail(f"run_state.status=completed requires {agent} to be completed")

    dispatches = require_object(pm_output.get("dispatches"), "pm_output.dispatches")
    for agent in activated:
        dispatch_key = DISPATCH_AGENTS.get(agent)
        if dispatch_key is not None and dispatch_key not in dispatches:
            fail(f"{agent} is activated but pm_output.dispatches.{dispatch_key} is missing")


def walk_issues(value: Any, path: str = "$") -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if key == "issues" and isinstance(item, list):
                for index, issue in enumerate(item):
                    if isinstance(issue, dict):
                        found.append((f"{item_path}[{index}]", issue))
            else:
                found.extend(walk_issues(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(walk_issues(item, f"{path}[{index}]"))
    return found


def check_expected_examples(path: Path, should_pass: bool) -> None:
    try:
        check_run_output(path)
    except SystemExit as exc:
        if should_pass:
            raise
        if exc.code == 0:
            fail(f"expected invalid fixture to fail: {path}")
        return
    if not should_pass:
        fail(f"expected invalid fixture to fail: {path}")


def check_run_output(path: Path) -> None:
    run = load_json(path)
    try:
        validate_run_schema(run)
        check_contract_versions(run)
        check_frontend_e2e_handoff(run)
        check_mock_policy(run)
        check_blocking_issues(run)
        check_run_state(run)
    except ValueError as exc:
        fail(str(exc))


def main(argv: list[str]) -> None:
    if len(argv) == 1:
        fail("usage: check_run_output.py RUN_OUTPUT.json [...]")
    for item in argv[1:]:
        check_run_output(Path(item))
    print("run output checks passed")


if __name__ == "__main__":
    main(sys.argv)
