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
4. A 6x4 grid of 24 tiles: this room's targets plus decoys, shuffled, equal-size tiles.
   Click a tile to select it, click again to deselect, press Done. Done works with
   nothing selected. No time limit.

## Rooms

- Three basement layouts (storage, laundry, workshop), each shown once per condition:
  9 scored trials. Room order within a block rotates across participants.
- A fourth, simpler basement corner is the practice room: 4 made objects, a 6x4 grid
  with 20 practice-only decoys.
- One picture per trial. The camera sits a little high and looks down, so a foreground
  table is seen nearly from above (for photos taken from above) and the shelves and
  floor behind are seen from the side.
- Each room is rendered empty with tagged spots: surface type (floor, shelf, table,
  wall) and the largest object the spot takes.

## Targets (dataset photos)

- 42 photos from a published object-image set, in `art/dataset_photos/` (gitignored
  until the license is known; credit to be added).
- Cut out procedurally from the white background.
- At the start of a run the participant number seeds the deal: 6 rooms get 5 photos and
  3 rooms get 4 (42 in all). Each photo is a target once per participant, so an earlier
  target never appears in a later grid. The deal is saved.
- Placed at session time on a spot that fits its real size and surface
  (`art/dataset_photos.csv`, editable), at real-world scale.
- Rotated in the picture plane only where needed to rest naturally (a knife lying flat).
  Never mirrored.
- Colour-graded to the room's light, with a contact shadow.

## Filler

Unscored clutter in each room is also added as cutouts with the same grade and shadow,
so the scored photos do not stand out. Filler and decoys are separate pools.

## Decoys

- About 180 made studio shots in the dataset's style: white background, same soft top
  light and angle, 2000 px, slight JPEG grain.
- Each decoy appears at most once per participant and is never in any room.
- A decoy may share a category with a target in its grid; its category is saved.
- 19 or 20 decoys per grid (24 minus the targets).

## Grid

Tiles show the original photo, not the rotation used in the room.

## Data

- One row per tile: trial, room, condition, image, target or decoy, decoy category,
  selected, click time, rotation applied in the room.
- One row per trial: hits, false alarms, d', time to Done.
- Manipulation checks as before. Crash-resume as before.

## Baseline group

Sees the grids only, without the rooms. If they pick dataset photos above chance, the
decoys can be told apart from real photos and must be fixed before the main study.
