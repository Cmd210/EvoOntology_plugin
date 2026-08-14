"""Load the immutable, versioned DDR semantic store."""

import json
from pathlib import Path
from typing import Dict, Optional

from .models import Constraint, Evidence, Mapping, Relation, Term


DEFAULT_STORE_DIR = Path(__file__).resolve().parents[1] / "semantic_layer"


class VersionedSemanticStore:
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

    @classmethod
    def load(cls, path: Optional[str] = None) -> "VersionedSemanticStore":
        """Load the semantic version selected by ``active.json``."""
        store_dir = Path(path) if path else DEFAULT_STORE_DIR
        active_file = store_dir / "active.json"
        if not active_file.is_file():
            raise FileNotFoundError(f"Missing semantic-layer index: {active_file}")

        version = _load_json(active_file).get("version", "")
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
        missing = [
            filename for filename, _ in required.values()
            if not (version_dir / filename).is_file()
        ]
        if missing:
            raise FileNotFoundError(
                f"Semantic version {version!r} is missing files: {missing}"
            )

        loaded = {}
        for family, (filename, model) in required.items():
            records = _load_json(version_dir / filename)
            loaded[family] = {item["id"]: model.from_dict(item) for item in records}
        return cls(version=version, root_dir=str(store_dir), **loaded)

    def get(self, semantic_id: str):
        """Return an object from any semantic record family."""
        return (
            self.terms.get(semantic_id)
            or self.relations.get(semantic_id)
            or self.mappings.get(semantic_id)
            or self.constraints.get(semantic_id)
            or self.evidence.get(semantic_id)
        )


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)
