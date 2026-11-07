# Lab computer checklist

About 20 minutes the first time. Use the same computer, screen and mouse as the study.

## Install (once)

1. Install **PsychoPy Standalone 2026.2.5, Python 3.11 version** from https://www.psychopy.org/download.html. If it needs admin rights, ask IT.
2. Unzip the `MemoryTask-Windows` folder somewhere the account can write to, such as the Desktop.
3. Double-click `Self Test.bat`. It should end with `SELF TEST PASSED`. If it says PsychoPy was not found, put the full path of PsychoPy's `python.exe` into `psychopy_python.txt` in the same folder.
4. Double-click `Smoke Test.bat`. A window opens briefly; the console prints `smoke test ok` with the screen size.

## Try a session

1. Double-click `Run Task.bat`.
2. Type participant number `999`, then press Enter.
3. Do the practice, then one full room, including the sums.
4. Quit with **Ctrl+Shift+Q** during the second room.
5. Start `Run Task.bat` again, type `999`, press **F8** to resume, and finish.
6. Open `data\P999_results.csv` and confirm it has 30 rows, and that `study_dropped_frames` is 0 or close to it.
7. Delete every `P999_` file from `data`.

## Check while it runs

- [ ] The picture fills the screen without stretching (black bars at the sides are fine).
- [ ] Objects pick up and drop exactly under the pointer.
- [ ] A very quick click on Done still works.
- [ ] Y and N answer the sums.
- [ ] The cut from the full room is instant and the 3-second walk plays smoothly.
- [ ] No screen ever shows a condition letter or noise name.

Send back: anything that failed, the Windows version, the screen resolution, and
`selftest.log`.
