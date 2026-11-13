# Room Recall Task

By **Hunter Caraway** ([hcaraway5705@floridapoly.edu](mailto:hcaraway5705@floridapoly.edu)), https://github.com/Hunter-Caraway/room-recall-task

An object recognition memory task for an in-lab psychology study on colored noise.
Participants study a realistic basement holding photos of everyday objects, do 30 seconds
of quick sums on a blank screen, then click every object they saw in a 6x4 grid where the
room's objects are mixed in with decoys. It runs on [PsychoPy](https://www.psychopy.org),
or as a single Windows .exe.

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

- **Targets:** 42 photos from the Bank of Standardized Stimuli (BOSS; Brodeur et al., 2010, 2014; CC BY-SA 3.0).
  They are cut out of their white background and placed into the rooms when the session
  runs, at real-world size, on a spot that suits them (floor, table, shelf, wall, or leaning
  on a wall), tinted by the light at that spot, with a contact shadow. A photo is turned in
  the picture plane only where `art/dataset_photos.csv` says so, and is never mirrored.
- **Deal:** the participant number shares the 42 photos over the 9 scored rooms (six get 5,
  three get 4). Each photo is a target exactly once per participant.
- **Decoys:** about 190 made objects, shot in Blender in the dataset's style (white
  background, soft product light, three-quarter view). Each grid is filled up to 24 with
  decoys; a decoy appears at most once per participant and is never in any room.
- **Filler:** the smaller clutter in each room is made the same way as the decoys and added
  with the same code as the targets, so the photos do not stand out. Filler and decoys are
  separate pools.
- **Grid tiles** show each object as photographed (never turned), on white.

## Experimenter controls

| Key | Action |
| --- | --- |
| F8 | Continue past the experimenter screen, resume an unfinished session, close the end screen |
| Space | Participant starts a room or a check after reading the instructions |
| Y / N | Participant answers a sum |
| Mouse | Click grid tiles, Done, sliders |
| Digits, Backspace, Enter | Participant types a digit-span answer |
| Ctrl+Shift+Q | Quit at any time. Finished rooms stay saved |

## Running it on Windows

1. On GitHub, click **Code**, then **Download ZIP**.
2. Right-click the zip, choose **Extract All**, and open the extracted folder.
3. Double-click **`Run Task.bat`** (`Run Baseline.bat` for the baseline group).

The first run needs internet once and takes about a minute. It sets up a private copy of
Python 3.11 with pygame in a `runtime` folder inside the task folder. It needs no admin
rights and changes nothing else on the computer. Every download is checked against a fixed
checksum (`windows/setup_runtime.ps1`). After that it starts straight away, with or without
internet. Data goes to the `data` folder next to `Run Task.bat`. If Windows warns about
a file from the internet, choose **More info**, then **Run anyway**.

`Self Test.bat` runs scripted sessions with no window and should end with
`SELF TEST PASSED`. From a command prompt, `"Run Task.bat" --windowed` runs in a window.

Other builds (from GitHub Actions; the screens and data files are the same):

- **`MemoryTask-Windows-exe`**: one `MemoryTask.exe`, nothing to download on first run.
- **`MemoryTask-Windows-PsychoPy`**: draws with PsychoPy and records dropped display
  frames. Needs **PsychoPy Standalone 2026.2.5 (Python 3.11)** installed.

Use one build for every participant in a study; the `build` column records which one
(`pygame` or `psychopy`). Run `docs/LAB_CHECKLIST.md` before the first participant.

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

`Run Baseline.bat` shows the grids to people who **never see the rooms**: they practise
once, then pick the objects they guess were in a room they have not seen. No checks, no
noise. If they pick the dataset photos more often than the decoys, the made decoys can be
told apart from real photos and must be fixed before the main study. About 10 to 15
people, not also in the main study.

## Changing the study

Edit `config.toml`: conditions, rooms, study time, delay, the 10 s hold, grid size, practice
delay, digit-span settings and slider wording. Object sizes, surfaces and turns are in
`art/dataset_photos.csv`; rebuild the assets after changing it.

## Counterbalancing

The participant number sets everything. Condition order uses a Williams balanced Latin
square: 6 orders for 3 conditions, so 120 participants gives 20 per order. Room order
within a block comes from a second balanced square, shifted in each block. The deal of
photos and decoys is random but seeded by the participant number, and saved.

## Development (Linux)

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-exe.txt numpy scipy
.venv/bin/python -m pytest -q          # synthetic assets; runs without the dataset photos
.venv/bin/python run_task.py --pygame --windowed
```

PsychoPy needs Python 3.10 to 3.12; see `requirements.txt`. GitHub Actions runs the tests on
Windows and builds both packages.

## Art

All 3D models, textures and the HDRI are CC0 from [Poly Haven](https://polyhaven.com), see
`art/CREDITS.md`. To rebuild everything (Blender 5.2, Python with Pillow, numpy and scipy):

1. Put the dataset photos in `art/dataset_photos/`.
2. `cd art && python fetch_assets.py` (downloads models and textures).
3. `art/render_all.sh`: cuts out the photos, shoots the made objects, renders the four
   basements, then `art/assemble_assets.py` builds `assets/` and fails if any target spot
   overlaps another spot or the filler.

`art/choose_models.py` chose the decoy, practice and filler pools (`art/made_objects.csv`,
editable). `art/build_basements.py` holds the rooms and their spots.

## How to cite

This task was written by Hunter Caraway. If you use it, or a modified version, in
research, please cite it in your Methods section and keep the copyright notice in
`LICENSE` (MIT). GitHub's **Cite this repository** button (from `CITATION.cff`) gives
APA and BibTeX. In APA:

> Caraway, H. (2026). *Room Recall Task: An object recognition memory task for colored-noise research* [Computer software]. https://github.com/Hunter-Caraway/room-recall-task

Also cite the Bank of Standardized Stimuli, which the target photos come from:

> Brodeur, M. B., Dionne-Dostie, E., Montreuil, T., & Lepage, M. (2010). The Bank of Standardized Stimuli (BOSS), a new set of 480 normative photos of objects to be used as visual stimuli in cognitive research. *PLoS ONE, 5*(5), e10773. https://doi.org/10.1371/journal.pone.0010773
>
> Brodeur, M. B., Guérard, K., & Bouras, M. (2014). Bank of Standardized Stimuli (BOSS) phase II: 930 new normative photos. *PLoS ONE, 9*(9), e106953. https://doi.org/10.1371/journal.pone.0106953

The BOSS photos and their cut-outs are CC BY-SA 3.0, not MIT. The rendered art uses CC0
models and textures from Poly Haven (`art/CREDITS.md`).
