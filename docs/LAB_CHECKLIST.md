# Lab computer checklist

About 20 minutes the first time. Use the same computer, screen and mouse as the study.

## Install (once)

1. On GitHub, click **Code**, then **Download ZIP**. Right-click the zip, choose
   **Extract All**, and open the extracted folder somewhere the account can write to,
   such as the Desktop.
2. Click the folder's address bar, type `cmd`, press Enter, then type
   `"Run Task.bat" --self-test` and press Enter. The first time, it sets up Python
   (internet needed, about a minute). It should end with `SELF TEST PASSED`.
   If Windows warns about a file from the internet, choose **More info**, then **Run anyway**.

## Try a session

1. Double-click `Run Task.bat`.
2. Type participant number `999`, then press Enter.
3. Do the practice room, then one full scored room, including the sums.
4. Quit with **Ctrl+Shift+Q** during the second scored room.
5. Start `Run Task.bat` again, type `999`, press **F8** to resume, and finish (about 30 minutes).
6. Open `data\P999_trials.csv` and confirm it has 9 rows, with `targets` adding up to 42 and `study_dropped_frames` 0 or close to it. Open `data\P999_tiles.csv` and confirm it has 108 rows (9 rooms x 12 tiles).
7. Open `data\P999_checks.csv` and confirm it has digit-span and slider rows for blocks 1, 2 and 3.
8. Delete every `P999_` file from `data`.

## Check while it runs

- [ ] The picture fills the screen without stretching (black bars at the sides are fine).
- [ ] The objects in the room look like they belong there: right size, on a surface, nothing floating or cut off.
- [ ] Clicking a grid tile puts a yellow border on it; clicking again removes it.
- [ ] Done works with no tiles selected, and a very quick click on Done still works.
- [ ] The grid pictures are sharp and every tile is the same size.
- [ ] Y and N answer the sums.
- [ ] "Please wait for the experimenter" appears before each block, and F8 does nothing for the first 10 seconds.
- [ ] Digit-span digits are easy to read; typing, Backspace and Enter work.
- [ ] The sliders show no marker until clicked, and the marker follows a drag.
- [ ] No screen ever shows a condition letter or noise name.

Send back: anything that failed, the Windows version, the screen resolution, and
`selftest.log`.
