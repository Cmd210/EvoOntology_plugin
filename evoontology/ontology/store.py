"""Versioned ontology store: load, save, publish candidates, and switch active version.

A store root (workspace) contains ``active.json`` (``{"active_version": "<v>"}``)
and a ``versions/<v>/`` directory holding the five serialized record files:
``terms.json``, ``mappings.json``, ``relations.json``, ``constraints.json``, and
``evidence.json``. ``active.json`` also accepts the legacy ``version`` field for
backward compatibility with pre-``.evoontology`` workspaces.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

from .models import Constraint, Evidence, Mapping, Relation, Term

# The five serialized record files under ``versions/<v>/``.
VERSION_FILES = (
    "terms.json",
    "mappings.json",
    "relations.json",
    "constraints.json",
    "evidence.json",
)

_FAMILIES = {
    "terms": ("terms.json", Term),
    "relations": ("relations.json", Relation),
    "mappings": ("mappings.json", Mapping),
    "constraints": ("constraints.json", Constraint),
    "evidence": ("evidence.json", Evidence),
}


class SemanticStore:
    """In-memory view of the semantic version selected by ``active.json``."""

    def __init__(
        self,
        version: str,
        terms: Dict[str, Term],
        relations: Dict[str, Relation],
        mappings: Dict[str, Mapping],
        constraints: Dict[str, Constraint],
        evidence: Dict[str, Evidence],
        root_dir: str = "",
    ):
        self.version = version
        self.terms = terms
        self.relations = relations
        self.mappings = mappings
        self.constraints = constraints
        self.evidence = evidence
        self.root_dir = root_dir

    # ---- loading -----------------------------------------------------------

    @classmethod
    def load(cls, path: str) -> "SemanticStore":
        """Load the semantic version selected by ``active.json`` under ``path``."""
        version, records = cls.load_records(path)
        loaded = {}
        for family, (filename, model) in _FAMILIES.items():
            loaded[family] = {
                item["id"]: model.from_dict(item) for item in records[family]
            }
        return cls(version=version, root_dir=str(Path(path)), **loaded)

    @classmethod
    def load_records(cls, path: str) -> tuple[str, Dict[str, list]]:
        """Load raw records for benchmark-specific thin adapters.

        This is the canonical implementation of active-version selection and
        required-file checking. Benchmark adapters may construct richer local
        model objects without reimplementing the on-disk store contract.
        """
        version = cls.active_version(path)
        version_dir = Path(path) / "versions" / version
        missing = [
            filename for filename, _ in _FAMILIES.values()
            if not (version_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                f"Semantic version {version!r} is missing files: {missing}"
            )
        return version, {
            family: _load_json(version_dir / filename)
            for family, (filename, _) in _FAMILIES.items()
        }

    @staticmethod
    def active_version(path: str) -> str:
        """Return the active version name without loading records."""
        store_dir = Path(path)
        active_file = store_dir / "active.json"
        if not active_file.is_file():
            raise FileNotFoundError(f"Missing ontology index: {active_file}")
        active = _load_json(active_file)
        version = str(active.get("active_version") or active.get("version") or "").strip()
        if not version:
            raise ValueError(f"Missing active_version in {active_file}")
        return version

    # ---- writing -----------------------------------------------------------

    @classmethod
    def save_version(cls, path: str, version: str, records: Dict[str, list]) -> str:
        """Write a version directory holding the five record files.

        ``records`` maps each family name (``terms`` / ``mappings`` /
        ``relations`` / ``constraints`` / ``evidence``) to a list of raw record
        dicts. Returns the absolute path of the written version directory.
        """
        version_dir = Path(path) / "versions" / version
        version_dir.mkdir(parents=True, exist_ok=True)
        for family, (filename, _) in _FAMILIES.items():
            items = records.get(family, [])
            if not isinstance(items, list):
                raise TypeError(f"records[{family!r}] must be a list")
            (version_dir / filename).write_text(
                json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return str(version_dir)

    @classmethod
    def set_active(cls, path: str, version: str) -> None:
        """Point ``active.json`` at ``version``."""
        active_file = Path(path) / "active.json"
        active_file.write_text(
            json.dumps({"active_version": version}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def promote(cls, path: str, candidate_version: str, new_version: str) -> str:
        """Accept a candidate: copy it to ``new_version`` and make it active.

        The candidate must already exist under ``versions/<candidate_version>/``
        (written via :meth:`save_version`). Rejects are simply "do not promote":
        ``active.json`` keeps pointing at the parent. Returns the new version name.
        """
        root = Path(path)
        src = root / "versions" / candidate_version
        if not src.is_dir():
            raise FileNotFoundError(f"Candidate version missing: {src}")
        dst = root / "versions" / new_version
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        cls.set_active(str(root), new_version)
        return new_version

    @staticmethod
    def list_versions(path: str) -> List[str]:
        """Return the names of all versions present under ``versions/``."""
        versions_dir = Path(path) / "versions"
        if not versions_dir.is_dir():
            return []
        return sorted(p.name for p in versions_dir.iterdir() if p.is_dir())

    # ---- lookup ------------------------------------------------------------

    def get(self, semantic_id: str):
        """Return an object from any semantic record family."""
        return (
            self.terms.get(semantic_id)
            or self.relations.get(semantic_id)
            or self.mappings.get(semantic_id)
            or self.constraints.get(semantic_id)
            or self.evidence.get(semantic_id)
        )

    def counts(self) -> Dict[str, int]:
        return {
            "terms": len(self.terms),
            "mappings": len(self.mappings),
            "relations": len(self.relations),
            "constraints": len(self.constraints),
            "evidence": len(self.evidence),
        }


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def ensure_workspace(root: str) -> str:
    """Create the ``.evoontology`` workspace skeleton (``versions/`` and
    ``trajectories/``). Idempotent; ``active.json`` and ``state.json`` are
    written lazily by :meth:`SemanticStore.set_active` and the trigger module.
    """
    root_dir = Path(root)
    (root_dir / "versions").mkdir(parents=True, exist_ok=True)
    (root_dir / "trajectories").mkdir(parents=True, exist_ok=True)
    return str(root_dir)
