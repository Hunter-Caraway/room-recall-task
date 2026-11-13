"""The order of screens in a session, independent of any graphics library.

A Display draws screens and collects input. PsychoPy and pygame displays run the
real task; the self-test uses a scripted display with no window. All of them run
this same flow, so the self-test checks the real sequence of screens and saves.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .checks import SLIDER_INSTRUCTIONS, SPAN_INSTRUCTIONS, DigitSpan, SliderAnswer, SliderController, check_rows
from .composite import compose, tile
from .config import Config
from .deal import Trial
from .filler import FillerResult, Problem, problems
from .grid import TILE, GridController
from .schedule import Block
from .session import Session, TrialTiming
from .stimuli import Room, load_items, load_room

END_TEXT = "That's the end of the task. Thank you!"
WAIT_TEXT = "Please wait for the experimenter"
REMEMBER = "Remember which objects are in the room."

# A line of text and its style: "title", "body", "muted" or "entry".
Lines = list[tuple[str, str]]


class QuitSession(Exception):
    """The experimenter pressed Ctrl+Shift+Q. Everything finished so far is saved."""


class Display(Protocol):
    def now_ms(self) -> int: ...
    def message(self, lines: Lines, key: str, hold_ms: int = 0) -> None:
        """Show lines until `key` ("space" or "f8") is pressed; the key does nothing
        until the screen has been up for hold_ms."""
    def enter_participant(self, baseline: bool = False) -> tuple[int, bool]: ...
    def ask_resume(self, number: int) -> bool:
        """F8 resumes the unfinished session; Esc returns False to type another number."""
    def prepare(self, key: str, room, tiles: list) -> None:
        """Load one trial's pictures (PIL images): the furnished room and the grid tiles."""
    def study(self, key: str, seconds: float) -> tuple[int, float, int | None]:
        """Show the room for `seconds`, then a blank screen. Returns (measured ms, length
        in ms of the frame the cut landed on, dropped frames or None if unmeasured)."""
    def filler(self, items: list[Problem], seconds: float) -> FillerResult: ...
    def grid(self, key: str, controller: GridController) -> None:
        """Run the recognition grid until the controller records Done."""
    def digit_span(self, digits: list[int], digit_ms: int, gap_ms: int) -> tuple[str, int]:
        """Show the digits one at a time, then collect the typed answer. Returns
        (typed digits, ms from the answer screen appearing to Enter)."""
    def slider(self, question: str, low: str, high: str, controller: SliderController) -> None:
        """Run a 0-100 slider until the controller records Continue."""


