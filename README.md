# Colored noise memory task

An original object-location memory task for an in-lab psychology study on colored
noise. Participants study a realistic room, do a short distractor task, then drag each
object from a tray back to where it was in the now-empty room. It runs on
[PsychoPy](https://www.psychopy.org).

This is the **2-room test build**. It checks the whole flow before more rooms are made.
The design choices, and the research behind them, are in `docs/research/`.

## Session flow

1. The experimenter types the participant number.
2. Practice in the hallway, using 5 objects that never appear in a scored room. Practice is not saved.
3. `Please wait for the experimenter`: set the noise for this block from the run sheet, then press **F8**.
4. Study the furnished room for 30 seconds.
5. 30 seconds of quick sums (Y = right, N = wrong). This filled delay stops rehearsal, so the test measures memory rather than an after-image.
6. The empty room appears with every object in the tray. Drag each object into place, then press Done.
7. A 3-second hallway walk plays, then the next block starts at step 3.

Participants are never shown a condition. The game plays no audio; noise is controlled
outside it.

## Why the objects look the way they do

Objects in the tray, and objects once placed, are separate studio renders of each object:
one camera angle, one light and one size for every object. If they were cut out of the room
render, their angle, lean and size would show where in the room they came from, so a
participant could place them without remembering anything. The cost is that a placed object
does not match the room's perspective.

## Experimenter controls

| Key | Action |
| --- | --- |
| F8 | Continue past a pause, or resume an unfinished session |
| Space | Participant starts a room after reading the instructions |
| Y / N | Participant answers a sum |
| Ctrl+Shift+Q | Quit at any time. Finished rooms stay saved |

## Running it on the Windows lab PC

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
- `P001_state.json`: progress, used to resume after a crash.
- `B001_...`: the same files for the baseline group.
- `error_log.txt`: appears only if the game crashes.

Keep the key to what A, B, C and D mean somewhere else.

Main results columns:

- `distance_pct`: distance from the right spot, as a percent of room width. Continuous; usually the primary measure.
- `score`: 1 if within `tolerance_pct`, else 0.
- `nearest_other`, `nearest_other_distance_pct`, `swap`: `swap` is 1 when an object missed its own spot but landed on another object's spot (it remembered the location, not which object).
- `study_ms`, `study_end_frame_ms`, `study_dropped_frames`: measured study time and display frame drops.
- `retention_ms`, `filler_answered`, `filler_correct`: the delay and how many sums were done.
- `placement_order`, `first_placed_ms`, `last_placed_ms`, `moves`, `session_resumed`, and the order this participant received.

## Baseline group (guessing)

Realistic rooms let people place some objects by common sense (a pan goes on the stove).
`Run Baseline.bat` runs the same task for people who **never see the full rooms**: they
practise normally, then place each object where they think it belongs. Their placements give
the chance level per object. Replace any object whose guesses land on its true spot, and
compare participants' errors against this group. About 10 to 15 people is a reasonable
start; they should not also take part in the main study.

## Changing the study

Edit `config.toml`: conditions, room sets, study time, delay, transition time, tolerance.
It must have an even number of conditions, with one room set per condition. Raw positions
are saved, so tolerance can be changed during analysis without rerunning anyone.

## Counterbalancing

The participant number sets everything, so the same number always gets the same order.
Condition order uses a balanced Latin square. Room sets rotate separately, so over
`n x n` participants every order meets every rotation. With 35 participants groups are not
exactly equal. Each row saves the order that participant received.

## Development (Linux)

PsychoPy needs Python 3.10 to 3.12. On Python 3.11:

```
python3.11 -m venv .venv-psychopy
.venv-psychopy/bin/pip install --no-deps psychopy==2026.2.5
.venv-psychopy/bin/pip install arabic-reshaper freetype-py i18next json-tricks numpy packaging pandas pillow pyglet==1.5.27 pyserial python-bidi pyyaml requests scipy six pytest==8.4.2
.venv-psychopy/bin/python -m pytest -q
.venv-psychopy/bin/python run_task.py --windowed
```

The tests and `--self-test` need only `pytest` and `pillow`, not PsychoPy. GitHub Actions
runs them on Windows and uploads the lab folder as `MemoryTask-Windows`. GitHub's machines
have no graphics card, so the PsychoPy window itself is only checked on the lab PC.

## Art

Everything is made from CC0 assets from [Poly Haven](https://polyhaven.com), see
`art/CREDITS.md`. To rebuild, install Blender 5.2 and Python with Pillow, then run
`art/render_all.sh` and `python art/postprocess.py`. `postprocess.py` fails if a scored
object is more than 10% hidden, touches the image edge, or is within twice the tolerance of
another scored object. The previous pygame version is tagged `pygame-v1`.

## Known limits of the test build

- Not yet run on Windows or on a real monitor and mouse with PsychoPy: see the lab checklist.
- Unscored furniture and clutter stay in the empty room, by design.
- Placed objects are drawn at one size and angle, so they do not sit in the room's perspective.
- Object expectancy (how guessable each spot is) has not been normed yet: run the baseline group.
- Two rooms per condition is too few for a real study, and 35 participants may be underpowered for a small effect (see `docs/research/01_paradigms.md`).
