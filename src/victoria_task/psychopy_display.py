"""The PsychoPy display: draws every screen and reads the keyboard and mouse.

All positions are canvas coordinates (1920x1080, top left origin, y down, see
layout.py). The canvas is scaled to fit the real screen, with black bars if the
shape differs, so object positions mean the same on every computer.

Mouse buttons and keys come straight from the pyglet window's event handlers, not
from polling, so a click shorter than one display frame is never missed.
"""
from __future__ import annotations

from pathlib import Path

from psychopy import core, event, logging, visual

from .checks import CONTINUE_RECT, SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y, SliderController
from .filler import FillerResult, Problem
from .flow import QuitSession
from .grid import CANVAS, DONE_RECT, PROMPT, PROMPT_Y, ROOM_ORIGIN, ROOM_SIZE, GridController


def rgb(r, g, b):
    """0-255 colour to PsychoPy's -1..1 range."""
    return [c / 127.5 - 1 for c in (r, g, b)]


BG = rgb(18, 18, 20)
SELECTED = rgb(250, 200, 60)
TILE_EDGE = rgb(90, 92, 96)
TEXT = rgb(232, 232, 228)
MUTED = rgb(160, 160, 158)
ENTRY = rgb(250, 220, 130)
BUTTON = rgb(70, 140, 90)
BUTTON_OFF = rgb(70, 72, 76)
STYLES = {"title": (44, TEXT), "body": (30, TEXT), "muted": (28, MUTED), "entry": (44, ENTRY),
          "digit": (150, TEXT)}


