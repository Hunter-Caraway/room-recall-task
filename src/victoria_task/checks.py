"""Post-block manipulation checks, with no graphics library.

After the last room of every block the participant does a backward digit span,
then rates the noise on 0-100 sliders. The display shows the screens; the logic
here decides what to show, scores it and turns it into data rows.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

# Slider geometry on the 1920x1080 canvas.
SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y = 460, 1460, 560
SLIDER_HIT_HALF_HEIGHT = 40  # px above and below the line that still count as a click on it
CONTINUE_RECT = (860, 760, 200, 90)  # x, y, width, height

SPAN_INSTRUCTIONS = [
    ("Numbers in reverse", "title"),
    ("Some numbers will appear one at a time.", "body"),
    ("When they stop, type them in reverse order, last number first, then press Enter.", "body"),
    ("For example, if you see 3  8  1, type 1 8 3.", "body"),
    ("Press the space bar to begin", "muted"),
]
SLIDER_INSTRUCTIONS = [
    ("A few questions", "title"),
    ("Click on each line to give your answer, then press Continue.", "body"),
    ("Press the space bar to begin", "muted"),
]


def sequence(participant: int, block: int, length: int, trial: int) -> list[int]:
    """Digits 1-9 with no repeats, the same for a given participant, block and trial."""
    return random.Random(f"span/{participant}/{block}/{length}/{trial}").sample(range(1, 10), length)


@dataclass(frozen=True)
class SpanTrial:
    length: int
    trial: int  # 1-based within the length
    digits: tuple[int, ...]
    response: str
    rt_ms: int

    @property
    def correct(self) -> bool:
        return self.response == "".join(str(d) for d in reversed(self.digits))


@dataclass
class DigitSpan:
    """Backward digit span: trials_per_length trials at each length, rising from
    start until every trial at one length is wrong, or max is passed."""
    participant: int
    block: int
    start: int
    maximum: int
    trials_per_length: int
    trials: list[SpanTrial] = field(default_factory=list)

    def next_digits(self) -> tuple[int, int, list[int]] | None:
        """(length, trial, digits) for the next trial, or None when finished."""
        length = self.start + len(self.trials) // self.trials_per_length
        trial = len(self.trials) % self.trials_per_length + 1
        if trial == 1 and self.trials:
            previous = [t for t in self.trials if t.length == length - 1]
            if not any(t.correct for t in previous):
                return None
        if length > self.maximum:
            return None
        return length, trial, sequence(self.participant, self.block, length, trial)

    def record(self, length: int, trial: int, digits: list[int], response: str, rt_ms: int) -> None:
        self.trials.append(SpanTrial(length, trial, tuple(digits), response, rt_ms))

    @property
    def span(self) -> int:
        """Longest length with at least one trial right; 0 if none."""
        return max((t.length for t in self.trials if t.correct), default=0)

    @property
    def total_correct(self) -> int:
        return sum(t.correct for t in self.trials)


@dataclass
class SliderController:
    """A 0-100 line with no starting marker, so the first answer is not anchored.
    Continue works only once the participant has clicked on the line."""
    started_ms: int
    value: int | None = None
    first_click_ms: int | None = None
    dragging: bool = False
    finished_ms: int | None = None

    @staticmethod
    def x_for(value: int) -> float:
        return SLIDER_LEFT + (SLIDER_RIGHT - SLIDER_LEFT) * value / 100

    def _set(self, x: float, now_ms: int) -> None:
        fraction = (min(max(x, SLIDER_LEFT), SLIDER_RIGHT) - SLIDER_LEFT) / (SLIDER_RIGHT - SLIDER_LEFT)
        self.value = round(fraction * 100)
        if self.first_click_ms is None:
            self.first_click_ms = now_ms - self.started_ms

    def press(self, point: tuple[float, float], now_ms: int) -> bool:
        """Returns True when Continue was pressed and accepted."""
        x, y = point
        cx, cy, cw, ch = CONTINUE_RECT
        if cx <= x < cx + cw and cy <= y < cy + ch:
            if self.value is not None:
                self.finished_ms = now_ms - self.started_ms
                return True
            return False
        if SLIDER_LEFT - 30 <= x <= SLIDER_RIGHT + 30 and abs(y - SLIDER_Y) <= SLIDER_HIT_HALF_HEIGHT:
            self._set(x, now_ms)
            self.dragging = True
        return False

    def move(self, point: tuple[float, float], now_ms: int) -> None:
        if self.dragging:
            self._set(point[0], now_ms)

    def release(self, point: tuple[float, float], now_ms: int) -> None:
        if self.dragging:
            self._set(point[0], now_ms)
        self.dragging = False


@dataclass(frozen=True)
class SliderAnswer:
    id: str
    value: int
    first_click_ms: int
    rt_ms: int  # from the question appearing to Continue


def check_rows(base: dict, span: DigitSpan | None, sliders: list[SliderAnswer]) -> list[dict]:
    """One row per digit-span trial, one per span summary score, one per slider."""
    rows = []
    blank = {"trial": "", "length": "", "sequence": "", "response": "", "correct": "",
             "value": "", "first_click_ms": "", "rt_ms": ""}
    if span is not None:
        for t in span.trials:
            rows.append(base | blank | {
                "measure": "digit_span_trial", "trial": t.trial, "length": t.length,
                "sequence": "".join(map(str, t.digits)), "response": t.response,
                "correct": int(t.correct), "rt_ms": t.rt_ms,
            })
        rows.append(base | blank | {"measure": "digit_span_longest", "value": span.span})
        rows.append(base | blank | {"measure": "digit_span_total_correct", "value": span.total_correct})
    for answer in sliders:
        rows.append(base | blank | {"measure": answer.id, "value": answer.value,
                                    "first_click_ms": answer.first_click_ms, "rt_ms": answer.rt_ms})
    return rows
