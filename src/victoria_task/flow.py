"""The order of screens in a session, independent of any graphics library.

A Display draws screens and collects input. The PsychoPy display runs the real
task; the self-test uses a scripted display with no window. Both run this same
flow, so the self-test checks the real sequence of screens and saves.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .config import Config
from .filler import FillerResult, Problem, problems
from .layout import ICON_PX, Icon, PlacementController, load_icon
from .session import PlacementRound, RoomInfo, RoomTiming, Session, load_room, tray_order

PAUSE_TEXT = "Please wait for the experimenter"
END_TEXT = "That's the end of the task. Thank you!"

# A line of text and its style: "title", "body", "muted" or "entry".
Lines = list[tuple[str, str]]


class QuitSession(Exception):
    """The experimenter pressed Ctrl+Shift+Q. Everything finished so far is saved."""


class Display(Protocol):
    def now_ms(self) -> int: ...
    def message(self, lines: Lines, key: str) -> None:
        """Show lines until `key` ("space" or "f8") is pressed."""
    def enter_participant(self) -> int: ...
    def ask_resume(self, number: int) -> bool:
        """F8 resumes the unfinished session; Esc returns False to type another number."""
    def prepare(self, room: RoomInfo, icons: dict[str, Icon]) -> None:
        """Load a room's pictures before it is needed."""
    def study(self, room: RoomInfo, seconds: float, cut_to_empty: bool) -> tuple[int, float, int | None]:
        """Show the full room for `seconds`. Returns (measured ms, length in ms of the
        frame the cut landed on, dropped frames or None if unmeasured)."""
    def filler(self, items: list[Problem], seconds: float) -> FillerResult: ...
    def placement(self, room: RoomInfo, controller: PlacementController) -> None:
        """Run drag-and-drop until the controller records Done."""
    def transition(self, seconds: float) -> None: ...


class Experiment:
    def __init__(self, config: Config, assets: Path, data_dir: Path, display: Display,
                 baseline: bool = False, build: str = "test"):
        self.config = config
        self.assets = Path(assets)
        self.data_dir = Path(data_dir)
        self.display = display
        self.baseline = baseline
        self.build = build
        self.rooms: dict[str, RoomInfo] = {}
        self.icons: dict[str, dict[str, Icon]] = {}

    # ------------------------------------------------------------ loading
    def room(self, name: str) -> RoomInfo:
        if name not in self.rooms:
            info = load_room(self.assets, name)
            base = self.assets / "rooms" / name
            self.rooms[name] = info
            self.icons[name] = {o.id: load_icon(base / o.icon) for o in info.objects}
            self.display.prepare(info, self.icons[name])
        return self.rooms[name]

    def all_room_names(self) -> list[str]:
        names = [self.config.practice_room]
        for room_set in self.config.room_sets:
            names += [n for n in room_set if n not in names]
        return names

    # ------------------------------------------------------------ screens
    def choose_session(self) -> Session:
        while True:
            number = self.display.enter_participant()
            session = Session(self.config, self.data_dir, number, self.build, baseline=self.baseline)
            if session.store.has_session():
                if session.is_complete():
                    self.display.message([
                        (f"Participant {number} has already finished.", "title"),
                        ("Their data has not been changed. Press F8 to enter another number.", "muted"),
                    ], "f8")
                    continue
                if not self.display.ask_resume(number):
                    continue
            session.begin()
            return session

    def instructions(self, practice: bool, guessing: bool, retention: float) -> None:
        heading = "Practice room" if practice else "Next room"
        if guessing:
            lines = [
                (heading, "title"),
                ("You will see a room and some objects in a tray.", "body"),
                ("Drag each object to where you think it belongs in the room.", "body"),
                ("When every object is placed, press Done.", "body"),
            ]
        else:
            lines = [
                (heading, "title"),
                (f"You will see a room for {int(self.config.study_seconds)} seconds. "
                 "Remember where everything is.", "body"),
            ]
            if retention > 0:
                lines.append(("Then you will check some quick sums: press Y if a sum is right, "
                              "N if it is wrong.", "body"))
            lines += [
                ("Then some objects will be gone from the room.", "body"),
                ("Drag each object from the tray back to where it was.", "body"),
                ("When every object is placed, press Done.", "body"),
            ]
        self.display.message(lines + [("Press the space bar to begin", "muted")], "space")

    def play_room(self, session: Session, name: str, objects, block_index: int,
                  practice: bool) -> tuple[PlacementRound, RoomTiming]:
        info = self.room(name)
        # Baseline participants practise normally, then guess in the scored rooms.
        guessing = self.baseline and not practice
        retention = self.config.practice_retention_seconds if practice else self.config.retention_seconds
        self.instructions(practice, guessing, retention)
        study_ms, end_frame_ms, dropped = 0, 0.0, None
        filler = FillerResult()
        retention_ms = 0
        if not guessing:
            study_ms, end_frame_ms, dropped = self.display.study(
                info, self.config.study_seconds, cut_to_empty=retention <= 0)
            if retention > 0:
                start = self.display.now_ms()
                filler = self.display.filler(problems(session.participant, block_index, name), retention)
                retention_ms = self.display.now_ms() - start
        order = tray_order(session.participant, block_index, name, list(objects))
        round_ = PlacementRound(info, list(objects), self.display.now_ms())
        controller = PlacementController(round_, order, self.icons[name])
        self.display.placement(info, controller)
        timing = RoomTiming(
            finished_ms=controller.finished_ms, study_ms=study_ms, study_end_frame_ms=end_frame_ms,
            study_dropped_frames=dropped, retention_ms=retention_ms,
            filler_answered=filler.answered, filler_correct=filler.correct, icon_px=ICON_PX,
        )
        return round_, timing

    def run(self) -> None:
        session = self.choose_session()
        if not session.practice_done:
            practice = self.room(self.config.practice_room)
            self.play_room(session, practice.name, practice.objects[: self.config.practice_objects],
                           0, practice=True)
            session.mark_practice_done()  # practice results are never written to the data
            self.display.transition(self.config.transition_seconds)
        first_room = True
        while (step := session.next_room()) is not None:
            block, name, order = step
            # Pause at each new block, and on the first room after any restart, so
            # the experimenter can set the noise. Baseline sessions have no noise.
            if not self.baseline and (session.starts_block() or first_room):
                self.display.message([(PAUSE_TEXT, "title")], "f8")
            first_room = False
            info = self.room(name)
            round_, timing = self.play_room(session, name, info.objects, block.index, practice=False)
            session.finish_room(block, order, round_, timing)
            if session.next_room() is not None:
                self.display.transition(self.config.transition_seconds)
        self.display.message([
            (END_TEXT, "title"),
            ("Please let the experimenter know you have finished.", "muted"),
        ], "f8")
