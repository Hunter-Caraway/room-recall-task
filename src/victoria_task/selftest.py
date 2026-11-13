"""Play whole scripted sessions with no window and check what got saved.

Uses the real session flow (flow.py), deal, grid logic and data files, with a
scripted display in place of PsychoPy or pygame. Run it on the lab computer with
`Self Test.bat` or `python run_task.py --self-test`; it writes selftest.log.
Real display and mouse behaviour still need a person at the lab computer.
"""
from __future__ import annotations

import csv
import itertools
import tempfile
import traceback
from collections import Counter
from pathlib import Path

from .checks import CONTINUE_RECT, SLIDER_Y, SliderController
from .config import Config
from .deal import deal
from .filler import FillerResult
from .flow import REMEMBER, WAIT_TEXT, Experiment, QuitSession
from .grid import DONE_RECT, GridController
from .schedule import build_schedule
from .session import Session
from .stimuli import load_items, load_room, pool

DONE_POINT = (DONE_RECT[0] + DONE_RECT[2] / 2, DONE_RECT[1] + DONE_RECT[3] / 2)
CONTINUE_POINT = (CONTINUE_RECT[0] + CONTINUE_RECT[2] / 2, CONTINUE_RECT[1] + CONTINUE_RECT[3] / 2)
SPAN_RIGHT_UP_TO = 4  # the script answers digit-span trials right up to this length
SLIDER_ANSWER = 65
FALSE_ALARMS = 2  # decoys the script picks in every grid
DEAL_CHECK_PARTICIPANTS = 126  # every participant number up to this must deal


class ScriptedDisplay:
    """Answers every screen automatically and records what was shown.

    In each grid it picks every target but one, picks two decoys, and picks then
    unpicks a third decoy, so hits, false alarms and toggles are all known.
    """

    def __init__(self, participant: int, items):
        self.participant = participant
        self.items = items
        self.clock = itertools.count(0, 16)
        self.shown: list[str] = []
        self.holds: list[int] = []
        self.prepared: dict[str, tuple] = {}
        self.studied: list[str] = []

    def now_ms(self) -> int:
        return next(self.clock)

    def message(self, lines, key, hold_ms=0):
        self.shown += [text for text, _ in lines]
        if any(text == WAIT_TEXT for text, _ in lines):
            self.holds.append(hold_ms)

    def enter_participant(self, baseline=False):
        return self.participant, baseline

    def ask_resume(self, number):
        return True

    def prepare(self, key, room, tiles):
        self.prepared[key] = (room.size, [t.size for t in tiles])

    def study(self, key, seconds):
        self.studied.append(key)
        return int(seconds * 1000), 16.7, 0

    def filler(self, items, seconds):
        # Answer five sums, getting the last one wrong.
        answers = [p.is_true for p in items[:4]] + [not items[4].is_true]
        result = FillerResult()
        for said, problem in zip(answers, items):
            result.answer(problem, said, 900)
        return result

    def grid(self, key, controller: GridController):
        targets = [i for i, n in enumerate(controller.names) if self.items[n].pool.endswith("target")]
        decoys = [i for i, n in enumerate(controller.names) if i not in targets]
        for index in targets[1:] + decoys[:FALSE_ALARMS]:
            assert not controller.press(controller.point_of(index), self.now_ms())
        flip = decoys[FALSE_ALARMS]
        controller.press(controller.point_of(flip), self.now_ms())
        controller.press(controller.point_of(flip), self.now_ms())
        assert controller.press(DONE_POINT, self.now_ms()), "Done did not finish the grid"

    def digit_span(self, digits, digit_ms, gap_ms):
        backward = "".join(str(d) for d in reversed(digits))
        return (backward if len(digits) <= SPAN_RIGHT_UP_TO else backward[::-1]), 1500

    def slider(self, question, low, high, controller: SliderController):
        self.shown.append(question)
        assert not controller.press(CONTINUE_POINT, self.now_ms()), "Continue worked before an answer"
        controller.press((SliderController.x_for(40), SLIDER_Y + 10), self.now_ms())
        controller.move((SliderController.x_for(SLIDER_ANSWER), SLIDER_Y + 200), self.now_ms())
        controller.release((SliderController.x_for(SLIDER_ANSWER), SLIDER_Y + 200), self.now_ms())
        assert controller.press(CONTINUE_POINT, self.now_ms()), "Continue did not accept an answer"


class _StopHere(QuitSession):
    pass


