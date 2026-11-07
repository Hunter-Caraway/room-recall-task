# Colored noise memory task

An original object-placement memory task for an in-lab psychology study on colored
noise. Participants study a cluttered room, the room blinks empty, and they drag each
object back to where it was.

This is the **2-room test build**. It checks that the whole flow works before the
remaining rooms are made.

## Session flow

1. The experimenter types the participant number.
2. Practice room (not saved).
3. `Please wait for the experimenter`: set the noise for this block using the run sheet, then press **F8**.
4. Study the furnished room for 30 seconds.
5. The room blinks empty. Drag every object from the tray back into place, then press Done.
6. A 3-second doorway transition plays, then the next block starts at step 3.

Participants are never shown a condition. The game plays no audio: noise is controlled
outside it.

## Experimenter controls

| Key | Action |
| --- | --- |
| F8 | Continue past a pause, or resume an unfinished session |
| Space | Participant starts a room after reading the instructions |
| Ctrl+Shift+Q | Quit at any time. Finished rooms stay saved |

## Files written to `data/`

- `run_sheet.csv`: **experimenter only.** Each participant's condition for each block.
- `P001_results.csv`: one row per object for that participant.
- `P001_state.json`: progress, used to resume after a crash.
- `error_log.txt`: appears only if the game crashes.

Keep the key to what A, B, C and D mean somewhere else.

Results columns include `condition`, `room`, `object`, correct and placed positions in
room pixels, `distance_pct` (percent of room width), `score` (1 or 0), `placement_order`,
timings in milliseconds, `moves`, and `session_resumed`. Practice is never saved.

## Changing the study

Edit `config.toml`: conditions, room sets, study time, transition time, tolerance. It must
have an even number of conditions, with one room set per condition. Raw positions are
saved, so tolerance can also be changed during analysis without rerunning anyone.

## Counterbalancing

The participant number sets everything, so the same number always gets the same order.
Condition order uses a balanced Latin square. Room sets rotate separately, so over
`n x n` participants every order meets every rotation. 35 participants is not a multiple of
16 (or of 4 in this build), so groups are not exactly equal. Each row saves the order
that participant received, for use in analysis.

## Development

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python run_task.py --windowed
```

`run_task.py --self-test` plays a full scripted session without a window, including a
crash and resume. GitHub Actions builds `MemoryTask.exe` and runs that same self-test
inside it on Windows.

## Art

Everything is made from CC0 assets from [Poly Haven](https://polyhaven.com), see
`art/CREDITS.md`. To rebuild, install Blender 5.2 and Python with Pillow, then run:

```
python art/fetch_assets.py laminate_floor_02 herringbone_parquet floor_tiles_06 long_white_tiles marble_01 kitchen_wood fabric_pattern_07 oak_veneer_01
art/render_all.sh
python art/postprocess.py
```

`postprocess.py` fails if a scored object is more than 10% hidden, touches the image edge
or is too small.

## Known limits of the test build

- Practice reuses the kitchen, so practice shows part of a scored room. Real participants need a separate practice room.
- Unscored clutter and furniture stay visible when the room blinks empty.
- An object placed back shows no contact shadow, so it can look slightly lifted.
- Depth is scored in screen position. Objects stay at their original on-screen size.
- A common-sense guessing baseline has not been measured yet.
