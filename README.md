# Room Recall Task

By **Hunter Caraway** ([hcaraway5705@floridapoly.edu](mailto:hcaraway5705@floridapoly.edu)), https://github.com/Hunter-Caraway/room-recall-task

An original object-location memory task for an in-lab psychology study on colored
noise. Participants study a realistic room, do a short distractor task, then drag each
object from a tray back to where it was in the now-empty room. It runs on
[PsychoPy](https://www.psychopy.org).

This is the **9-room build**: three conditions, each with a bedroom, a living room and a
garage. The three rooms are the same in every condition, but the scored objects stand in
different places in each, so nothing learned in one condition helps in the next. The design
choices, and the research behind them, are in `docs/research/`.

## Session flow

1. The experimenter types the participant number.
2. Each block (one condition) runs without any pause screen:
   1. **Practice room** (a hallway, 5 objects that never appear in a scored room), with the instruction "Remember where objects belong." Practice is not saved. **Set the noise for this block, from the run sheet, while this screen is up.**
   2. Three scored rooms in a shuffled order. Each room: study the furnished room for 30 seconds, then 30 seconds of quick sums (Y = right, N = wrong), then drag the 6 objects from the tray into the empty room and press Done. A 3-second hallway walk plays between rooms.
   3. Manipulation checks, with the block's noise still on: backward digit span, then two 0-100 sliders (how loud, how annoying was the noise).
3. After the third block, the end screen waits for the experimenter (F8).

Participants are never shown a condition; they are only told they will hear noise. The game
plays no audio; noise is controlled outside it.

The 30-second study time is a placeholder until it is justified from the literature
(`study_seconds` in `config.toml`).

## Session length

About **30 to 35 minutes** on screen; plan about 45 minutes per lab visit with consent and debrief.

| Part | Each | Count | Total |
| --- | --- | --- | --- |
| Practice room (instructions, 30 s study, 10 s sums, place 5 objects, walk) | ~1.6 min | 3 | ~5 min |
| Scored room (instructions, 30 s study, 30 s sums, place 6 objects, 3 s walk) | ~2.3 min | 9 | ~21 min |
| Manipulation checks (backward digit span, 2 sliders) | ~2 min | 3 | ~6 min |
| Experimenter sets the noise, presses F8 | ~0.5 min | 3 | ~1.5 min |

Placement speed varies most; slow participants can add about 5 minutes.

## Why the objects look the way they do

Objects in the tray, and objects once placed, are separate studio renders of each object:
one camera angle, one light and one size for every object. If they were cut out of the room
render, their angle, lean and size would show where in the room they came from, so a
participant could place them without remembering anything. The cost is that a placed object
does not match the room's perspective.

## Experimenter controls

| Key | Action |
| --- | --- |
| F8 | Resume an unfinished session, or close the end screen |
| Space | Participant starts a room or a check after reading the instructions |
| Y / N | Participant answers a sum |
| Digits, Backspace, Enter | Participant types a digit-span answer |
| Ctrl+Shift+Q | Quit at any time. Finished rooms stay saved |

## Running it on the Windows lab PC

There are two builds. They show the same screens, use the same rooms and write the same
data files; only the drawing library differs.

- **`MemoryTask-Windows-exe`**: one `MemoryTask.exe`, nothing to install. Draws with pygame.
  Double-click it; `MemoryTask.exe --self-test` writes `selftest.log`. An edited
  `config.toml` next to the .exe overrides the built-in one. It does not record dropped
  display frames (`study_dropped_frames` is empty).
- **`MemoryTask-Windows-PsychoPy`**: the PsychoPy version, below.

Use one build for every participant in a study, and say which in the write-up; the `build`
column records it.

### PsychoPy build

1. Install **PsychoPy Standalone 2026.2.5, the Python 3.11 version**, from the PsychoPy download page (once).
2. Unzip the `MemoryTask-Windows` folder somewhere the account can write to.
3. Double-click `Run Task.bat`.

Other launchers: `Run Baseline.bat` (no-study group, see below), `Self Test.bat`
(scripted sessions, writes `selftest.log`) and `Smoke Test.bat` (opens the window and loads
every picture). If PsychoPy is installed somewhere unusual, write the full path of its
`python.exe` into `psychopy_python.txt` in the same folder. Run `docs/LAB_CHECKLIST.md`
before the first participant.

## Files written to `data/`

- `run_sheet.csv`: **experimenter only.** Each participant's condition for each block.
- `P001_results.csv`: one row per object for that participant.
- `P001_checks.csv`: the manipulation checks, one row per digit-span trial, per span score and per slider.
- `P001_state.json`: progress, used to resume after a crash.
- `B001_...`: the same files for the baseline group.
- `error_log.txt`: appears only if the game crashes.

Keep the key to what A, B and C mean somewhere else.

Main results columns:

- `distance_pct` (primary outcome): distance from the right spot, as a percent of room width. Continuous, so it needs no threshold. `distance_px` is the same in pixels of the 1600 px room.
- `score` (secondary outcome): 1 if within `tolerance_pct`, else 0. 5% of a 1600 px room is 80 px, a little less than the 100 px an object is drawn at. The threshold is a convention, not a finding; raw positions are saved, so it can be changed or dropped at analysis.
- `nearest_other`, `nearest_other_distance_pct`, `swap`: `swap` is 1 when an object missed its own spot but landed on another object's spot (it remembered the location, not which object).
- Response times, all in ms from the empty room appearing unless noted:
  - `reconstruction_ms`: total time to place every object and press Done.
  - `first_pickup_ms`, `first_placed_ms`: when the object was first picked up and first dropped in the room.
  - `placement_latency_ms`: time from the previous object's first placement (or from the start, for the first) to this object's first placement.
  - `held_ms`: total time spent dragging the object. `correction_ms`: the part of that spent moving it after its first placement.
  - `last_placed_ms`, `moves`, `placement_order`.
- `study_ms`, `study_end_frame_ms`, `study_dropped_frames`: measured study time and display frame drops.
- `retention_ms`, `filler_answered`, `filler_correct`, `filler_mean_rt_ms`: the delay, how many sums were done, and the mean time per answer.
- `session_resumed`, and the condition and room order this participant received.

Check columns (`P001_checks.csv`): `measure` is `digit_span_trial` (with `length`,
`sequence`, `response`, `correct`, `rt_ms`), `digit_span_longest` and
`digit_span_total_correct` (in `value`), or a slider id such as `loudness` and `annoyance`
(`value` 0-100, `first_click_ms`, `rt_ms` from the question appearing to Continue).

## Baseline group (guessing)

Realistic rooms let people place some objects by common sense (a pan goes on the stove).
`Run Baseline.bat` runs the same task for people who **never see the full rooms**: they
practise once, then place each object where they think it belongs. There are no
manipulation checks. Their placements give
the chance level per object. Replace any object whose guesses land on its true spot, and
compare participants' errors against this group. About 10 to 15 people is a reasonable
start; they should not also take part in the main study.

## Changing the study

Edit `config.toml`: conditions, room sets, objects per room, study time, delay, transition
time, tolerance, practice rooms, digit-span settings and slider wording. It needs one room
set per condition. Changing `objects_per_room` also needs the rooms re-rendered (see Art).
Raw positions are saved, so tolerance can be changed during analysis without rerunning
anyone.

## Counterbalancing

The participant number sets everything, so the same number always gets the same order.
Condition order uses a Williams balanced Latin square: with 3 conditions that is 6 orders,
so 120 participants gives exactly 20 per order. Room sets (arrangements) rotate separately,
so over 18 participants every order meets every rotation; 120 is not a multiple of 18, so
those cells differ by one person (126 would make them equal). The order of the three rooms
inside a block is shuffled per participant. Each row saves the order that participant received.

## Development (Linux)

PsychoPy needs Python 3.10 to 3.12. On Python 3.11:

```
python3.11 -m venv .venv-psychopy
.venv-psychopy/bin/pip install --no-deps psychopy==2026.2.5
.venv-psychopy/bin/pip install arabic-reshaper freetype-py i18next json-tricks numpy packaging pandas pillow pyglet==1.5.27 pyserial python-bidi pyyaml requests scipy six pytest==8.4.2
.venv-psychopy/bin/python -m pytest -q
.venv-psychopy/bin/python run_task.py --windowed
```

`--pygame` runs the pygame display instead (`.venv` with `requirements-exe.txt`). The tests
and `--self-test` need only `pytest` and `pillow`. GitHub Actions runs them on Windows, builds
`MemoryTask.exe` with PyInstaller, runs the self-test inside it, and uploads both builds. GitHub's machines
have no graphics card, so the PsychoPy window itself is only checked on the lab PC.

## Art

Everything is made from CC0 assets from [Poly Haven](https://polyhaven.com), see
`art/CREDITS.md`. To rebuild, install Blender 5.2 and Python with Pillow, then run
`art/render_all.sh` and `python art/postprocess.py`. `postprocess.py` fails if a scored
object is more than 10% hidden, touches the image edge, is within twice the tolerance of
another scored object, or stands within twice the tolerance of where it stood in another
arrangement. The previous pygame version is tagged `pygame-v1`.

How the rooms avoid giving locations away (`docs/research/06_round3_rooms.md`):

- **No shadows or gaps.** The empty room is a fresh render without the objects, so no shadow stays behind. Every room has a pool of 18 free spots with clutter around them; each arrangement uses 6, so 12 free patches are visible in every full room and an empty patch in the empty room is no clue.
- **No obvious spots.** The scored objects are portable things with no single home in the room (no pan on a stove, no cup by a plate), and each sits on a different kind of surface in each arrangement.
- **Busier rooms.** More furniture and clutter than round 2, with clutter next to each spot.

## Known limits of the test build

- Not yet run on Windows or on a real monitor and mouse with PsychoPy: see the lab checklist.
- Unscored furniture and clutter stay in the empty room, by design.
- Placed objects are drawn at one size and angle, so they do not sit in the room's perspective.
- Object expectancy (how guessable each spot is) has not been normed yet: run the baseline group.
- The extra measure planned after the pilot is not built yet.

## How to cite

This task was written by Hunter Caraway. If you use it, or a modified version, in
research, please cite it in your Methods section and keep the copyright notice in
`LICENSE` (MIT). GitHub's **Cite this repository** button (from `CITATION.cff`) gives
APA and BibTeX. In APA:

> Caraway, H. (2026). *Room Recall Task: An object-location memory task for colored-noise research* [Computer software]. https://github.com/Hunter-Caraway/room-recall-task

The rendered art uses CC0 models and textures from Poly Haven (`art/CREDITS.md`).