def play(config: Config, assets: Path, data_dir: Path, participant: int, crash_after_trial=False,
         baseline=False) -> ScriptedDisplay:
    items = load_items(assets)
    display = ScriptedDisplay(participant, items)
    experiment = Experiment(config, assets, data_dir, display, baseline=baseline, build="selftest")
    if not crash_after_trial:
        experiment.run()
        return display
    original = Session.finish_trial

    def stop_after_save(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise _StopHere

    Session.finish_trial = stop_after_save
    try:
        experiment.run()
    except _StopHere:
        pass
    finally:
        Session.finish_trial = original
    return display


def read_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_assets(config: Config, assets: Path) -> list[str]:
    """Every room's spots lie inside its picture, the pools are big enough, and every
    participant number up to DEAL_CHECK_PARTICIPANTS gets a deal that fits."""
    failures = []
    items = load_items(assets)
    rooms = {name: load_room(assets, name) for name in dict.fromkeys([config.practice_room, *config.rooms])}
    for room in rooms.values():
        if not room.image.exists():
            failures.append(f"{room.name}: missing {room.image.name}")
        for spot in room.spots:
            if not (0 <= spot.x <= room.width and 0 <= spot.y <= room.height):
                failures.append(f"{room.name}/{spot.id}: outside the picture")
        if len({s.id for s in room.spots}) != len(room.spots):
            failures.append(f"{room.name}: spot ids repeat")
    targets, decoys = pool(items, "target"), pool(items, "decoy")
    for item in targets:
        if not any(s.fits(item) for r in config.rooms for s in rooms[r].spots):
            failures.append(f"{item.name}: fits no spot in any scored room")
    trials = len(config.conditions) * len(config.rooms)
    need = trials * config.tiles - len(targets)
    if len(decoys) < need:
        failures.append(f"{len(decoys)} decoys, a session needs {need}")
    names = [i.name for i in items.values()]
    if len(set(names)) != len(names):
        failures.append("object names repeat")
    if not failures:
        for participant in range(1, DEAL_CHECK_PARTICIPANTS + 1):
            blocks = build_schedule(participant, config.conditions, config.rooms)
            try:
                deal(participant, blocks, rooms, targets, decoys, config.tiles)
            except Exception as error:  # noqa: BLE001 - reported, not raised
                failures.append(f"participant {participant}: {error}")
                break
    return failures


def check_session(config: Config, assets: Path, data_dir: Path) -> list[str]:
    """Return a list of failures. An empty list means everything worked."""
    failures = check_assets(config, assets)
    if failures:
        return failures

    def expect(condition, message):
        if not condition:
            failures.append(message)

    items = load_items(assets)
    n_trials = len(config.conditions) * len(config.rooms)
    blocks = len(config.conditions)
    n_targets = len(pool(items, "target"))
    hold = int(config.block_hold_seconds * 1000)

    # An uninterrupted session.
    display = play(config, assets, data_dir, 1)
    trials = read_rows(data_dir / "P001_trials.csv")
    tiles = read_rows(data_dir / "P001_tiles.csv")
    expect(len(trials) == n_trials, f"expected {n_trials} trial rows, got {len(trials)}")
    expect(len(tiles) == n_trials * config.tiles, f"expected {n_trials * config.tiles} tile rows, got {len(tiles)}")
    expect({r["session_resumed"] for r in trials} == {"0"}, "uninterrupted session marked as resumed")
    expect({r["condition"] for r in trials} == set(config.conditions), "not all conditions recorded")
    per_block = Counter((r["block"], r["room"]) for r in trials)
    expect(len(per_block) == n_trials, "a room repeats within a block")
    for block in {r["block"] for r in trials}:
        expect(sorted(r["room"] for r in trials if r["block"] == block) == sorted(config.rooms),
               f"block {block} does not show every room once")
    target_rows = [r for r in tiles if r["role"] == "target"]
    decoy_rows = [r for r in tiles if r["role"] == "decoy"]
    expect(sorted(r["item"] for r in target_rows) == sorted(i.name for i in pool(items, "target")),
           "not every target photo was a target exactly once")
    expect(len({r["item"] for r in decoy_rows}) == len(decoy_rows), "a decoy appeared twice")
    expect(not {r["item"] for r in decoy_rows} & {r["item"] for r in target_rows}, "an item was target and decoy")
    expect(all(items[r["item"]].pool == "decoy" for r in decoy_rows), "a non-decoy item filled a grid")
    counts = Counter(int(r["targets"]) for r in trials)
    low = n_targets // n_trials
    expect(set(counts) <= {low, low + 1} and sum(k * v for k, v in counts.items()) == n_targets,
           f"targets per trial uneven: {dict(counts)}")
    for row in trials:
        k = int(row["targets"])
        expect(row["hits"] == str(k - 1) and row["false_alarms"] == str(FALSE_ALARMS),
               f"{row['block']}/{row['room']}: hits {row['hits']}, false alarms {row['false_alarms']}")
        expect(int(row["targets"]) + int(row["decoys"]) == config.tiles, "grid not full")
        expect(row["dprime"] != "" and float(row["dprime"]) > 0, "d' missing or not positive")
        expect(row["grid_ms"] != "" and int(row["grid_ms"]) > 0, "grid time missing")
        expect(config.retention_seconds <= 0 or (row["filler_answered"] == "5" and row["filler_correct"] == "4"
                                                 and row["filler_mean_rt_ms"] == "900"), "filler results not saved")
    for row in tiles:
        expect(row["correct"] == str(int((row["selected"] == "1") == (row["role"] == "target"))),
               "tile correct column wrong")
        if row["selected"] == "1":
            expect(row["first_selected_ms"] != "", "selected tile has no selection time")
        expect(bool(row["spot"]) == (row["role"] == "target"), "spot recorded wrongly")
    expect(sum(1 for r in tiles if r["toggles"] == "2") == n_trials, "pick-then-unpick not recorded")
    expect(display.shown.count("Practice room") == 1, f"practice shown {display.shown.count('Practice room')} times")
    expect(display.holds == [hold] * blocks, f"experimenter waits {display.holds}")
    expect(display.shown.count(REMEMBER) == 1 + n_trials, "an instruction screen lacks the remember line")
    expect(len(display.studied) == 1 + n_trials, "a room was not studied")
    expect(all(len(sizes) == config.tiles for _, sizes in display.prepared.values()), "a grid lacked tiles")

    # Manipulation checks after every block.
    checks = read_rows(data_dir / "P001_checks.csv")
    by_block: dict[str, dict[str, list[dict]]] = {}
    for row in checks:
        by_block.setdefault(row["block"], {}).setdefault(row["measure"], []).append(row)
    expect(sorted(by_block) == [str(b) for b in range(1, blocks + 1)], f"checks saved for blocks {sorted(by_block)}")
    for block, measures in by_block.items():
        trials_ = measures.get("digit_span_trial", [])
        right = 2 * (SPAN_RIGHT_UP_TO - config.span_start + 1)
        expect(len(trials_) == right + 2, f"block {block}: {len(trials_)} digit-span trials")
        expect(measures.get("digit_span_longest", [{}])[0].get("value") == str(SPAN_RIGHT_UP_TO),
               f"block {block}: wrong longest span")
        for question_id, *_ in config.slider_questions:
            answer = measures.get(question_id, [{}])[0]
            expect(answer.get("value") == str(SLIDER_ANSWER), f"block {block}: {question_id} not saved")

    # Nothing on screen may reveal a condition.
    leaks = [t for t in display.shown if t in set(config.conditions) or "condition" in t.lower()]
    expect(not leaks, f"condition shown on screen: {leaks}")
    header = set(trials[0]) | set(tiles[0]) | set(checks[0])
    expect(not {"name", "email", "birthdate", "age"} & header, "personal detail column in results")

    # Crash after the first trial, then resume.
    play(config, assets, data_dir, 2, crash_after_trial=True)
    first = read_rows(data_dir / "P002_trials.csv")
    expect(len(first) == 1, f"crash should leave 1 saved trial, got {len(first)}")
    display = play(config, assets, data_dir, 2)
    final = read_rows(data_dir / "P002_trials.csv")
    expect(len(final) == n_trials, f"resume left {len(final)} trials")
    expect(len({(r["block"], r["room"]) for r in final}) == n_trials, "resume duplicated a trial")
    expect(len(read_rows(data_dir / "P002_tiles.csv")) == n_trials * config.tiles, "resume lost tile rows")
    expect(any(r["session_resumed"] == "1" for r in final), "resumed rows are not marked")
    expect("Practice room" not in display.shown, "resume repeated the practice")
    expect(len(display.holds) == blocks, "resume skipped the experimenter wait")
    expect(Session(config, data_dir, 2, items, {n: load_room(assets, n) for n in
                                                [config.practice_room, *config.rooms]}).is_complete(),
           "resumed session not marked complete")

    # The no-study baseline group: separate files, no study, no checks, no condition.
    display = play(config, assets, data_dir, 3, baseline=True)
    base = read_rows(data_dir / "B003_trials.csv")
    expect(len(base) == n_trials, f"baseline wrote {len(base)} trials")
    expect({r["condition"] for r in base} == {"baseline"}, "baseline rows carry a condition")
    expect({r["study_ms"] for r in base} == {"0"}, "baseline participants saw a scored room")
    expect(not (data_dir / "B003_checks.csv").exists(), "baseline did manipulation checks")
    expect(display.shown.count("Practice room") == 1, "baseline should practise once")
    expect(not (data_dir / "P003_trials.csv").exists(), "baseline wrote a participant file")
    return failures


def run_self_test(assets: Path, config: Config, log_path: Path) -> int:
    try:
        with tempfile.TemporaryDirectory() as temp:
            failures = check_session(config, assets, Path(temp))
    except Exception:
        failures = [traceback.format_exc()]
    text = "SELF TEST PASSED\n" if not failures else "SELF TEST FAILED\n" + "\n".join(failures) + "\n"
    log_path.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not failures else 1
