#!/usr/bin/env python3
"""Lightweight contract checks for this skill bundle.

The script intentionally uses only the Python standard library so `make check`
works in a plain checkout.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMON_CONTRACT_REF = "common.schema.json#/$defs/contract"


def fail(message: str) -> None:
    print(f"check_contracts: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def load_yaml_subset(path: Path) -> object:
    """Parse the limited YAML shape used by bundle.yaml and agents.yaml."""

    lines = path.read_text(encoding="utf-8").splitlines()
    root: dict[str, object] = {}
    stack: list[tuple[int, object]] = [(-1, root)]

    for index, raw in enumerate(lines):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            if not isinstance(parent, list):
                fail(f"unsupported YAML list placement in {path.relative_to(ROOT)}: {raw}")
            parent.append(parse_yaml_scalar(line[2:].strip()))
            continue

        if ":" not in line:
            fail(f"unsupported YAML line in {path.relative_to(ROOT)}: {raw}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value:
            item: object = parse_yaml_scalar(value)
        else:
            next_item = next_significant_line(lines, index)
            item = [] if next_item and next_item.strip().startswith("- ") else {}

        if not isinstance(parent, dict):
            fail(f"unsupported YAML mapping placement in {path.relative_to(ROOT)}: {raw}")
        parent[key] = item
        if isinstance(item, (dict, list)):
            stack.append((indent, item))

    return root


def next_significant_line(lines: list[str], current_index: int) -> str | None:
    current_raw = lines[current_index]
    current_indent = len(current_raw) - len(current_raw.lstrip(" "))
    for raw in lines[current_index + 1:]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent <= current_indent:
            return None
        return raw
    return None


def parse_yaml_scalar(value: str) -> object:
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(item.strip()) for item in inner.split(",")]
    return value.strip("'\"")


def check_schema_files() -> None:
    schema_dir = ROOT / "schemas"
    files = sorted(schema_dir.glob("*.schema.json"))
    if not files:
        fail("no schema files found")
    for path in files:
        data = load_json(path)
        if not isinstance(data, dict):
            fail(f"schema is not an object: {path.relative_to(ROOT)}")
        if "$schema" not in data:
            fail(f"schema missing $schema: {path.relative_to(ROOT)}")
        if "$id" not in data:
            fail(f"schema missing $id: {path.relative_to(ROOT)}")
        for ref in collect_refs(data):
            if ref.startswith("#") or ref.startswith("http://") or ref.startswith("https://"):
                continue
            ref_path = ref.split("#", 1)[0]
            if ref_path and not (path.parent / ref_path).exists():
                fail(f"schema {path.relative_to(ROOT)} references missing $ref: {ref}")
        check_contract_properties(path, data)


def collect_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                refs.append(item)
            else:
                refs.extend(collect_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(collect_refs(item))
    return refs


def check_registry_paths() -> None:
    registry = load_agents_registry()
    for agent_name, agent in registry.items():
        for key in ("path", "input_schema", "output_schema"):
            value = agent.get(key)
            if value is None:
                continue
            if not isinstance(value, str):
                fail(f"agents.yaml {agent_name}.{key} must be a string or null")
            if not (ROOT / value).exists():
                fail(f"agents.yaml references missing {key}: {value}")


def check_required_docs() -> None:
    required = [
        "references/contracts.md",
        "references/state-machine.md",
        "references/artifact-policy.md",
        "references/retry-policy.md",
        "bundle.yaml",
        "schemas/project_context.schema.json",
        "schemas/bus_output.schema.json",
        "schemas/issue.schema.json",
        "agents.yaml",
    ]
    for item in required:
        if not (ROOT / item).exists():
            fail(f"missing required contract file: {item}")


def load_agents_registry() -> dict[str, dict[str, object]]:
    data = load_yaml_subset(ROOT / "agents.yaml")
    agents = data.get("agents") if isinstance(data, dict) else None
    if not isinstance(agents, dict):
        fail("agents.yaml missing agents mapping")
    for name, agent in agents.items():
        if not isinstance(agent, dict):
            fail(f"agents.yaml agent entry is not an object: {name}")
    return agents  # type: ignore[return-value]


def check_contract_properties(path: Path, schema: object) -> None:
    for pointer, value in walk_schema(schema):
        if not pointer.endswith("_contract"):
            continue
        if not contains_ref(value, COMMON_CONTRACT_REF):
            fail(
                f"{path.relative_to(ROOT)} property {pointer} must reference "
                f"{COMMON_CONTRACT_REF}"
            )


def walk_schema(value: object, path: str = "") -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            for name, child in properties.items():
                child_path = f"{path}.{name}" if path else str(name)
                found.append((child_path, child))
                found.extend(walk_schema(child, child_path))
        for key in ("items", "additionalProperties", "$defs"):
            child = value.get(key)
            if isinstance(child, dict):
                found.extend(walk_schema(child, path))
    return found


def contains_ref(value: object, ref: str) -> bool:
    if isinstance(value, dict):
        return value.get("$ref") == ref or any(contains_ref(item, ref) for item in value.values())
    if isinstance(value, list):
        return any(contains_ref(item, ref) for item in value)
    return False


def check_outputs_doc_matches_schemas() -> None:
    doc = (ROOT / "references" / "outputs.md").read_text(encoding="utf-8")
    schema_by_root = {
        "architect_output": load_json(ROOT / "schemas" / "architect_output.schema.json"),
        "pm_output": load_json(ROOT / "schemas" / "pm_output.schema.json"),
        "bus_output": load_json(ROOT / "schemas" / "bus_output.schema.json"),
    }

    for root_name, paths in extract_yaml_field_paths(doc).items():
        schema = schema_by_root.get(root_name)
        if schema is None:
            fail(f"references/outputs.md declares unknown output object: {root_name}")
        for path in sorted(paths):
            if not schema_path_exists(schema, path, ROOT / "schemas" / f"{root_name}.schema.json"):
                fail(f"references/outputs.md declares {root_name}.{path}, missing from schema")


def extract_yaml_field_paths(markdown: str) -> dict[str, set[str]]:
    blocks = re.findall(r"```yaml\n(.*?)\n```", markdown, flags=re.DOTALL)
    result: dict[str, set[str]] = {}
    for block in blocks:
        stack: list[tuple[int, str]] = []
        root_name: str | None = None
        for raw in block.splitlines():
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            line = raw.strip()
            if line.startswith("- "):
                line = line[2:].strip()
                if ":" not in line:
                    continue
            if ":" not in line:
                continue
            key = line.split(":", 1)[0].strip().strip("'\"")
            if not key or key.endswith("[]"):
                continue
            while stack and indent <= stack[-1][0]:
                stack.pop()
            if root_name is None:
                root_name = key
                result.setdefault(root_name, set())
                stack.append((indent, ""))
                continue
            parent = stack[-1][1] if stack else ""
            path = f"{parent}.{key}" if parent else key
            result[root_name].add(path)
            stack.append((indent, path))
    return result


def schema_path_exists(schema: object, dotted_path: str, schema_path: Path) -> bool:
    current = schema
    for part in dotted_path.split("."):
        current = resolve_schema_ref(unwrap_schema(current), schema_path)
        if not isinstance(current, dict):
            return False
        properties = current.get("properties")
        if isinstance(properties, dict) and part in properties:
            current = properties[part]
            continue
        additional = current.get("additionalProperties")
        if isinstance(additional, dict):
            current = additional
            continue
        if "items" in current:
            current = current["items"]
            if schema_path_exists(current, part, schema_path):
                continue
        return False
    return True


def unwrap_schema(schema: object) -> object:
    if not isinstance(schema, dict):
        return schema
    for key in ("allOf", "oneOf", "anyOf"):
        variants = schema.get(key)
        if isinstance(variants, list):
            merged: dict[str, object] = {}
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                properties = variant.get("properties")
                if isinstance(properties, dict):
                    merged.setdefault("properties", {}).update(properties)  # type: ignore[union-attr]
                additional = variant.get("additionalProperties")
                if additional is not None:
                    merged["additionalProperties"] = additional
                items = variant.get("items")
                if items is not None:
                    merged["items"] = items
            if merged:
                return merged
    return schema


def resolve_schema_ref(schema: object, schema_path: Path) -> object:
    if not isinstance(schema, dict):
        return schema
    ref = schema.get("$ref")
    if not isinstance(ref, str) or ref.startswith(("http://", "https://")):
        return schema

    ref_file, _, fragment = ref.partition("#")
    target_path = schema_path if not ref_file else schema_path.parent / ref_file
    target = load_json(target_path)
    if not fragment:
        return target
    if not fragment.startswith("/"):
        return schema
    current = target
    for part in fragment.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            return schema
        current = current[part]
    return current


def check_registry_artifact_names() -> None:
    agents = load_agents_registry()
    known = {
        "project_context",
        "user_intent",
        "architect_output",
        "pm_output",
        "pm_summary",
        "bus_output",
    }
    for schema_path in (ROOT / "schemas").glob("*.schema.json"):
        schema = load_json(schema_path)
        if not isinstance(schema, dict):
            continue
        known.add(schema_path.name.removesuffix(".schema.json"))
        properties = schema.get("properties")
        if isinstance(properties, dict):
            known.update(str(name) for name in properties)

    for agent_name, agent in agents.items():
        for key in ("consumes", "produces"):
            values = agent.get(key)
            if not isinstance(values, list):
                fail(f"agents.yaml {agent_name}.{key} must be a list")
            unknown = sorted(str(item) for item in values if item not in known)
            if unknown:
                fail(f"agents.yaml {agent_name}.{key} uses unknown artifact(s): {unknown}")


def check_context_schema_version() -> None:
    schema = load_json(ROOT / "schemas" / "project_context.schema.json")
    if not isinstance(schema, dict):
        fail("project_context.schema.json is not an object")
    version = (
        schema.get("properties", {})
        .get("schema_version", {})
        .get("const")
    )
    if not isinstance(version, str):
        fail("project_context.schema.json schema_version.const is missing")

    doc = (ROOT / "references" / "context-schema.md").read_text(encoding="utf-8")
    match = re.search(r"schema_version:\s+[\"']([^\"']+)[\"']", doc)
    if not match:
        fail("references/context-schema.md missing schema_version example")
    if match.group(1) != version:
        fail(
            "project_context.schema.json schema_version does not match "
            "references/context-schema.md example"
        )

    bundle = load_yaml_subset(ROOT / "bundle.yaml")
    compatible = bundle.get("compatible_context_schema_versions") if isinstance(bundle, dict) else None
    if not isinstance(compatible, list) or version not in compatible:
        fail("bundle.yaml compatible_context_schema_versions must include project context schema version")


def check_bundle_version_policy() -> None:
    bundle = load_yaml_subset(ROOT / "bundle.yaml")
    agents = load_yaml_subset(ROOT / "agents.yaml")
    if not isinstance(bundle, dict) or not isinstance(agents, dict):
        fail("bundle.yaml and agents.yaml must be mappings")
    if bundle.get("schema_version") != agents.get("schema_version"):
        fail("agents.yaml schema_version must match bundle.yaml schema_version")
    if not bundle.get("bundle_version"):
        fail("bundle.yaml missing bundle_version")


def check_input_dispatch_contracts() -> None:
    agents = load_agents_registry()
    expected_inputs = {
        "architect-agent": "schemas/architect_input.schema.json",
        "pm-agent": "schemas/pm_input.schema.json",
        "data-agent": "schemas/data_input.schema.json",
        "backend-agent": "schemas/backend_input.schema.json",
        "frontend-agent": "schemas/frontend_input.schema.json",
        "qa-agent": "schemas/qa_input.schema.json",
    }
    for agent_name, schema_path in expected_inputs.items():
        agent = agents.get(agent_name)
        if agent is None:
            fail(f"agents.yaml missing {agent_name}")
        if agent.get("input_schema") != schema_path:
            fail(f"agents.yaml {agent_name}.input_schema must be {schema_path}")

    expected_refs = {
        "data_input.schema.json": "data_dispatch.schema.json",
        "backend_input.schema.json": "backend_dispatch.schema.json",
        "frontend_input.schema.json": "frontend_dispatch.schema.json",
        "qa_input.schema.json": "qa_dispatch.schema.json",
    }
    for input_file, expected_ref in expected_refs.items():
        schema = load_json(ROOT / "schemas" / input_file)
        if not isinstance(schema, dict) or schema.get("$ref") != expected_ref:
            fail(f"schemas/{input_file} must directly reference {expected_ref}")

    pm_output = load_json(ROOT / "schemas" / "pm_output.schema.json")
    dispatches = (
        pm_output.get("properties", {})
        .get("dispatches", {})
        if isinstance(pm_output, dict)
        else {}
    )
    if not isinstance(dispatches, dict) or dispatches.get("$ref") != "dispatches.schema.json":
        fail("pm_output.dispatches must reference dispatches.schema.json")


def main() -> None:
    check_required_docs()
    check_schema_files()
    check_registry_paths()
    check_outputs_doc_matches_schemas()
    check_registry_artifact_names()
    check_context_schema_version()
    check_bundle_version_policy()
    check_input_dispatch_contracts()
    print("contract checks passed")


if __name__ == "__main__":
    main()
