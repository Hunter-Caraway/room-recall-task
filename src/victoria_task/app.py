"""The pygame front end. All study logic lives in session.py.

The screen is a fixed 1920x1080 canvas, scaled to fit whatever display is attached,
so object positions are comparable across computers:
  room     1600x900 at (160, 0), identical in the study and placement phases
  tray     the strip under the room
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from .config import Config, load_config
from .data import write_run_sheet
from .session import PlacementRound, RoomInfo, Session, load_room, tray_order

CANVAS = (1920, 1080)
ROOM_ORIGIN = (160, 0)
ROOM_SIZE = (1600, 900)
TRAY_RECT = pygame.Rect(0, 900, 1920, 180)
DONE_RECT = pygame.Rect(1730, 925, 170, 130)
SLOT_AREA_WIDTH = 1710
FPS = 60

BG = (18, 18, 20)
TRAY_BG = (40, 41, 45)
SLOT_BG = (58, 60, 66)
TEXT = (232, 232, 228)
MUTED = (160, 160, 158)
BUTTON = (70, 140, 90)
BUTTON_OFF = (70, 72, 76)

EXPERIMENTER_KEY = pygame.K_F8


class QuitSession(Exception):
    """The experimenter pressed Ctrl+Shift+Q. Everything finished so far is saved."""


def resource_root() -> Path:
    """Where bundled files live: next to the source, or inside the packaged app."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def writable_root() -> Path:
    """Where data goes: next to the .exe when packaged, otherwise the project."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def config_path() -> Path:
    """Prefer an editable config.toml next to the .exe over the bundled copy."""
    beside = writable_root() / "config.toml"
    return beside if beside.exists() else resource_root() / "config.toml"


class Scene:
    """Loaded images for one room."""

    def __init__(self, assets: Path, info: RoomInfo):
        self.info = info
        base = assets / "rooms" / info.name
        self.full = pygame.image.load(base / "full.jpg").convert()
        self.empty = pygame.image.load(base / "empty.jpg").convert()
        self.sprites = {
            o.id: pygame.image.load(base / o.file).convert_alpha() for o in info.objects
        }


def tray_thumbnails(scene: Scene, order) -> dict[str, tuple[pygame.Surface, pygame.Rect]]:
    """One shrunken picture per object, spaced evenly along the tray."""
    slot_w = SLOT_AREA_WIDTH / max(len(order), 1)
    thumbs = {}
    for i, obj in enumerate(order):
        sprite = scene.sprites[obj.id]
        scale = min((slot_w - 10) / sprite.get_width(), 140 / sprite.get_height(), 1.0)
        size = (max(1, int(sprite.get_width() * scale)), max(1, int(sprite.get_height() * scale)))
        thumb = pygame.transform.smoothscale(sprite, size)
        center = (int(10 + slot_w * (i + 0.5)), TRAY_RECT.centery)
        thumbs[obj.id] = (thumb, thumb.get_rect(center=center))
    return thumbs


class Game:
    def __init__(self, config: Config, assets: Path, data_dir: Path, fullscreen: bool = True):
        pygame.init()
        # The dummy driver used by the self-test has no renderer to scale with.
        scaled = 0 if os.environ.get("SDL_VIDEODRIVER") == "dummy" else pygame.SCALED
        flags = scaled | (pygame.FULLSCREEN if fullscreen else 0)
        self.screen = pygame.display.set_mode(CANVAS, flags)
        pygame.display.set_caption("Memory task")
        self.clock = pygame.time.Clock()
        self.config = config
        self.assets = assets
        self.data_dir = data_dir
        self.font = pygame.font.Font(None, 48)
        self.small = pygame.font.Font(None, 32)
        self.tiny = pygame.font.Font(None, 24)
        self.scenes: dict[str, Scene] = {}
        self.transition_frames: list[pygame.Surface] = []

    # ------------------------------------------------------------ helpers
    def scene(self, name: str) -> Scene:
        if name not in self.scenes:
            self.scenes[name] = Scene(self.assets, load_room(self.assets, name))
        return self.scenes[name]

    def load_transition(self) -> None:
        folder = self.assets / "transition"
        self.transition_frames = [
            pygame.image.load(path).convert() for path in sorted(folder.glob("*.jpg"))
        ]

    def events(self):
        """Return this frame's events. Ctrl+Shift+Q always quits, from any screen."""
        result = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise QuitSession
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q and (
                event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT
            ):
                raise QuitSession
            result.append(event)
        return result

    def show_text(self, lines: list[tuple[str, pygame.font.Font, tuple]]) -> None:
        self.screen.fill(BG)
        total = sum(font.get_linesize() + 14 for _, font, _ in lines)
        y = (CANVAS[1] - total) // 2
        for text, font, color in lines:
            surface = font.render(text, True, color)
            self.screen.blit(surface, surface.get_rect(midtop=(CANVAS[0] // 2, y)))
            y += font.get_linesize() + 14
        pygame.display.flip()

    def wait_screen(self, lines, key=None) -> None:
        """Show a screen until the given key, or any participant key if None."""
        while True:
            self.show_text(lines)
            for event in self.events():
                if event.type == pygame.KEYDOWN:
                    if key is None and event.key == pygame.K_SPACE:
                        return
                    if key is not None and event.key == key:
                        return
            self.clock.tick(FPS)

    def on_placement_start(self, scene, order, thumbs) -> None:
        """Hook used by the self-test to script mouse input."""

    # ------------------------------------------------------------ screens
    def enter_participant(self) -> int:
        text = ""
        message = ""
        while True:
            self.show_text([
                ("Experimenter: type the participant number, then press Enter", self.font, TEXT),
                (text or "_", self.font, (250, 220, 130)),
                (message, self.small, MUTED),
            ])
            for event in self.events():
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if text and 1 <= int(text) <= 9999:
                        return int(text)
                    message = "Enter a number from 1 to 9999"
                elif event.unicode.isdigit() and event.unicode.isascii() and len(text) < 4:
                    text += event.unicode
            self.clock.tick(FPS)

    def confirm_existing(self, session: Session) -> bool:
        """Offer to resume. Returns False if the experimenter wants a different number."""
        number = session.participant
        if session.is_complete():
            self.wait_screen([
                (f"Participant {number} has already finished.", self.font, TEXT),
                ("Their data has not been changed. Press F8 to enter another number.", self.small, MUTED),
            ], EXPERIMENTER_KEY)
            return False
        while True:
            self.show_text([
                (f"Participant {number} has an unfinished session.", self.font, TEXT),
                ("F8: resume it (marked as resumed in the data)", self.small, MUTED),
                ("Esc: enter a different number", self.small, MUTED),
            ])
            for event in self.events():
                if event.type == pygame.KEYDOWN:
                    if event.key == EXPERIMENTER_KEY:
                        return True
                    if event.key == pygame.K_ESCAPE:
                        return False
            self.clock.tick(FPS)

    def experimenter_pause(self) -> None:
        """Neutral on purpose: the participant must never learn the condition.
        The experimenter reads which noise to set from data/run_sheet.csv."""
        self.wait_screen([("Please wait for the experimenter", self.font, TEXT)], EXPERIMENTER_KEY)

    def instructions(self, practice: bool) -> None:
        heading = "Practice room" if practice else "Next room"
        seconds = int(self.config.study_seconds)
        self.wait_screen([
            (heading, self.font, TEXT),
            (f"You will see a room for {seconds} seconds. Remember where everything is.", self.small, TEXT),
            ("Then some objects will disappear.", self.small, TEXT),
            ("Drag each object from the tray back to where it was.", self.small, TEXT),
            ("When every object is placed, press Done.", self.small, TEXT),
            ("Press the space bar to begin", self.small, MUTED),
        ])

    def study(self, scene: Scene) -> tuple[int, float]:
        """Show the furnished room for the exact study time, then cut to empty.

        The cut happens on the first display flip at or after the deadline. The
        game loop runs without a frame cap here, limited by vsync when available,
        so overshoot stays near one display frame. Returns measured study time
        and the length of the frame the cut landed on.
        """
        duration_ms = int(self.config.study_seconds * 1000)
        self.screen.fill(BG)
        self.screen.blit(scene.full, ROOM_ORIGIN)
        pygame.draw.rect(self.screen, TRAY_BG, TRAY_RECT)
        pygame.display.flip()
        started = pygame.time.get_ticks()
        while pygame.time.get_ticks() - started < duration_ms:
            self.events()  # stays responsive; mouse and keys do nothing here
            pygame.time.wait(1)
        self.screen.fill(BG)
        self.screen.blit(scene.empty, ROOM_ORIGIN)
        pygame.draw.rect(self.screen, TRAY_BG, TRAY_RECT)
        before_flip = pygame.time.get_ticks()
        pygame.display.flip()
        ended = pygame.time.get_ticks()
        return ended - started, float(ended - before_flip)

    def placement(self, scene: Scene, objects, participant: int, block_index: int) -> tuple[PlacementRound, int]:
        """Drag objects from the tray. Returns the round and time to Done (ms)."""
        round_ = PlacementRound(scene.info, list(objects), pygame.time.get_ticks())
        order = tray_order(participant, block_index, scene.info.name, list(objects))
        thumbs = tray_thumbnails(scene, order)
        self.on_placement_start(scene, order, thumbs)
        stacking: list[str] = []  # draw order of placed objects, last on top
        dragging: str | None = None
        grab = (0.0, 0.0)
        mouse = (0, 0)

        def in_room(point) -> bool:
            return pygame.Rect(ROOM_ORIGIN, ROOM_SIZE).collidepoint(point)

        def sprite_rect(object_id: str) -> pygame.Rect:
            x, y = round_.placements[object_id].position
            rect = scene.sprites[object_id].get_rect()
            rect.center = (int(x + ROOM_ORIGIN[0]), int(y + ROOM_ORIGIN[1]))
            return rect

        def hit_placed(point) -> str | None:
            """Topmost placed object under the pointer, using its visible pixels."""
            for object_id in reversed(stacking):
                rect = sprite_rect(object_id)
                if rect.collidepoint(point):
                    local = (point[0] - rect.x, point[1] - rect.y)
                    if scene.sprites[object_id].get_at(local).a > 30:
                        return object_id
            return None

        while True:
            for event in self.events():
                if event.type == pygame.MOUSEMOTION:
                    mouse = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse = event.pos
                    if DONE_RECT.collidepoint(mouse) and round_.can_finish:
                        return round_, pygame.time.get_ticks() - round_.started_ms
                    picked = hit_placed(mouse)
                    if picked:
                        rect = sprite_rect(picked)
                        grab = (mouse[0] - rect.centerx, mouse[1] - rect.centery)
                        stacking.remove(picked)
                        dragging = picked
                    else:
                        for object_id, (_, rect) in thumbs.items():
                            if round_.placements[object_id].position is None and rect.collidepoint(mouse):
                                dragging = object_id
                                grab = (0.0, 0.0)
                                break
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                    mouse = event.pos
                    center = (mouse[0] - grab[0], mouse[1] - grab[1])
                    now = pygame.time.get_ticks()
                    if in_room(center):
                        position = (center[0] - ROOM_ORIGIN[0], center[1] - ROOM_ORIGIN[1])
                        round_.drop(dragging, position, now)
                        stacking.append(dragging)
                    else:
                        round_.drop(dragging, None, now)  # back to the tray
                    dragging = None

            self.screen.fill(BG)
            self.screen.blit(scene.empty, ROOM_ORIGIN)
            for object_id in stacking:
                self.screen.blit(scene.sprites[object_id], sprite_rect(object_id))
            pygame.draw.rect(self.screen, TRAY_BG, TRAY_RECT)
            for object_id, (thumb, rect) in thumbs.items():
                if round_.placements[object_id].position is None and object_id != dragging:
                    self.screen.blit(thumb, rect)
            ready = round_.can_finish
            pygame.draw.rect(self.screen, BUTTON if ready else BUTTON_OFF, DONE_RECT, border_radius=10)
            label = self.font.render("Done", True, TEXT if ready else MUTED)
            self.screen.blit(label, label.get_rect(center=DONE_RECT.center))
            if dragging:
                sprite = scene.sprites[dragging]
                self.screen.blit(sprite, sprite.get_rect(center=(int(mouse[0] - grab[0]), int(mouse[1] - grab[1]))))
            pygame.display.flip()
            self.clock.tick(FPS)

    def transition(self) -> None:
        """Doorway walk with a fixed length, independent of the computer's speed."""
        if not self.transition_frames:
            self.load_transition()
        duration_ms = int(self.config.transition_seconds * 1000)
        frames = self.transition_frames
        fade = pygame.Surface(ROOM_SIZE)
        fade.fill((0, 0, 0))
        started = pygame.time.get_ticks()
        while True:
            elapsed = pygame.time.get_ticks() - started
            if elapsed >= duration_ms:
                return
            self.events()
            t = elapsed / duration_ms
            self.screen.fill(BG)
            self.screen.blit(frames[min(int(t * len(frames)), len(frames) - 1)], ROOM_ORIGIN)
            edge = min(t, 1 - t) / 0.08  # fade in and out over the first and last 8%
            if edge < 1:
                fade.set_alpha(int(255 * (1 - edge)))
                self.screen.blit(fade, ROOM_ORIGIN)
            pygame.draw.rect(self.screen, BG, TRAY_RECT)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------ session flow
    def choose_session(self) -> Session:
        while True:
            number = self.enter_participant()
            session = Session(self.config, self.data_dir, number)
            if session.store.has_session() and not self.confirm_existing(session):
                continue
            session.begin()
            return session

    def run_practice(self, session: Session) -> None:
        scene = self.scene(self.config.practice_room)
        self.instructions(practice=True)
        self.study(scene)
        self.placement(scene, scene.info.objects[: self.config.practice_objects], session.participant, 0)
        session.mark_practice_done()  # practice results are never written to the data

    def run(self) -> None:
        session = self.choose_session()
        if not session.practice_done:
            self.run_practice(session)
            self.transition()
        first_room = True
        while (step := session.next_room()) is not None:
            block, room, order = step
            # Pause at each new block, and on the first room after any restart so
            # the experimenter can get the noise running again.
            if session.starts_block() or first_room:
                self.experimenter_pause()
            first_room = False
            scene = self.scene(room)
            self.instructions(practice=False)
            study_ms, blink_ms = self.study(scene)
            placement, finished_ms = self.placement(scene, scene.info.objects, session.participant, block.index)
            session.finish_room(block, order, placement, finished_ms, study_ms, blink_ms)
            if session.next_room() is not None:
                self.transition()
        self.wait_screen([
            ("That's the end of the task. Thank you!", self.font, TEXT),
            ("Please let the experimenter know you have finished.", self.small, MUTED),
        ], EXPERIMENTER_KEY)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        from .selftest import run_self_test
        return run_self_test(resource_root() / "assets", load_config(config_path()), writable_root() / "selftest.log")
    config = load_config(config_path())
    data_dir = writable_root() / "data"
    write_run_sheet(data_dir / "run_sheet.csv", config.participants_on_run_sheet, config.conditions, config.room_sets)
    if "--write-run-sheet" in argv:
        return 0
    if "--smoke-test" in argv:
        # Packaging check: confirm every bundled asset loads, then exit.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        game = Game(config, resource_root() / "assets", data_dir, fullscreen=False)
        for room in {name for room_set in config.room_sets for name in room_set} | {config.practice_room}:
            game.scene(room)
        game.load_transition()
        print(f"smoke test ok: {len(game.scenes)} rooms, {len(game.transition_frames)} transition frames")
        pygame.quit()
        return 0
    game = Game(config, resource_root() / "assets", data_dir, fullscreen="--windowed" not in argv)
    try:
        game.run()
    except QuitSession:
        pass
    except Exception:
        # Finished rooms are already saved. Leave the reason for the experimenter.
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "error_log.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        pygame.quit()
    return 0
