"""Load an immutable, versioned InsightBench semantic store."""

import json
from pathlib import Path
from typing import Dict, Optional

from insightbench.tceo.models import Constraint, Evidence, Mapping, Relation, Term


_DEFAULT_STORE_DIR = Path(__file__).resolve().parents[2] / "semantic_layer"
DEFAULT_STORE_PATH = str(_DEFAULT_STORE_DIR)


class VersionedSemanticStore:
    """In-memory view of the version selected by ``active.json``."""

    def __init__(
        self,
        version: str,
        terms: Dict[str, Term],
        relations: Dict[str, Relation],
        mappings: Dict[str, Mapping],
        constraints: Dict[str, Constraint],
        evidence: Dict[str, Evidence],
    ):
        self.version = version
        self._terms = terms
        self._relations = relations
        self._mappings = mappings
        self._constraints = constraints
        self._evidence = evidence

    @property
    def terms(self) -> Dict[str, Term]:
        return dict(self._terms)

    @property
    def relations(self) -> Dict[str, Relation]:
        return dict(self._relations)

    @property
    def mappings(self) -> Dict[str, Mapping]:
        return dict(self._mappings)

    @property
    def constraints(self) -> Dict[str, Constraint]:
        return dict(self._constraints)

    @property
    def evidence(self) -> Dict[str, Evidence]:
        return dict(self._evidence)

    def get(self, semantic_id: str):
        """Return an object from any semantic record family."""
        return (
            self._terms.get(semantic_id)
            or self._relations.get(semantic_id)
            or self._mappings.get(semantic_id)
            or self._constraints.get(semantic_id)
            or self._evidence.get(semantic_id)
        )

    @classmethod
    def load(cls, path: Optional[str] = None) -> "VersionedSemanticStore":
        """Load the immutable version selected by ``active.json``."""
        store_dir = Path(path) if path else _DEFAULT_STORE_DIR
        active_file = store_dir / "active.json"
        if not active_file.is_file():
            raise FileNotFoundError(f"Missing semantic-layer index: {active_file}")

        active = _load_json(active_file)
        version = active.get("version", "")
        if not version:
            raise ValueError(f"Missing version in {active_file}")

        version_dir = store_dir / "versions" / version
        required = {
            "terms": ("terms.json", Term),
            "relations": ("relations.json", Relation),
            "mappings": ("mappings.json", Mapping),
            "constraints": ("constraints.json", Constraint),
            "evidence": ("evidence.json", Evidence),
        }
        missing = [name for name, _ in required.values() if not (version_dir / name).is_file()]
        if missing:
            raise FileNotFoundError(
                f"Semantic version {version!r} is missing files: {missing}"
            )

        loaded = {}
        for family, (filename, model) in required.items():
            records = _load_json(version_dir / filename)
            loaded[family] = {item["id"]: model.from_dict(item) for item in records}
        return cls(version=version, **loaded)


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)
