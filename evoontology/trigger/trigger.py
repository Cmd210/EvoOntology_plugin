"""Evolution trigger: decide whether to remind the user to evolve.

The trigger only decides *whether* to remind — it never starts the Evolver.
Two conditions (OR): at least ``min_new_trajectories`` new tasks since the last
evolution, or at least ``min_days`` elapsed since the last evolution. Checkpoints
live in ``<workspace>/state.json``; after an evolution completes,
:meth:`EvolutionTrigger.mark_evolved` resets them and clears ``evolution_due``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ..trajectory.trajectory import TrajectoryStore

DEFAULT_MIN_TRAJECTORIES = 10
DEFAULT_MIN_DAYS = 7


class EvolutionTrigger:
    def __init__(
        self,
        root: str,
        min_new_trajectories: int = DEFAULT_MIN_TRAJECTORIES,
        min_days: int = DEFAULT_MIN_DAYS,
    ):
        self.root = Path(root)
        self.trajectories = TrajectoryStore(str(self.root))
        self.state_path = self.root / "state.json"
        self._default_min_new = min_new_trajectories
        self._default_min_days = min_days

    # ---- state -------------------------------------------------------------

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.is_file():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        self.state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _thresholds(self) -> Dict[str, int]:
        state = self._load_state()
        thresholds = state.get("thresholds", {})
        if not isinstance(thresholds, dict):
            thresholds = {}
        return {
            "min_new_trajectories": int(
                thresholds.get("min_new_trajectories", self._default_min_new)
            ),
            "min_days": int(thresholds.get("min_days", self._default_min_days)),
        }

    # ---- check -------------------------------------------------------------

    def check(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Return whether evolution is due, with the supporting numbers.

        ``now`` is injectable for deterministic tests.
        """
        state = self._load_state()
        thresholds = self._thresholds()
        min_new = thresholds["min_new_trajectories"]
        min_days = thresholds["min_days"]

        last_traj = state.get("last_evolution_trajectory")
        last_time = state.get("last_evolution_time")

        new_count = self.trajectories.count_since(last_traj if last_traj else None)

        due_by_count = new_count >= min_new
        due_by_time = False
        days_since = None
        if last_time:
            try:
                last_dt = datetime.fromisoformat(str(last_time))
            except ValueError:
                last_dt = None
            if last_dt is not None:
                current = now or datetime.now(timezone.utc)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                days_since = (current - last_dt).total_seconds() / 86400.0
                due_by_time = days_since >= min_days

        evolution_due = due_by_count or due_by_time

        reasons = []
        if due_by_count:
            reasons.append(f"{new_count} new trajectories >= {min_new}")
        if due_by_time:
            reasons.append(f"{days_since:.1f} days since last evolution >= {min_days}")

        return {
            "evolution_due": evolution_due,
            "new_trajectories": new_count,
            "days_since_last_evolution": round(days_since, 3) if days_since is not None else None,
            "reason": " OR ".join(reasons) if reasons else "not due",
            "thresholds": thresholds,
        }

    def mark_evolved(
        self,
        last_trajectory_id: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Reset the evolution checkpoint after a completed evolution round.

        When ``last_trajectory_id`` is omitted, the most recently recorded task
        becomes the checkpoint so the next round only analyzes newer tasks.
        ``when`` injects the checkpoint timestamp for deterministic tests.
        """
        if last_trajectory_id is None:
            all_trajs = self.trajectories.list_since(None)
            if all_trajs:
                last_trajectory_id = str(all_trajs[-1].get("task_id"))

        checkpoint = when or datetime.now(timezone.utc)
        thresholds = self._thresholds()
        state = {
            "last_evolution_trajectory": last_trajectory_id,
            "last_evolution_time": checkpoint.isoformat(),
            "evolution_due": False,
            "thresholds": thresholds,
        }
        self._save_state(state)
        return state
