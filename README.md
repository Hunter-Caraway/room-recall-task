# Room Recall Task

By **Hunter Caraway** ([hcaraway5705@floridapoly.edu](mailto:hcaraway5705@floridapoly.edu)), https://github.com/Hunter-Caraway/room-recall-task

An object recognition memory task for an in-lab psychology study on colored noise.
Participants study a drawn basement holding everyday objects, do 30 seconds of quick
sums on a blank screen, then click every object they saw in a 4x3 grid of drawings where the
room's objects are mixed in with decoys. On Windows it runs from one file, `Run Task.bat`.

The full design, and the reasons behind it, are in `docs/RECOGNITION_DESIGN.md`.

## Session flow

1. The experimenter types the participant number.
2. **One practice room**, with no noise playing. Not saved.
3. Three blocks, one per noise condition. Each block:
   1. `Please wait for the experimenter`: start the noise for this block (from the run sheet), then press **F8**. F8 only works after the screen has been up for 10 seconds, so the participant settles into the noise first.
   2. Three basements (storage, laundry, workshop), in an order that rotates across participants. Each one: instructions, **30 s** studying the room, **30 s** of sums on a blank screen (Y = right, N = wrong), then the grid: click every object that was in the room, click again to undo, press Done.
   3. Manipulation checks, noise still on: backward digit span, then two 0-100 sliders (how loud, how annoying).
4. The end screen waits for the experimenter (F8).

Participants never see a condition. The game plays no audio; noise is controlled outside it.

## Session length

About **25 to 30 minutes** on screen; plan about 40 minutes per visit with consent and debrief.

| Part | Each | Count | Total |
| --- | --- | --- | --- |
| Practice room (instructions, 30 s study, 10 s sums, grid) | ~1.5 min | 1 | ~1.5 min |
| Scored room (instructions, 30 s study, 30 s sums, grid) | ~2 min | 9 | ~18 min |
| Manipulation checks (digit span, 2 sliders) | ~2 min | 3 | ~6 min |
| Experimenter starts the noise, 10 s hold, F8 | ~0.5 min | 3 | ~1.5 min |

## The pictures

Everything is a flat illustration drawn in code (`art/drawings/`): the rooms, the objects
in them and every grid tile. One consistent drawn style keeps any object from standing out
and makes the grid objects easy to tell apart.

- **Targets:** 42 drawings of objects from the Bank of Standardized Stimuli (BOSS;
  Brodeur et al., 2010, 2014; CC BY-SA 3.0), each drawn after its BOSS photo (same object,
  colours and view). They are placed into the rooms when the session runs, at real-world
  size, on a surface that suits them (`art/drawings/objects.csv`): floor, table, shelf,
  leaning against the wall, or hanging from a wall hook.
- **Deal:** the participant number shares the 42 targets over the 9 scored rooms (six get 5,
  three get 4). Each target appears exactly once per participant.
- **Decoys:** 91 drawn everyday objects that are not BOSS targets (many share a kind with a
  target: another ball, cup or hand tool). Each grid is filled up to 12 with decoys; a decoy
  appears at most once per participant and is never in any room.
- **Filler:** a few pieces of unscored clutter (boxes, cans, a tire) are drawn into each
  room with the same code as the targets. Filler and decoys are separate pools.
- **Grid tiles** show each object's drawing on white, the same drawing as in the room.

## Experimenter controls

| Key | Action |
| --- | --- |
| B | On the participant-number screen: switch between main study and baseline group |
| F8 | Continue past the experimenter screen, resume an unfinished session, close the end screen |
| Space | Participant starts a room or a check after reading the instructions |
| Y / N | Participant answers a sum |
| Mouse | Click grid tiles, Done, sliders |
| Digits, Backspace, Enter | Participant types a digit-span answer |
| Ctrl+Shift+Q | Quit at any time. Finished rooms stay saved |

## Running it on Windows

1. On GitHub, click **Code**, then **Download ZIP**.
2. Right-click the zip, choose **Extract All**, and open the extracted folder.
3. Double-click **`Run Task.bat`**. On the first screen, type the participant number and
   press Enter. Press **B** first for the baseline group.

The first run needs internet once and takes about a minute. It sets up a private copy of
Python 3.11 with pygame in a `runtime` folder inside the task folder. It needs no admin
rights and changes nothing else on the computer. Every download is checked against a fixed
checksum (`windows/setup_runtime.ps1`). After that it starts straight away, with or without
internet. Data goes to the `data` folder next to `Run Task.bat`. If Windows warns about
a file from the internet, choose **More info**, then **Run anyway**.

