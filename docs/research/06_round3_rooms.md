# Round 3 rooms: nine rooms, three arrangements

Source: experimenter feedback after the 2-room test build.

## What changed in the task

| Feedback | Change |
|---|---|
| Three conditions, three rooms each (bedroom, living room, kitchen or garage) | `config.toml` has conditions A, B, C. Each room set is one arrangement of a bedroom, a living room and a garage. The garage replaces the kitchen, whose appliances make spots easy to guess. |
| Objects must switch places in every condition | One room per type, three arrangements. The same 6 objects stand on different spots in each. `postprocess.py` and the self-test fail if an object stands within twice the tolerance of where it stood in another arrangement. |
| 120 participants | Run sheet lists 120. Three conditions need a Williams square with 6 orders (the square plus its mirror), so each order gets exactly 20. |
| Remove the "wait for experimenter" screen | Removed. The experimenter changes the noise while the next block's practice-room screen is up. |
| Encoding time to be justified later | `study_seconds` stays 30 and is marked as a placeholder. |
| Include response time | Per object: first pickup, first placement, placement latency, total drag time, correction time. Per room: reconstruction time. Per sum: mean answer time. Per check: response times. |
| 5 to 8 objects per room | 6 (`objects_per_room`). Changing it needs a re-render. |
| Post-block checks: loudness and annoyance sliders, backward digit span | After the third room of every block: backward digit span (digits shown one at a time, typed in reverse; two trials per length from 2 up to 8; stops when both trials at a length are wrong), then two 0-100 sliders with no starting marker. Saved to `P001_checks.csv`. |
| "Practice room. Remember where objects belong." at the start of every condition | Each block opens with a short unscored practice room (a hallway, also in three arrangements). Every instruction screen says "Remember where objects belong." Nothing names the condition. |
| 5% threshold is arbitrary | Kept, but documented as the secondary outcome. Continuous `distance_pct` (and `distance_px`) is primary. 5% of 1600 px is 80 px, under one object width (100 px). |

## Rooms

### Avoiding location clues

- **Shadows.** The empty room is a fresh path-traced render with the objects hidden, so no shadow or reflection stays behind.
- **Gaps.** Each room has a pool of 18 spots. Each arrangement uses 6, so 12 free patches of surface are visible in every full room too. An empty patch in the empty room is therefore no clue. Targets sit on open surface next to clutter, never in a slot (a gap in a row of books).
- **Obvious spots.** Targets are portable things with no single home in their room, and each moves across different kinds of surface (shelf, table, floor, seat) between arrangements. No target sits by its usual partner (no cup by a plate, no pan on a stove).

### Targets

| Room | Targets |
|---|---|
| Bedroom | binoculars, video camera, lantern, rubber duck, wooden elephant, brass vase |
| Living room | chess set, horse statue, ukulele, boombox, cat statue, wicker basket |
| Garage | football, watering can, garden gnome, tire pump, toolbox, megaphone |
| Hallway (practice) | hat, flashlight, boots, gloves, suitcase |

No target kind appears as clutter in another room.

### BOSS stimuli

The BOSS photos cannot be placed inside 3D-rendered rooms: the room and the object
must be the same model, lit by the same scene. The targets above are Poly Haven
models chosen to match BOSS-style criteria (common, nameable, distinct kinds).
BOSS norms (name agreement, familiarity) could still be used to pick between
candidate objects.

## Known flaws

- Expectancy is still not normed: run the baseline group.
- All rooms share one shell size and camera.
- The sofa in the living room hides the floor behind it, so living-room spots are all on furniture.