class PsychoPyDisplay:
    def __init__(self, assets: Path, fullscreen: bool = True, screenshots: Path | None = None):
        logging.console.setLevel(logging.WARNING)
        self.assets = Path(assets)
        self.win = visual.Window(
            size=CANVAS, fullscr=fullscreen, units="pix", winType="pyglet", color=BG,
            allowGUI=not fullscreen, checkTiming=fullscreen,
        )
        self.win.mouseVisible = True
        width, height = self.win.size
        self.scale = min(width / CANVAS[0], height / CANVAS[1])
        self.clock = core.Clock()
        self.screenshots = screenshots
        self._shot_count = 0
        self._queue: list[tuple] = []
        self._quit = False
        self.win.winHandle.push_handlers(
            on_mouse_press=self._on_press, on_mouse_release=self._on_release,
            on_mouse_motion=self._on_motion, on_mouse_drag=self._on_drag,
            on_key_press=self._on_key, on_text=self._on_text, on_close=self._on_close,
        )
        self.trials: dict[str, dict] = {}
        self._text = visual.TextStim(self.win, text="", color=TEXT, font="Arial", wrapWidth=1700 * self.scale)
        self.done = self._rect(DONE_RECT, BUTTON)
        self.done_label = visual.TextStim(self.win, text="Done", font="Arial", height=44 * self.scale,
                                          pos=self.pos(DONE_RECT[0] + DONE_RECT[2] / 2, DONE_RECT[1] + DONE_RECT[3] / 2))

    # ------------------------------------------------------------ coordinates
    def pos(self, x: float, y: float) -> tuple[float, float]:
        """Canvas point to PsychoPy pixel position (centre origin, y up)."""
        return ((x - CANVAS[0] / 2) * self.scale, (CANVAS[1] / 2 - y) * self.scale)

    def size(self, w: float, h: float) -> tuple[float, float]:
        return (w * self.scale, h * self.scale)

    def _canvas(self, x: float, y: float) -> tuple[float, float]:
        """pyglet window point (bottom left origin, y up) to canvas point."""
        w, h = self.win.winHandle.width, self.win.winHandle.height
        s = min(w / CANVAS[0], h / CANVAS[1])
        return ((x - w / 2) / s + CANVAS[0] / 2, CANVAS[1] / 2 - (y - h / 2) / s)

    def _rect(self, rect, color) -> visual.Rect:
        x, y, w, h = rect
        return visual.Rect(self.win, width=w * self.scale, height=h * self.scale,
                           pos=self.pos(x + w / 2, y + h / 2), fillColor=color, lineWidth=0)

    def _image(self, image, rect, interpolate=True) -> visual.ImageStim:
        x, y, w, h = rect
        return visual.ImageStim(self.win, image=image, size=self.size(w, h),
                                pos=self.pos(x + w / 2, y + h / 2), interpolate=interpolate)

    # ------------------------------------------------------------ input
    def _on_press(self, x, y, button, modifiers):
        if button == 1:
            self._queue.append(("press", self._canvas(x, y), self.now_ms()))

    def _on_release(self, x, y, button, modifiers):
        if button == 1:
            self._queue.append(("release", self._canvas(x, y), self.now_ms()))

    def _on_motion(self, x, y, dx, dy):
        self._queue.append(("move", self._canvas(x, y), self.now_ms()))

    def _on_drag(self, x, y, dx, dy, buttons, modifiers):
        self._queue.append(("move", self._canvas(x, y), self.now_ms()))

    def _on_key(self, symbol, modifiers):
        from pyglet.window import key
        if symbol == key.Q and modifiers & key.MOD_CTRL and modifiers & key.MOD_SHIFT:
            self._quit = True
        names = {key.SPACE: "space", key.F8: "f8", key.ESCAPE: "escape", key.BACKSPACE: "backspace",
                 key.RETURN: "return", key.ENTER: "return", key.Y: "y", key.N: "n"}
        if symbol in names:
            self._queue.append(("key", names[symbol], self.now_ms()))
        from pyglet import event as pyglet_event
        return pyglet_event.EVENT_HANDLED  # keep PsychoPy's own key buffer from filling up

    def _on_text(self, text):
        if text.isascii() and text.isdigit():
            self._queue.append(("digit", text, self.now_ms()))

    def _on_close(self):
        self._quit = True

    def events(self) -> list[tuple]:
        self.win.winHandle.dispatch_events()
        event.clearEvents()
        if self._quit:
            raise QuitSession
        queue, self._queue = self._queue, []
        return queue

    def now_ms(self) -> int:
        return int(self.clock.getTime() * 1000)

    # ------------------------------------------------------------ text screens
    def _draw_lines(self, lines) -> None:
        heights = [STYLES[style][0] * 1.6 for _, style in lines]
        y = (CANVAS[1] - sum(heights)) / 2
        for (text, style), h in zip(lines, heights):
            size, color = STYLES[style]
            self._text.text, self._text.color = text, color
            self._text.height = size * self.scale
            self._text.pos = self.pos(CANVAS[0] / 2, y + h / 2)
            self._text.draw()
            y += h

    def message(self, lines, key: str, hold_ms: int = 0) -> None:
        self.events()
        shot = True
        shown = self.now_ms()
        while True:
            self._draw_lines(lines)
            self.win.flip()
            if shot:
                self.screenshot("message")
                shot = False
            for kind, value, _ in self.events():
                if kind == "key" and value == key and self.now_ms() - shown >= hold_ms:
                    return

    def enter_participant(self) -> int:
        text, note = "", ""
        while True:
            self._draw_lines([
                ("Experimenter: type the participant number, then press Enter", "title"),
                (text or "_", "entry"), (note, "muted"),
            ])
            self.win.flip()
            for kind, value, _ in self.events():
                if kind == "digit" and len(text) < 4:
                    text += value
                elif kind == "key" and value == "backspace":
                    text = text[:-1]
                elif kind == "key" and value == "return":
                    if text and 1 <= int(text) <= 9999:
                        return int(text)
                    note = "Enter a number from 1 to 9999"

    def ask_resume(self, number: int) -> bool:
        lines = [
            (f"Participant {number} has an unfinished session.", "title"),
            ("F8: resume it (marked as resumed in the data)", "muted"),
            ("Esc: enter a different number", "muted"),
        ]
        while True:
            self._draw_lines(lines)
            self.win.flip()
            for kind, value, _ in self.events():
                if kind == "key" and value == "f8":
                    return True
                if kind == "key" and value == "escape":
                    return False

    # ------------------------------------------------------------ trials
    def prepare(self, key: str, room, tiles: list) -> None:
        area = (*ROOM_ORIGIN, *ROOM_SIZE)
        self.trials = {key: {"room": self._image(room, area, interpolate=self.scale != 1), "tiles": tiles}}

    def study(self, key: str, seconds: float):
        room = self.trials[key]["room"]
        self.events()
        self.win.recordFrameIntervals = True
        dropped_before = self.win.nDroppedFrames
        room.draw()
        self.win.flip()
        started = core.getTime()
        self.screenshot(f"{key.replace('/', '_')}_study")
        while core.getTime() - started < seconds:
            room.draw()
            self.win.flip()
            self.events()  # mouse and keys do nothing here, but quitting still works
        before = core.getTime()
        self.win.flip()  # blank
        ended = core.getTime()
        self.win.recordFrameIntervals = False
        dropped = self.win.nDroppedFrames - dropped_before
        return int(round((ended - started) * 1000)), (ended - before) * 1000, dropped

    def filler(self, items: list[Problem], seconds: float) -> FillerResult:
        result = FillerResult()
        deadline = core.getTime() + seconds
        index = 0
        shown_at = None  # when the current sum first appeared
        shot = True
        self.events()
        while core.getTime() < deadline:
            problem = items[index % len(items)]
            self._draw_lines([(problem.text, "title"), ("Y = right      N = wrong", "muted")])
            self.win.flip()
            if shown_at is None:
                shown_at = self.now_ms()
            if shot:
                self.screenshot("filler")
                shot = False
            for kind, value, at in self.events():
                if kind == "key" and value in ("y", "n"):
                    result.answer(problem, value == "y", at - shown_at)
                    index += 1
                    shown_at = None
                    break
        return result

    def grid(self, key: str, controller: GridController) -> None:
        s = self.scale
        tiles = [self._image(image, rect) for image, rect in zip(self.trials[key]["tiles"], controller.rects)]
        frames = []
        for x, y, w, h in controller.rects:
            frames.append((
                visual.Rect(self.win, width=(w + 12) * s, height=(h + 12) * s, pos=self.pos(x + w / 2, y + h / 2),
                            fillColor=None, lineColor=SELECTED, lineWidth=8 * s),
                visual.Rect(self.win, width=(w + 4) * s, height=(h + 4) * s, pos=self.pos(x + w / 2, y + h / 2),
                            fillColor=None, lineColor=TILE_EDGE, lineWidth=2 * s),
            ))
        prompt = visual.TextStim(self.win, text=PROMPT, font="Arial", color=TEXT, height=30 * s,
                                 wrapWidth=1700 * s, pos=self.pos(CANVAS[0] / 2, PROMPT_Y))
        self.events()
        first = True
        while True:
            for kind, value, at in self.events():
                if kind == "press" and controller.press(value, at):
                    self.screenshot(f"{key.replace('/', '_')}_answered")
                    return
            prompt.draw()
            for image, (chosen, plain), state in zip(tiles, frames, controller.tiles):
                image.draw()
                (chosen if state.selected else plain).draw()
            self.done.draw()
            self.done_label.draw()
            self.win.flip()
            if first:
                self.screenshot(f"{key.replace('/', '_')}_grid")
                first = False

    # ------------------------------------------------------------ manipulation checks
    def _hold(self, lines, seconds: float) -> None:
        """Show lines for a fixed time, timed by flips. Keys pressed meanwhile are dropped."""
        started = None
        while started is None or core.getTime() - started < seconds:
            self._draw_lines(lines)
            self.win.flip()
            if started is None:
                started = core.getTime()
            self.events()

    def digit_span(self, digits: list[int], digit_ms: int, gap_ms: int) -> tuple[str, int]:
        self._hold([("+", "digit")], 1.0)
        for digit in digits:
            self._hold([(str(digit), "digit")], digit_ms / 1000)
            self._hold([("", "digit")], gap_ms / 1000)
        text = ""
        shown_at = None
        shot = True
        while True:
            self._draw_lines([
                ("Type the numbers in reverse order, then press Enter", "title"),
                (" ".join(text) or "_", "entry"),
                ("Backspace fixes a mistake", "muted"),
            ])
            self.win.flip()
            if shown_at is None:
                shown_at = self.now_ms()
            if shot:
                self.screenshot("digit_span")
                shot = False
            for kind, value, at in self.events():
                if kind == "digit" and len(text) < 12:
                    text += value
                elif kind == "key" and value == "backspace":
                    text = text[:-1]
                elif kind == "key" and value == "return" and text:
                    return text, at - shown_at

    def slider(self, question: str, low: str, high: str, controller: SliderController) -> None:
        self.events()
        shot = True
        s = self.scale
        title = visual.TextStim(self.win, text=question, font="Arial", color=TEXT, height=44 * s,
                                wrapWidth=1700 * s, pos=self.pos(CANVAS[0] / 2, SLIDER_Y - 170))
        line = visual.Line(self.win, start=self.pos(SLIDER_LEFT, SLIDER_Y), end=self.pos(SLIDER_RIGHT, SLIDER_Y),
                           lineColor=MUTED, lineWidth=6 * s)
        ticks = [visual.Line(self.win, start=self.pos(x, SLIDER_Y - 18), end=self.pos(x, SLIDER_Y + 18),
                             lineColor=MUTED, lineWidth=4 * s) for x in (SLIDER_LEFT, SLIDER_RIGHT)]
        labels = [visual.TextStim(self.win, text=text, font="Arial", color=MUTED, height=28 * s,
                                  pos=self.pos(x, SLIDER_Y + 56)) for text, x in ((low, SLIDER_LEFT), (high, SLIDER_RIGHT))]
        marker = visual.Circle(self.win, radius=18 * s, fillColor=ENTRY, lineWidth=0)
        button = self._rect(CONTINUE_RECT, BUTTON_OFF)
        button_label = visual.TextStim(self.win, text="Continue", font="Arial", height=30 * s,
                                       pos=self.pos(CONTINUE_RECT[0] + CONTINUE_RECT[2] / 2,
                                                    CONTINUE_RECT[1] + CONTINUE_RECT[3] / 2))
        while True:
            for kind, value, at in self.events():
                if kind == "press":
                    if controller.press(value, at):
                        return
                elif kind == "move":
                    controller.move(value, at)
                elif kind == "release":
                    controller.release(value, at)
            for stim in (title, line, *ticks, *labels):
                stim.draw()
            ready = controller.value is not None
            if ready:
                marker.pos = self.pos(controller.x_for(controller.value), SLIDER_Y)
                marker.draw()
            button.fillColor = BUTTON if ready else BUTTON_OFF
            button_label.color = TEXT if ready else MUTED
            button.draw()
            button_label.draw()
            self.win.flip()
            if shot:
                self.screenshot("slider")
                shot = False

    # ------------------------------------------------------------ helpers
    def screenshot(self, name: str) -> None:
        """Save the frame just shown, when --screenshots was given (for checking only)."""
        if not self.screenshots:
            return
        self.screenshots.mkdir(parents=True, exist_ok=True)
        self._shot_count += 1
        self.win.getMovieFrame(buffer="front")
        self.win.saveMovieFrames(str(self.screenshots / f"{self._shot_count:02d}_{name}.png"))

    def close(self) -> None:
        self.win.close()
