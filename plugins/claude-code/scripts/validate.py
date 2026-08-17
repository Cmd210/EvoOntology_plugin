#!/usr/bin/env python3
"""Deterministic validation of a versioned ontology workspace.

Checks that the active version exists, its five record files are valid JSON,
every cross-record reference resolves, and the store can be loaded by the
runtime. This is the publish-time gate; the Builder/Evolver analysis lives in
the skills, not here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from evoontology.ontology.store import SemanticStore, VERSION_FILES


def validate(root: str) -> Dict[str, Any]:
    root = Path(root)
    errors: List[str] = []

    active_file = root / "active.json"
    if not active_file.is_file():
        return {"passed": False, "root": str(root), "errors": [f"Missing {active_file}"]}

    try:
        active = json.loads(active_file.read_text(encoding="utf-8"))
        version = str(active.get("active_version") or active.get("version") or "").strip()
    except json.JSONDecodeError as exc:
        return {"passed": False, "root": str(root), "errors": [f"Invalid active.json: {exc}"]}

    if not version:
        errors.append("active.json has no 'version'")
        return {"passed": False, "root": str(root), "version": "", "errors": errors}

    version_dir = root / "versions" / version
    if not version_dir.is_dir():
        errors.append(f"Version directory missing: {version_dir}")
        return {"passed": False, "root": str(root), "version": version, "errors": errors}

    # Load raw records for reference checking.
    raw: Dict[str, Dict[str, dict]] = {}
    for filename in VERSION_FILES:
        path = version_dir / filename
        if not path.is_file():
            errors.append(f"Missing file: {path}")
            continue
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {filename}: {exc}")
            continue
        if not isinstance(records, list):
            errors.append(f"{filename} must be a JSON list")
            continue
        raw[filename] = {item["id"]: item for item in records}

    term_ids = set(raw.get("terms.json", {}))
    mapping_ids = set(raw.get("mappings.json", {}))
    evidence_ids = set(raw.get("evidence.json", {}))

    def _check_refs(field_value, *, label: str, allowed: set):
        refs = field_value
        if isinstance(refs, dict):
            refs = refs.get("source_refs", [])
        if not isinstance(refs, list):
            return
        for ref in refs:
            if str(ref) not in allowed:
                errors.append(f"{label}: unresolved evidence ref {ref!r}")

    for obj_id, item in raw.get("terms.json", {}).items():
        _check_refs(item.get("evidence"), label=f"term {obj_id}", allowed=evidence_ids)
    for obj_id, item in raw.get("relations.json", {}).items():
        for end in ("source", "target"):
            ref = item.get(end)
            if ref and ref not in term_ids:
                errors.append(f"relation {obj_id}: unresolved {end} {ref!r}")
        _check_refs(item.get("evidence"), label=f"relation {obj_id}", allowed=evidence_ids)
    def _mapping_evidence(item: dict):
        refs = item.get("evidence_refs", [])
        if refs:
            return refs
        validation = item.get("validation", {})
        if isinstance(validation, dict):
            val_evidence = validation.get("evidence", [])
            if isinstance(val_evidence, list):
                return val_evidence
        return item.get("evidence", [])

    for obj_id, item in raw.get("mappings.json", {}).items():
        term_ref = item.get("term_id")
        if term_ref and term_ref not in term_ids:
            errors.append(f"mapping {obj_id}: unresolved term_id {term_ref!r}")
        _check_refs(_mapping_evidence(item), label=f"mapping {obj_id}", allowed=evidence_ids)
    for obj_id, item in raw.get("constraints.json", {}).items():
        target = item.get("target")
        if target and target not in term_ids and target not in mapping_ids:
            errors.append(f"constraint {obj_id}: unresolved target {target!r}")
        _check_refs(item.get("evidence"), label=f"constraint {obj_id}", allowed=evidence_ids)

    # The runtime must be able to load the store.
    if not errors:
        try:
            SemanticStore.load(str(root))
        except Exception as exc:
            errors.append(f"Store load failed: {exc}")

    return {
        "passed": not errors,
        "root": str(root),
        "version": version,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an ontology workspace")
    parser.add_argument("--root", required=True, help="Workspace root containing active.json")
    args = parser.parse_args()
    report = validate(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
