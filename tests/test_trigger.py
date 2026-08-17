"""Trigger tests: initialization, thresholds, and checkpoint reset."""

from datetime import datetime, timedelta, timezone

from evoontology import EvolutionTrigger, TrajectoryStore


def _seed(tmp_path, n, start_day):
    store = TrajectoryStore(str(tmp_path))
    for i in range(n):
        day = start_day + timedelta(days=i)
        store.append({
            "task_id": f"task_{i:03d}",
            "question": f"q{i}",
            "ontology_version": "semantic_v0",
            "tool_calls": [],
            "final_answer": "a",
            "status": "completed",
        }, recorded_at=day.isoformat())
    return store


def test_count_trigger(tmp_path):
    _seed(tmp_path, 3, datetime(2026, 8, 1, tzinfo=timezone.utc))
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=2, min_days=7)
    result = trigger.check()
    assert result["evolution_due"] is True
    assert result["new_trajectories"] == 3


def test_initialize_creates_initial_state(tmp_path):
    started_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=20, min_days=14)

    state = trigger.initialize(when=started_at)

    assert state == {
        "last_evolution_trajectory": None,
        "last_evolution_time": started_at.isoformat(),
        "evolution_due": False,
        "thresholds": {"min_new_trajectories": 20, "min_days": 14},
    }
    assert (tmp_path / "state.json").is_file()


def test_initialize_is_idempotent(tmp_path):
    first = datetime(2026, 8, 1, tzinfo=timezone.utc)
    later = datetime(2026, 8, 20, tzinfo=timezone.utc)
    trigger = EvolutionTrigger(str(tmp_path))

    initial_state = trigger.initialize(when=first)
    current_state = trigger.initialize(when=later)

    assert current_state == initial_state
    assert current_state["last_evolution_time"] == first.isoformat()


def test_initialize_preserves_existing_trajectories_for_first_reminder(tmp_path):
    _seed(tmp_path, 3, datetime(2026, 8, 1, tzinfo=timezone.utc))
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=2, min_days=7)

    trigger.initialize(when=datetime(2026, 8, 4, tzinfo=timezone.utc))
    result = trigger.check(now=datetime(2026, 8, 4, tzinfo=timezone.utc))

    assert result["evolution_due"] is True
    assert result["new_trajectories"] == 3


def test_time_trigger(tmp_path):
    _seed(tmp_path, 1, datetime(2026, 8, 1, tzinfo=timezone.utc))
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=10, min_days=7)
    trigger.mark_evolved("task_000", when=datetime(2026, 8, 1, tzinfo=timezone.utc))

    now = datetime(2026, 8, 20, tzinfo=timezone.utc)  # 19 days later
    result = trigger.check(now=now)
    assert result["evolution_due"] is True
    assert result["days_since_last_evolution"] >= 7


def test_checkpoint_reset(tmp_path):
    _seed(tmp_path, 3, datetime(2026, 8, 1, tzinfo=timezone.utc))
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=2, min_days=7)
    assert trigger.check()["evolution_due"] is True

    trigger.mark_evolved("task_002")
    result = trigger.check()
    assert result["evolution_due"] is False
    assert result["new_trajectories"] == 0


def test_mark_evolved_autodetect_last(tmp_path):
    _seed(tmp_path, 3, datetime(2026, 8, 1, tzinfo=timezone.utc))
    trigger = EvolutionTrigger(str(tmp_path), min_new_trajectories=2, min_days=7)
    state = trigger.mark_evolved()  # no explicit id -> last trajectory
    assert state["last_evolution_trajectory"] == "task_002"
    assert state["evolution_due"] is False