To check the computer, run `"Run Task.bat" --self-test` from a command prompt in the task
folder. It plays scripted sessions with no window and should end with `SELF TEST PASSED`.
`"Run Task.bat" --windowed` runs in a window. Run `docs/LAB_CHECKLIST.md` before the
first participant.

## Files written to `data/`

- `run_sheet.csv`: **experimenter only.** Each participant's condition and room order per block.
- `P001_trials.csv`: one row per scored room. Targets, decoys, hits, false alarms, raw hit
  and false-alarm rates, `dprime` and `criterion` (log-linear corrected: add 0.5 to counts
  and 1 to totals), number selected, `grid_ms` (grid on screen to Done), study and delay
  timing, sum results, and the condition and room order.
- `P001_tiles.csv`: one row per grid tile. Item, label, category, `role` (target or decoy),
  `spot` and `rotate_deg` for targets, `selected`, `correct`, `first_selected_ms`,
  `last_toggle_ms`, `toggles`.
- `P001_checks.csv`: digit-span trials and scores, and the slider answers.
- `P001_state.json`: progress and the whole deal, used to resume after a crash.
- `B001_...`: the same for the baseline group. `error_log.txt` only if the game crashes.

Keep the key to what A, B and C mean somewhere else.

## Baseline group

Press **B** on the participant-number screen (the screen then says BASELINE GROUP) to
show the grids to people who **never see the rooms**: they practise
once, then pick the objects they guess were in a room they have not seen. No checks, no
noise. If they pick the targets more often than the decoys, the targets can be told apart
from the decoys without seeing the room and the drawings must be fixed before the main study. About 10 to 15
people, not also in the main study.

## Changing the study

Edit `config.toml`: conditions, rooms, study time, delay, the 10 s hold, grid size, practice
delay, digit-span settings and slider wording. Object sizes and surfaces are in
`art/drawings/objects.csv`; rebuild the assets (`art/render_all.sh`) after changing it.

## Counterbalancing

The participant number sets everything. Condition order uses a Williams balanced Latin
square: 6 orders for 3 conditions, so 120 participants gives 20 per order. Room order
within a block comes from a second balanced square, shifted in each block. The deal of
targets and decoys is random but seeded by the participant number, and saved.

## Development (Linux)

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-exe.txt
.venv/bin/python -m pytest -q
.venv/bin/python run_task.py --pygame --windowed
```

An optional PsychoPy display (`python run_task.py` without `--pygame`) needs Python 3.10 to
3.12; see `requirements.txt`. GitHub Actions runs the tests and `Run Task.bat` on Windows.

## Art

Every picture is drawn in code as SVG (`art/drawings/`) and rendered to PNG. To rebuild
`assets/` after changing a drawing, a room or `art/drawings/objects.csv` (needs `cairosvg`):

```
.venv/bin/pip install cairosvg
art/render_all.sh
```

It draws every object and room, then checks that participants 1 to 120 all get a deal that
fits the rooms. `art/drawings/rooms.py` holds the rooms and their spots; see `art/CREDITS.md`.

## How to cite

This task was written by Hunter Caraway. If you use it, or a modified version, in
research, please cite it in your Methods section and keep the copyright notice in
`LICENSE` (MIT). GitHub's **Cite this repository** button (from `CITATION.cff`) gives
APA and BibTeX. In APA:

> Caraway, H. (2026). *Room Recall Task: An object recognition memory task for colored-noise research* [Computer software]. https://github.com/Hunter-Caraway/room-recall-task

Also cite the Bank of Standardized Stimuli, which the target objects are drawn from:

> Brodeur, M. B., Dionne-Dostie, E., Montreuil, T., & Lepage, M. (2010). The Bank of Standardized Stimuli (BOSS), a new set of 480 normative photos of objects to be used as visual stimuli in cognitive research. *PLoS ONE, 5*(5), e10773. https://doi.org/10.1371/journal.pone.0010773
>
> Brodeur, M. B., Guérard, K., & Bouras, M. (2014). Bank of Standardized Stimuli (BOSS) phase II: 930 new normative photos. *PLoS ONE, 9*(9), e106953. https://doi.org/10.1371/journal.pone.0106953

The target drawings are adapted from the BOSS photos, so they are CC BY-SA 3.0, not MIT
(`art/CREDITS.md`).
