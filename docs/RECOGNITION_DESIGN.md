# Recognition task design (round 4)

Agreed 2026-11-12. This replaces the drag-and-drop object-location task on `main`.

## Session

1. The experimenter types the participant number.
2. **One practice room** at the start of the session, with no noise playing. Not scored.
3. Three blocks, one per noise condition (A, B, C, Latin-square order). Each block:
   1. `Please wait for the experimenter`: the experimenter starts the noise. F8 works
      only after the screen has been up for 10 s, so the participant settles into the
      noise before the first room.
   2. Three scored basement rooms (trials).
   3. Manipulation checks: backward digit span, then loudness and annoyance sliders.
4. About 25 minutes on screen.

## Trial

1. Instructions: remember which objects are in the room; you will be asked which ones
   you saw (intentional encoding).
2. Study the room for 30 s.
3. 30 s of true/false sums on a blank screen (practice: 10 s).
4. A 4x3 grid of 12 tiles: this room's targets plus decoys, shuffled, equal-size tiles.
   Click a tile to select it, click again to deselect, press Done. Done works with
   nothing selected. No time limit.

## Rooms

- Three basement layouts (storage, laundry, workshop), each shown once per condition:
  9 scored trials. Room order within a block rotates across participants.
- A fourth, simpler basement is the practice room: 4 practice objects, a 4x3 grid with
  8 practice-only decoys.
- One picture per trial, a flat illustration in one-point perspective: back wall with
  shelves and hooks, the floor in front of it, and a table across the foreground for the
  smallest objects.
- Each room is drawn empty with tagged spots: surface type (floor, shelf, table, wall
  hook, lean against the wall) and the largest object the spot takes.

## Art direction (revised 2026-11-13)

Everything is drawn: rooms, objects in the rooms and every grid tile. Cutting the BOSS
photos into rendered 3D rooms never looked right (wrong angle, scale and contact), so each
object is redrawn in one flat illustration style instead: flat colours, light from the
upper left, hard-edged shading bands, no outlines. One style means no object stands out,
and drawn grid tiles are easier to tell apart than photos. All drawings are SVG made in
code (`art/drawings/`) and rendered by `art/build_drawn.py`.

## Targets

- 42 objects from the Bank of Standardized Stimuli (BOSS, CC BY-SA 3.0), each drawn
  after its photo: same object, colours, view and proportions. No photo is shown.
- At the start of a run the participant number seeds the deal: 6 rooms get 5 targets and
  3 rooms get 4 (42 in all). Each target appears once per participant, so an earlier
  target never appears in a later grid. The deal is saved.
- Placed at session time on a spot that fits its real size and surface
  (`art/drawings/objects.csv`, editable), at real-world scale, with a flat shadow (an
  ellipse under standing objects, an offset outline on the wall behind hanging and leaning
  ones). No target covers another target or the filler. Never turned or mirrored.

## Filler

A few pieces of unscored clutter in each room (boxes, cans, bottles, a tire), drawn in the
same style and added with the same code and shadow as the targets. Filler and decoys are
separate pools, and no filler kind resembles a decoy.

## Decoys

- 91 drawn everyday objects, none a BOSS target, filler or practice object.
- Each decoy appears at most once per participant and is never in any room
  (9 grids x 12 tiles - 42 targets = 66 decoys per participant).
- A decoy may share a category with a target in its grid; its category is saved.
- 7 or 8 decoys per grid (12 minus the targets).

## Grid

Tiles show the same drawing as in the room, on white.

## Data

- One row per tile: trial, room, condition, image, target or decoy, decoy category,
  selected, click time.
- One row per trial: hits, false alarms, d', time to Done.
- Manipulation checks as before. Crash-resume as before.

## Baseline group

Sees the grids only, without the rooms. If they pick targets above chance, the targets
can be told apart from the decoys without study and the drawings must be fixed before the
main study.
