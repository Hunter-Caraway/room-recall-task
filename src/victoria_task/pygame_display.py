"""The pygame display: the same screens as psychopy_display.py, for the single .exe.

Runs the same flow (flow.py) and drag logic (layout.py), so sessions and data files
are identical whichever display runs them. The canvas is a fixed 1920x1080 surface
that pygame scales to the screen (pygame.SCALED keeps the shape, with black bars).
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .checks import CONTINUE_RECT, SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y, SliderController
from .filler import FillerResult, Problem
from .flow import QuitSession
from .layout import CANVAS, DONE_RECT, ROOM_ORIGIN, ROOM_SIZE, TRAY_HEIGHT, TRAY_TOP, Icon, PlacementController
from .session import RoomInfo

BG = (18, 18, 20)
TRAY_BG = (40, 41, 45)
TEXT = (232, 232, 228)
MUTED = (160, 160, 158)
ENTRY = (250, 220, 130)
BUTTON = (70, 140, 90)
BUTTON_OFF = (70, 72, 76)
TRAY_RECT = pygame.Rect(0, TRAY_TOP, CANVAS[0], TRAY_HEIGHT)
DONE = pygame.Rect(DONE_RECT)
FPS = 60
KEYS = {pygame.K_SPACE: "space", pygame.K_F8: "f8", pygame.K_ESCAPE: "escape",
        pygame.K_BACKSPACE: "backspace", pygame.K_RETURN: "return", pygame.K_KP_ENTER: "return",
        pygame.K_y: "y", pygame.K_n: "n"}


class PygameDisplay:
    def __init__(self, assets: Path, fullscreen: bool = True, screenshots: Path | None = None):
        pygame.init()
        if os.environ.get("SDL_VIDEODRIVER") == "dummy":  # packaging check: no renderer to scale with
            self.screen = pygame.display.set_mode(CANVAS)
        else:
            flags = pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0)
            self.screen = pygame.display.set_mode(CANVAS, flags, vsync=1)
        pygame.display.set_caption("Memory task")
        self.assets = Path(assets)
        self.clock = pygame.time.Clock()
        self.fonts = {"title": pygame.font.Font(None, 60), "body": pygame.font.Font(None, 40),
                      "muted": pygame.font.Font(None, 36), "entry": pygame.font.Font(None, 60),
                      "digit": pygame.font.Font(None, 200)}
        self.colors = {"title": TEXT, "body": TEXT, "muted": MUTED, "entry": ENTRY, "digit": TEXT}
        self.screenshots = screenshots
        self._shot_count = 0
        self.rooms: dict[str, dict] = {}
        self.transition_frames: list[pygame.Surface] = []

    # ------------------------------------------------------------ input
    def events(self) -> list[tuple]:
        """This frame's input as (kind, value, ms). Ctrl+Shift+Q quits from any screen."""
        now = self.now_ms()
        result = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise QuitSession
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
                    raise QuitSession
                if event.key in KEYS:
                    result.append(("key", KEYS[event.key], now))
                elif event.unicode.isascii() and event.unicode.isdigit():
                    result.append(("digit", event.unicode, now))
            elif event.type == pygame.MOUSEMOTION:
                result.append(("move", event.pos, now))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result.append(("press", event.pos, now))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                result.append(("release", event.pos, now))
        return result

    def now_ms(self) -> int:
        return pygame.time.get_ticks()

    # ------------------------------------------------------------ text screens
    def _draw_lines(self, lines) -> None:
        self.screen.fill(BG)
        heights = [self.fonts[style].get_linesize() + 14 for _, style in lines]
        y = (CANVAS[1] - sum(heights)) // 2
        for (text, style), h in zip(lines, heights):
            surface = self.fonts[style].render(text, True, self.colors[style])
            self.screen.blit(surface, surface.get_rect(midtop=(CANVAS[0] // 2, y)))
            y += h

    def message(self, lines, key: str) -> None:
        self.events()
        shot = True
        while True:
            self._draw_lines(lines)
            pygame.display.flip()
            if shot:
                self.screenshot("message")
                shot = False
            if any(kind == "key" and value == key for kind, value, _ in self.events()):
                return
            self.clock.tick(FPS)

    def enter_participant(self) -> int:
        text, note = "", ""
        while True:
            self._draw_lines([
                ("Experimenter: type the participant number, then press Enter", "title"),
                (text or "_", "entry"), (note, "muted"),
            ])
            pygame.display.flip()
            for kind, value, _ in self.events():
                if kind == "digit" and len(text) < 4:
                    text += value
                elif kind == "key" and value == "backspace":
                    text = text[:-1]
                elif kind == "key" and value == "return":
                    if text and 1 <= int(text) <= 9999:
                        return int(text)
                    note = "Enter a number from 1 to 9999"
            self.clock.tick(FPS)

    def ask_resume(self, number: int) -> bool:
        lines = [
            (f"Participant {number} has an unfinished session.", "title"),
            ("F8: resume it (marked as resumed in the data)", "muted"),
            ("Esc: enter a different number", "muted"),
        ]
        while True:
            self._draw_lines(lines)
            pygame.display.flip()
            for kind, value, _ in self.events():
                if kind == "key" and value == "f8":
                    return True
                if kind == "key" and value == "escape":
                    return False
            self.clock.tick(FPS)

    # ------------------------------------------------------------ rooms
    def prepare(self, room: RoomInfo, icons: dict[str, Icon]) -> None:
        base = self.assets / "rooms" / room.name
        self.rooms[room.name] = {
            "full": pygame.image.load(base / "full.jpg").convert(),
            "empty": pygame.image.load(base / "empty.jpg").convert(),
            "icons": {
                oid: pygame.transform.smoothscale(
                    pygame.image.frombytes(icon.image.tobytes(), icon.image.size, "RGBA").convert_alpha(),
                    icon.size)
                for oid, icon in icons.items()
            },
        }

    def _room(self, picture) -> None:
        self.screen.fill(BG)
        self.screen.blit(picture, ROOM_ORIGIN)
        pygame.draw.rect(self.screen, TRAY_BG, TRAY_RECT)

    def study(self, room: RoomInfo, seconds: float, cut_to_empty: bool):
        """Show the full room, then cut on the first flip at or after the deadline.
        The wait loop is uncapped (vsync-limited where available), so the cut lands
        within about one display frame. Dropped frames are not measured here."""
        stims = self.rooms[room.name]
        self.events()
        self._room(stims["full"])
        pygame.display.flip()
        started = self.now_ms()
        self.screenshot(f"{room.name}_study")
        while self.now_ms() - started < seconds * 1000:
            self.events()  # mouse and keys do nothing here, but quitting still works
            pygame.time.wait(1)
        if cut_to_empty:
            self._room(stims["empty"])
        else:
            self.screen.fill(BG)
        before = self.now_ms()
        pygame.display.flip()
        ended = self.now_ms()
        return ended - started, float(ended - before), None

    def filler(self, items: list[Problem], seconds: float) -> FillerResult:
        result = FillerResult()
        deadline = self.now_ms() + seconds * 1000
        index = 0
        shown_at = None  # when the current sum first appeared
        shot = True
        self.events()
        while self.now_ms() < deadline:
            problem = items[index % len(items)]
            self._draw_lines([(problem.text, "title"), ("Y = right      N = wrong", "muted")])
            pygame.display.flip()
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
            self.clock.tick(FPS)
        return result

    def placement(self, room: RoomInfo, controller: PlacementController) -> None:
        stims = self.rooms[room.name]
        icons = stims["icons"]
        self.events()
        first = True

        def blit(oid, centre):
            surface = icons[oid]
            self.screen.blit(surface, surface.get_rect(center=(round(centre[0]), round(centre[1]))))

        while True:
            for kind, value, at in self.events():
                if kind == "move":
                    controller.move(value)
                elif kind == "press":
                    if controller.press(value, at):
                        self.screenshot(f"{room.name}_placed")
                        return
                elif kind == "release":
                    controller.release(value, at)
            self._room(stims["empty"])
            for oid in controller.stacking:
                blit(oid, controller.placed_centre(oid))
            for obj in controller.order:
                if controller.in_tray(obj.id):
                    blit(obj.id, controller.slots[obj.id])
            ready = controller.round.can_finish
            pygame.draw.rect(self.screen, BUTTON if ready else BUTTON_OFF, DONE, border_radius=10)
            label = self.fonts["title"].render("Done", True, TEXT if ready else MUTED)
            self.screen.blit(label, label.get_rect(center=DONE.center))
            if controller.dragging:
                blit(controller.dragging, controller.dragged_centre())
            pygame.display.flip()
            if first:
                self.screenshot(f"{room.name}_tray")
                first = False
            self.clock.tick(FPS)

    def load_transition(self) -> None:
        folder = self.assets / "transition"
        self.transition_frames = [pygame.image.load(p).convert() for p in sorted(folder.glob("*.jpg"))]

    def transition(self, seconds: float) -> None:
        if not self.transition_frames:
            self.load_transition()
        frames = self.transition_frames
        fade = pygame.Surface(ROOM_SIZE)
        fade.fill((0, 0, 0))
        started = self.now_ms()
        shot = False
        while (elapsed := self.now_ms() - started) < seconds * 1000:
            self.events()
            t = elapsed / (seconds * 1000)
            self.screen.fill(BG)
            self.screen.blit(frames[min(int(t * len(frames)), len(frames) - 1)], ROOM_ORIGIN)
            edge = min(t, 1 - t) / 0.08  # fade in and out over the first and last 8%
            if edge < 1:
                fade.set_alpha(int(255 * (1 - edge)))
                self.screen.blit(fade, ROOM_ORIGIN)
            pygame.display.flip()
            if not shot and t > 0.5:
                self.screenshot("transition")
                shot = True
            self.clock.tick(FPS)

    # ------------------------------------------------------------ manipulation checks
    def _hold(self, lines, ms: int) -> None:
        """Show lines for ms. Keys pressed meanwhile are dropped."""
        started = self.now_ms()
        while self.now_ms() - started < ms:
            self._draw_lines(lines)
            pygame.display.flip()
            self.events()
            self.clock.tick(FPS)

    def digit_span(self, digits: list[int], digit_ms: int, gap_ms: int) -> tuple[str, int]:
        self._hold([("+", "digit")], 1000)
        for digit in digits:
            self._hold([(str(digit), "digit")], digit_ms)
            self._hold([("", "digit")], gap_ms)
        text = ""
        shown_at = None
        shot = True
        while True:
            self._draw_lines([
                ("Type the numbers in reverse order, then press Enter", "title"),
                (" ".join(text) or "_", "entry"),
                ("Backspace fixes a mistake", "muted"),
            ])
            pygame.display.flip()
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
            self.clock.tick(FPS)

    def slider(self, question: str, low: str, high: str, controller: SliderController) -> None:
        self.events()
        shot = True
        button = pygame.Rect(CONTINUE_RECT)
        while True:
            for kind, value, at in self.events():
                if kind == "press":
                    if controller.press(value, at):
                        return
                elif kind == "move":
                    controller.move(value, at)
                elif kind == "release":
                    controller.release(value, at)
            self.screen.fill(BG)
            title = self.fonts["title"].render(question, True, TEXT)
            self.screen.blit(title, title.get_rect(center=(CANVAS[0] // 2, SLIDER_Y - 170)))
            pygame.draw.line(self.screen, MUTED, (SLIDER_LEFT, SLIDER_Y), (SLIDER_RIGHT, SLIDER_Y), 6)
            for x in (SLIDER_LEFT, SLIDER_RIGHT):
                pygame.draw.line(self.screen, MUTED, (x, SLIDER_Y - 18), (x, SLIDER_Y + 18), 4)
            for text, x in ((low, SLIDER_LEFT), (high, SLIDER_RIGHT)):
                label = self.fonts["muted"].render(text, True, MUTED)
                self.screen.blit(label, label.get_rect(midtop=(x, SLIDER_Y + 36)))
            if controller.value is not None:
                pygame.draw.circle(self.screen, ENTRY, (round(controller.x_for(controller.value)), SLIDER_Y), 18)
            ready = controller.value is not None
            pygame.draw.rect(self.screen, BUTTON if ready else BUTTON_OFF, button, border_radius=10)
            label = self.fonts["body"].render("Continue", True, TEXT if ready else MUTED)
            self.screen.blit(label, label.get_rect(center=button.center))
            pygame.display.flip()
            if shot:
                self.screenshot("slider")
                shot = False
            self.clock.tick(FPS)

    # ------------------------------------------------------------ helpers
    def screenshot(self, name: str) -> None:
        if not self.screenshots:
            return
        self.screenshots.mkdir(parents=True, exist_ok=True)
        self._shot_count += 1
        pygame.image.save(self.screen, self.screenshots / f"{self._shot_count:02d}_{name}.png")

    def close(self) -> None:
        pygame.quit()
