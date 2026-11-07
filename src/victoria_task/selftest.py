"""Play a full scripted session with no window and check what got saved.

Runs in the tests and inside the packaged .exe (`MemoryTask.exe --self-test`), so a
build is proven on the operating system it will run on. It writes a log file, since
a packaged windowed app has no console. Real display and mouse behavior still need
a person at the lab computer.
"""
from __future__ import annotations

import csv
import dataclasses
import os
import tempfile
import traceback
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from .app import DONE_RECT, ROOM_ORIGIN, EXPERIMENTER_KEY, Game, QuitSession
from .config import Config
from .session import Session


def _mouse(kind, position):
    return pygame.event.Event(kind, {"pos": position, "button": 1, "rel": (0, 0), "buttons": (1, 0, 0)})


def _key(key):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


class ScriptedGame(Game):
    """Answers every screen automatically, and records all text shown."""

    def __init__(self, *args, participant=1, stop_after_rooms=None, **kwargs):
        super().__init__(*args, fullscreen=False, **kwargs)
        self.participant = participant
        self.stop_after_rooms = stop_after_rooms
        self.rooms_done = 0
        self.queue: list[list] = []
        self.shown: list[str] = []
        self.scored_rounds = 0
        self.screenshot_dir: Path | None = None

    def events(self):
        if self.queue:
            return self.queue.pop(0)
        return []

    def show_text(self, lines):
        self.shown += [text for text, _, _ in lines]
        super().show_text(lines)

    def wait_screen(self, lines, key=None):
        self.queue.append([_key(pygame.K_SPACE if key is None else key)])
        super().wait_screen(lines, key)

    def enter_participant(self):
        return self.participant

    def confirm_existing(self, session):
        return not session.is_complete()

    def study(self, scene):
        result = super().study(scene)
        self._shot(f"{scene.info.name}_blink")
        return result

    def on_placement_start(self, scene, order, thumbs):
        script: list[list] = []
        full_round = len(order) == len(scene.info.objects)
        # Done is locked at first: clicking it now must do nothing.
        script.append([_mouse(pygame.MOUSEBUTTONDOWN, DONE_RECT.center)])
        script.append([_mouse(pygame.MOUSEBUTTONUP, DONE_RECT.center)])
        for index, obj in enumerate(order):
            start = thumbs[obj.id][1].center
            target = (int(obj.center[0] + ROOM_ORIGIN[0]), int(obj.center[1] + ROOM_ORIGIN[1]))
            if full_round and index == 0:  # dropped just outside tolerance: must score 0
                target = (target[0] + (81 if target[0] < 1000 else -81), target[1])
            if full_round and index == 1:  # back to the tray first, then placed properly
                script.append([_mouse(pygame.MOUSEBUTTONDOWN, start)])
                script.append([_mouse(pygame.MOUSEBUTTONUP, (start[0], start[1] - 5))])
            script.append([_mouse(pygame.MOUSEBUTTONDOWN, start)])
            script.append([_mouse(pygame.MOUSEMOTION, target)])
            script.append([_mouse(pygame.MOUSEBUTTONUP, target)])
        script.append([])  # draw one frame with everything placed
        script.append([_mouse(pygame.MOUSEBUTTONDOWN, DONE_RECT.center)])
        self.queue = script

    def placement(self, scene, objects, participant, block_index):
        result = super().placement(scene, objects, participant, block_index)
        self._shot(f"{scene.info.name}_placed")
        if len(objects) == len(scene.info.objects):
            self.scored_rounds += 1
        return result

    def transition(self):
        super().transition()
        self.rooms_done += 1

    def _shot(self, name):
        if self.screenshot_dir:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.screen, self.screenshot_dir / f"{name}.png")


class _StopHere(QuitSession):
    pass


def play(config: Config, assets: Path, data_dir: Path, participant: int, crash_after_room=False, shots=None):
    game = ScriptedGame(config, assets, data_dir, participant=participant)
    game.screenshot_dir = shots
    if crash_after_room:
        original = Session.finish_room

        def stop_after_save(self, *args, **kwargs):
            rows = original(self, *args, **kwargs)
            raise _StopHere
            return rows

        Session.finish_room = stop_after_save
        try:
            game.run()
        except _StopHere:
            pass
        finally:
            Session.finish_room = original
    else:
        game.run()
    shown = game.shown
    pygame.quit()
    return shown


def read_rows(data_dir: Path, participant: int) -> list[dict]:
    with open(data_dir / f"P{participant:03d}_results.csv", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_session(config: Config, assets: Path, data_dir: Path, shots=None) -> list[str]:
    """Return a list of failures. An empty list means everything worked."""
    failures = []

    def expect(condition, message):
        if not condition:
            failures.append(message)

    fast = dataclasses.replace(config, study_seconds=0.05, transition_seconds=0.05)

    # An uninterrupted session.
    shown = play(fast, assets, data_dir, 1, shots=shots)
    rows = read_rows(data_dir, 1)
    expected_rooms = sum(len(rooms) for rooms in config.room_sets)
    expect(len(rows) == 15 * expected_rooms, f"expected {15 * expected_rooms} rows, got {len(rows)}")
    expect({r["session_resumed"] for r in rows} == {"0"}, "uninterrupted session marked as resumed")
    expect({r["condition"] for r in rows} == set(config.conditions), "not all conditions recorded")
    per_room: dict[str, int] = {}
    for row in rows:
        per_room[row["room"]] = per_room.get(row["room"], 0) + int(row["score"])
    expect(all(v == 14 for v in per_room.values()), f"each room should score 14/15, got {per_room}")
    # One object per room goes back to the tray first: down/up in the tray, then the real drop.
    twice = [r for r in rows if r["moves"] == "2"]
    expect(len(twice) == expected_rooms, f"tray return not counted: {len(twice)} rows with 2 moves")
    expect(all(r["moves"] in ("1", "2") for r in rows), "unexpected move count")
    expect(all(r["placement_order"] for r in rows), "missing placement order")

    # Nothing shown on any screen may reveal a condition.
    labels = {f"condition {c}".lower() for c in config.conditions} | set(config.conditions)
    leaks = [t for t in shown if t in labels or "condition" in t.lower()]
    expect(not leaks, f"condition shown on screen: {leaks}")
    expect("Please wait for the experimenter" in shown, "experimenter pause was not shown")

    # Personal details: results contain the study number only.
    header = set(rows[0])
    expect(not {"name", "email", "birthdate", "age"} & header, "personal detail column in results")

    # Crash after the first room, then resume.
    play(fast, assets, data_dir, 2, crash_after_room=True)
    first = read_rows(data_dir, 2)
    expect(len(first) == 15, f"crash should leave 15 saved rows, got {len(first)}")
    expect(not Session(fast, data_dir, 2).is_complete(), "crashed session reported as complete")
    play(fast, assets, data_dir, 2)
    final = read_rows(data_dir, 2)
    expect(len(final) == 15 * expected_rooms, f"resume left {len(final)} rows")
    expect(len({(r["block"], r["room"], r["object"]) for r in final}) == len(final), "resume duplicated rows")
    expect(any(r["session_resumed"] == "1" for r in final), "resumed rows are not marked")
    expect(Session(fast, data_dir, 2).is_complete(), "resumed session not marked complete")
    before = (data_dir / "P002_results.csv").read_bytes()
    Session(fast, data_dir, 2)
    expect((data_dir / "P002_results.csv").read_bytes() == before, "reopening changed finished data")
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
