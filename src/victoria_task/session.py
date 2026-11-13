"""Session logic with no graphics, so it can be tested without a display.

A session is one practice trial, then blocks of scored trials, each block followed
by the manipulation checks. Every scored trial is saved as soon as it ends, so a
crash loses at most the trial in progress.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .data import ParticipantStore
from .deal import Trial, deal, practice_trial
from .grid import GridController
from .schedule import Block, build_schedule
from .scoring import criterion, dprime
from .stimuli import Item, Room, pool


@dataclass
class TrialTiming:
    """What the display measured for one trial."""
    study_ms: int
    study_end_frame_ms: float
    study_dropped_frames: int | None
    retention_ms: int
    filler_answered: int
    filler_correct: int
    filler_mean_rt_ms: float | None = None


class Session:
    """One participant's progress: what is next, what is saved, and how it resumes.

    baseline=True is the no-study group: they never see the rooms, so their picks
    show whether targets can be told apart from decoys without having seen them. Their files start
    with B instead of P, their condition is recorded as baseline, and they do no
    manipulation checks.
    """

    def __init__(self, config: Config, data_dir: Path, participant: int, items: dict[str, Item],
                 rooms: dict[str, Room], build: str = "test", baseline: bool = False):
        self.config = config
        self.participant = participant
        self.items = items
        self.build = build
        self.baseline = baseline
        self.store = ParticipantStore(data_dir, participant, "B" if baseline else "P")
        self.blocks: list[Block] = build_schedule(participant, config.conditions, config.rooms)
        self.trials: list[Trial] = deal(participant, self.blocks, rooms, pool(items, "target"),
                                        pool(items, "decoy"), config.tiles)
        self.practice: Trial = practice_trial(participant, rooms[config.practice_room],
                                              pool(items, "practice_target"), pool(items, "practice_decoy"),
                                              config.tiles)
        self.resumed = False
        self.finished: list[list] = []
        self.practice_done = False
        self.checks_done: list[int] = []
        state = self.store.load_state()
        if state:
            self.resumed = True
            if state.get("deal") != self.deal_record():
                raise RuntimeError(f"participant {participant}: saved deal differs from this build's "
                                   "objects or rooms; finish this participant with the build that started them")
            self.finished = state["finished"]
            self.practice_done = bool(state.get("practice_done"))
            self.checks_done = list(state.get("checks_done", []))
            self.store.reconcile({(str(b), r) for b, r in self.finished}, {str(b) for b in self.checks_done})

    # ------------------------------------------------------------ progress
    def is_complete(self) -> bool:
        return self.store.is_complete()

    def _all_done(self) -> bool:
        return all(not self.trials_left(b) and not self.needs_checks(b) for b in self.blocks)

    def trials_left(self, block: Block) -> list[Trial]:
        done = {(b, r) for b, r in self.finished}
        return [t for t in self.trials if t.block == block.index and (t.block, t.room) not in done]

    def needs_practice(self) -> bool:
        return not self.practice_done and not self.finished

    def block_started(self, block: Block) -> bool:
        return len(self.trials_left(block)) < len(block.rooms)

    def needs_checks(self, block: Block) -> bool:
        return self.config.checks and not self.baseline and block.index not in self.checks_done

    def deal_record(self) -> list[dict]:
        """The whole deal, saved with the state so a resume can prove it is the same."""
        return [{"trial": t.key, "targets": [list(p) for p in t.targets], "grid": list(t.grid)}
                for t in [self.practice] + self.trials]

    # ------------------------------------------------------------ saving
    def _state(self) -> dict:
        return {
            "participant": self.participant,
            "practice_done": self.practice_done,
            "finished": self.finished,
            "checks_done": self.checks_done,
            "resumed": self.resumed,
            "complete": self._all_done(),
            "deal": self.deal_record(),
        }

    def begin(self) -> None:
        if not self.store.has_session():
            self.store.save_state(self._state())

    def mark_practice_done(self) -> None:
        self.practice_done = True
        self.store.save_state(self._state())

    def finish_trial(self, trial: Trial, grid: GridController, timing: TrialTiming) -> tuple[list[dict], dict]:
        tiles, summary = self.rows(trial, grid, timing)
        self.finished.append([trial.block, trial.room])
        self.store.save_trial(tiles, summary, self._state())
        return tiles, summary

    def finish_checks(self, block: Block, rows: list[dict]) -> None:
        self.checks_done.append(block.index)
        self.store.save_checks(rows, self._state())

    def condition(self, block_or_trial) -> str:
        return "baseline" if self.baseline else block_or_trial.condition

    def check_base(self, block: Block) -> dict:
        """The columns every manipulation-check row starts with."""
        return {"participant": self.participant, "session_resumed": int(self.resumed),
                "block": block.index, "condition": self.condition(block), "build": self.build}

    def rows(self, trial: Trial, grid: GridController, timing: TrialTiming) -> tuple[list[dict], dict]:
        spots = dict(trial.targets)
        base = {
            "participant": self.participant, "baseline": int(self.baseline),
            "session_resumed": int(self.resumed), "block": trial.block, "condition": self.condition(trial),
            "room": trial.room, "room_order_in_block": trial.order_in_block,
        }
        tiles = []
        for index, (name, state) in enumerate(zip(trial.grid, grid.tiles), start=1):
            item = self.items[name]
            target = name in spots
            tiles.append({
                **base, "tile": index, "item": name, "label": item.label, "category": item.category,
                "role": "target" if target else "decoy", "spot": spots.get(name, ""),
                "selected": int(state.selected), "correct": int(state.selected == target),
                "first_selected_ms": "" if state.first_selected_ms is None else state.first_selected_ms,
                "last_toggle_ms": "" if state.last_toggle_ms is None else state.last_toggle_ms,
                "toggles": state.toggles, "build": self.build,
            })
        n_targets = len(spots)
        n_decoys = len(trial.grid) - n_targets
        hits = sum(1 for t in tiles if t["role"] == "target" and t["selected"])
        false_alarms = sum(1 for t in tiles if t["role"] == "decoy" and t["selected"])
        # Raw rates here; d' and c use the log-linear corrected rates (scoring.py).
        hit_rate, fa_rate = hits / n_targets, false_alarms / n_decoys
        summary = {
            **base, "targets": n_targets, "decoys": n_decoys, "hits": hits, "false_alarms": false_alarms,
            "hit_rate": f"{hit_rate:.4f}", "false_alarm_rate": f"{fa_rate:.4f}",
            "dprime": f"{dprime(hits, n_targets, false_alarms, n_decoys):.4f}",
            "criterion": f"{criterion(hits, n_targets, false_alarms, n_decoys):.4f}",
            "selected": hits + false_alarms, "grid_ms": grid.finished_ms,
            "study_ms": timing.study_ms, "study_end_frame_ms": f"{timing.study_end_frame_ms:.1f}",
            "study_dropped_frames": "" if timing.study_dropped_frames is None else timing.study_dropped_frames,
            "retention_ms": timing.retention_ms, "filler_answered": timing.filler_answered,
            "filler_correct": timing.filler_correct,
            "filler_mean_rt_ms": "" if timing.filler_mean_rt_ms is None else f"{timing.filler_mean_rt_ms:.0f}",
            "condition_order": ">".join(self.condition(b) for b in self.blocks),
            "room_order": ">".join("+".join(b.rooms) for b in self.blocks),
            "build": self.build,
        }
        return tiles, summary