class Experiment:
    def __init__(self, config: Config, assets: Path, data_dir: Path, display: Display,
                 baseline: bool = False, build: str = "test"):
        self.config = config
        self.assets = Path(assets)
        self.data_dir = Path(data_dir)
        self.display = display
        self.baseline = baseline
        self.build = build
        self.items = load_items(self.assets)
        self.rooms: dict[str, Room] = {name: load_room(self.assets, name) for name in self.room_names()}
        self._room_pictures: dict[str, object] = {}

    def room_names(self) -> list[str]:
        return list(dict.fromkeys([self.config.practice_room, *self.config.rooms]))

    # ------------------------------------------------------------ pictures
    def room_picture(self, name: str):
        from PIL import Image

        if name not in self._room_pictures:
            with Image.open(self.rooms[name].image) as image:
                self._room_pictures[name] = image.convert("RGB")
        return self._room_pictures[name]

    def prepare(self, trial: Trial) -> None:
        room = self.rooms[trial.room]
        spots = {s.id: s for s in room.spots}
        placed = [(self.items[name], spots[spot]) for name, spot in trial.targets]
        picture = compose(self.room_picture(trial.room), placed)
        tiles = [tile(self.items[name], TILE) for name in trial.grid]
        self.display.prepare(trial.key, picture, tiles)

    # ------------------------------------------------------------ screens
    def choose_session(self) -> Session:
        while True:
            number, self.baseline = self.display.enter_participant(self.baseline)
            session = Session(self.config, self.data_dir, number, self.items, self.rooms, self.build,
                              baseline=self.baseline)
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
                ("Next set", "title"),
                ("You will see a set of objects. Some of them were in a room you have not seen.", "body"),
                ("Click every object you think was in that room, then press Done.", "body"),
            ]
        else:
            lines = [(heading, "title"), (REMEMBER, "body"),
                     (f"You will see a room for {int(self.config.study_seconds)} seconds.", "body")]
            if retention > 0:
                lines.append(("Then you will check some quick sums: press Y if a sum is right, "
                              "N if it is wrong.", "body"))
            lines += [("Then you will see a set of objects.", "body"),
                      ("Click every object that was in the room, then press Done.", "body")]
        self.display.message(lines + [("Press the space bar to begin", "muted")], "space")

    def play(self, session: Session, trial: Trial, practice: bool) -> tuple[GridController, TrialTiming]:
        # Baseline participants practise normally, then guess in the scored trials.
        guessing = self.baseline and not practice
        retention = self.config.practice_retention_seconds if practice else self.config.retention_seconds
        self.prepare(trial)
        self.instructions(practice, guessing, retention)
        study_ms, end_frame_ms, dropped = 0, 0.0, None
        filler = FillerResult()
        retention_ms = 0
        if not guessing:
            study_ms, end_frame_ms, dropped = self.display.study(trial.key, self.config.study_seconds)
            if retention > 0:
                start = self.display.now_ms()
                filler = self.display.filler(problems(session.participant, trial.block, trial.room), retention)
                retention_ms = self.display.now_ms() - start
        controller = GridController(list(trial.grid), self.config.grid_columns, self.config.grid_rows,
                                    self.display.now_ms())
        self.display.grid(trial.key, controller)
        timing = TrialTiming(study_ms=study_ms, study_end_frame_ms=end_frame_ms, study_dropped_frames=dropped,
                             retention_ms=retention_ms, filler_answered=filler.answered,
                             filler_correct=filler.correct, filler_mean_rt_ms=filler.mean_rt_ms)
        return controller, timing

    def wait_for_experimenter(self) -> None:
        """Before each block: the experimenter sets the noise. F8 works only after the
        hold, so the participant has settled into the noise before the first room."""
        hold = 0 if self.baseline else int(self.config.block_hold_seconds * 1000)
        self.display.message([(WAIT_TEXT, "title")], "f8", hold_ms=hold)

    def checks(self, session: Session, block: Block) -> None:
        """Backward digit span, then the sliders. Saved as one block of rows."""
        config = self.config
        self.display.message(SPAN_INSTRUCTIONS, "space")
        span = DigitSpan(session.participant, block.index, config.span_start, config.span_max,
                         config.span_trials)
        while (step := span.next_digits()) is not None:
            length, trial, digits = step
            response, rt_ms = self.display.digit_span(digits, config.span_digit_ms, config.span_gap_ms)
            span.record(length, trial, digits, response, rt_ms)
        answers = []
        if config.slider_questions:
            self.display.message(SLIDER_INSTRUCTIONS, "space")
        for question_id, question, low, high in config.slider_questions:
            controller = SliderController(self.display.now_ms())
            self.display.slider(question, low, high, controller)
            answers.append(SliderAnswer(question_id, controller.value, controller.first_click_ms,
                                        controller.finished_ms))
        session.finish_checks(block, check_rows(session.check_base(block), span, answers))

    def run(self) -> None:
        session = self.choose_session()
        if session.needs_practice():
            self.play(session, session.practice, practice=True)  # practice is never saved
            session.mark_practice_done()
        for block in session.blocks:
            left = session.trials_left(block)
            if not left and not session.needs_checks(block):
                continue
            self.wait_for_experimenter()
            for trial in left:
                controller, timing = self.play(session, trial, practice=False)
                session.finish_trial(trial, controller, timing)
            if session.needs_checks(block):
                self.checks(session, block)
        self.display.message([
            (END_TEXT, "title"),
            ("Please let the experimenter know you have finished.", "muted"),
        ], "f8")
