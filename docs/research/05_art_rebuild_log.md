# Art rebuild log (round 2)

Spec: `02_scene_stimuli.md` rules 1-4 and 8-10, and `04_room_audit.md` sections A and D.
Build: `art/build_rooms.py`; render: `art/render_all.sh`; checks: `art/postprocess.py`.

## What changed

**Camera.** All three rooms use one camera at 1.55 m height, 26 mm lens, about 11° pitch (`ROOM_CAMERA`).
It was 1.85 m, 22 mm and 18-19° pitch, which gave a dollhouse look.

**Kitchen.**
- New: a sink cut into the counter with a tap, under the window.
- The counter runs fridge, prep, stove, sink, counter. The open shelves have brackets.
- New: a white fridge with a note, magnet and photo; a breakfast table at real scale (`wooden_table_02`) with two chairs; a pendant lamp; sockets.
- Removed: outdoor dustbin, distressed dresser, display shelves, goblets and the floor pot.
- Cleaners stand only by the sink, away from food.

**Living room.**
- The sofa sits with its back to the camera, facing a flat TV on a low cabinet. The coffee table is at real size.
- Added: an ottoman, a side table, curtains, a thick rug, a pendant lamp and sockets.
- Removed: grandfather clock, wall clock, pocket watch, base-less clamp lamp, carved console, rubber duck, suitcase and cat statue. The mantel clock is now the only timepiece.
- The window view uses a different HDRI (`cloudy_vondelpark`), so the two rooms no longer share one garden.

**Hallway (practice room, new).** Front door, coat rail and bench, shoe rack, tall console with mirror, runner, plant and pendant. It has 5 targets, none sharing a kind with the test rooms.

**Transition.** The walk is shorter (0.2 m to 4.3 m), so the clip ends framing the open doorway into a bright plain room. The old clip ended on a sliced sofa and blank wall. The far room now has a window.

**Tray icons (cue-leak fix).**
- Every target is rendered alone in a studio, never cut from the room: orthographic camera at 15° elevation, the same light, transparent background.
- `postprocess.py` trims each render, scales its longest side to 150 px and centres it on a 160x160 canvas. `room.json` gives each object an `"icon"`.
- The pose comes from `icon_rot` / `icon_rot_x` in `place(...)`. Flat objects (cutting board, plate, spoon, pan) are stood up so they read clearly.

**Checks in `postprocess.py`.**
- Spacing: correct spots must be more than 10% of room width apart (160 px; was 5%).
- Visibility: at least 90%. Objects must not touch the image edge, and must meet the minimum size.
- Icons must render something.
- All of this applies to the hallway too.

## Targets

| Room | Targets |
|---|---|
| Kitchen | cutting board, brass pan, spray bottle, kettle, wine bottle, enamel pot, teacup, carved plate, wicker basket, cheese box, cake, wooden spoon, bananas, thermos, wooden bucket |
| Living room | boombox, seashell, film projector, mantel clock, small plant, binoculars, chess set, candleholder, picture frame, camera, magnifying glass, compass, ukulele, horse statue, vase |
| Hallway | hat, flashlight, boots, gloves, suitcase |

Placement mix:
- **Highly expected:** pan on hob, spray bottle by sink, kettle on counter, plant on the sill.
- **Mildly odd:** thermos and wine bottle on chair seats, basket on a stool, film projector on a bookshelf.
- **Moderately expected:** the rest.

This mix is my judgement. It has not been normed.

## Layout rules learned while iterating

- **Height.** Nothing scored sits above eye height (1.55 m). A shelf or fridge lip above the eye hides the object's base, which failed the 90% visibility check. The fridge is now 1.42 m, and only bookshelf shelves at 0.11, 0.39, 0.67, 0.96 and 1.28 m hold targets.
- **Floor.** The camera sees the floor only beyond about y = -0.1, so the sofa sits with its back to the camera at y = -0.45. Objects on the back-wall floor overlap table objects in the image, so they are avoided.
- **Fast check.** `--mode check` runs the visibility test at low resolution in about 35 s. Full resolution came out up to 5 points lower, so aim for 0.93 or more in the check.

## Final check (postprocess: ok)

| Room | Minimum visible | Minimum spacing (limit 160 px) |
|---|---|---|
| Kitchen | 0.931 | 169 px |
| Living room | 0.931 | 168 px |
| Hallway | 0.918 | 164 px |

## Known flaws, seen in the final renders

- **Not normed.** Naturalness and schema expectancy have not been rated by anyone. Rules 5 and 6 (a no-study baseline group and expectancy norming) still need people.
- **Same shell.** All three rooms use one 4.6 m box and one camera. The kitchen and hallway share the garden HDRI, at different rotations.
- **Odd placements.** The thermos and wine bottle on chair seats and the basket on a stool are deliberate "mildly odd" spots, but some viewers may find them strange.
- **Pots.** The kitchen has several clutter pots and pans (brass pot, ceramic pot, metal jug) near the enamel-pot and brass-pan targets. This is realistic, but may make those two targets easier to confuse.
- **Candlestick.** A wooden candlestick (clutter) stands on the kitchen table, while the living-room target is a brass candleholder. The kitchen was rendered before I noticed.
- **Small targets.** The seashell, binoculars and compass are small on screen (about 70-90 px wide at 1600 px).
- **Empty room.** Chair seats and the stool are bare once their targets vanish. That is normal for chairs, but still a possible cue.
- **Hallway.** It is sparse and has no window.
- **Corridor.** Its walls are plain.
- **Flat TV.** It is simple geometry with a blank screen.
- **Icons.** The brass pan is shown tilted up so its bowl is visible. The cutting board and carved plate are stood upright. These poses differ from the room, which is deliberate.
