# PsychoPy feasibility

**Recommendation: yes, port it, using PsychoPy Standalone 2026.2.5 (the Python 3.11 installer) with our `.py` folder.** The one constraint to accept is that **PsychoPy must be installed on the lab PC; the single `.exe` goes away.** Keep the current pygame `.exe` until a person passes the lab-PC check in section 7. **Nothing here ran on Windows or on a physical display.**

Tags: [tested here], [docs], [forum]. "Tested" means Fedora 44 with the Radeon 780M GPU, a 60 Hz virtual output and synthetic X pointer events.

## 1. Install

- **Current:** 2026.2.5, `>=3.10,<3.13` ([PyPI](https://pypi.org/project/psychopy/)). [tested here]
- **System Python 3.14 fails.** pip falls back to the 2023.1.3 source zip: `BackendUnavailable: Cannot import 'setuptools.build_meta'`. Pinning gives `No matching distribution found for psychopy==2026.2.5`. [tested here]
- **Python 3.12 full install succeeds:** 1.4 GB, including PyQt6 at 272 MB. PTB and Qt load; no window opened with it. [tested here]
- **wxPython is no longer a blocker.** `psychopy` does not depend on it; only `psychopy-app` (the GUI) does, and that requires Python `<3.12`. PyPI has no Linux wx wheels. [tested here]
- **Minimal `--no-deps` works** on 3.11 and 3.12 at about 340 MB. [tested here]

Scratchpad root (tmpfs, lost on reboot): `/tmp/claude-1000/-home-hunter/71f3fc30-f3f9-4e28-8924-17ebebe8d9ee/scratchpad/psychopy_probe`

- Main venv, built with uv: `<root>/venv` (Python 3.11.18; pins in `<root>/venv-freeze.txt`)
- Same list built with plain pip: `<root>/pipcheck`

```
<root>/pythons/cpython-3.11-linux-x86_64-gnu/bin/python3.11 -m venv <root>/pipcheck
<root>/pipcheck/bin/pip install --no-deps psychopy==2026.2.5
<root>/pipcheck/bin/pip install arabic-reshaper freetype-py i18next json-tricks numpy packaging pandas pillow pyglet==1.5.27 pyserial python-bidi python-xlib pyyaml requests scipy six
```

pip warns `psychopy 2026.2.5 requires zope.interface==7.2, which is not installed`; harmless here. `python-xlib` is only for the test driver. Pass `--no-bin` to `uv python install`, or it writes symlinks into `~/.local/bin`.

## 2. Does it run? Yes

**The desktop was locked** (`LockedHint=yes`), so KWin never mapped managed windows and pyglet and even plain pygame hung. This is not a PsychoPy fault. Everything ran in a private `kwin_wayland --virtual` with rootful Xwayland, invisible to the desktop. **The real desktop session is untested.** [tested here]

| Measure (1920x1080, pyglet, 3.11) | PsychoPy | pygame-ce |
|---|---|---|
| `full.jpg` load | 20-28 ms | 11-12 ms |
| 15 sprites load | 12-26 ms | 1.5 ms |
| 72 transition frames load | 0.6-1.0 s | 0.3 s |
| Placement draw CPU, median | 3.3 ms | 1.1 ms |
| Placement frame, median / max | 16.7 / 18 ms | 16.1 / 17 ms |

- Room pixels versus the file on disk: identical (max difference 0). [tested here]
- `win.getMovieFrame` screenshots and a windowed run work. [tested here]
- **Port spike:** unmodified `session.py`, with no pygame loaded, ran a full 15-object room with real X drags. Kitchen and living room each wrote 15 CSV rows, scored 15/15, max error 0.07%. [tested here]

Rerun it invisibly:

```
<root>/work/spike_nested.sh <root>/work/out 2 7
```

## 3. Backends and Mouse

| Backend | Result on 2026.2.5 |
|---|---|
| pyglet | Works. Also works with `pyglet==1.4.11`, the version PsychoPy pins on Windows. [tested here] |
| glfw | `TypeError: Requested backend is not subclass of BaseBackend`. Moved to a plugin; a [third-party note](https://github.com/aforren1/psych-nix) says that plugin is incompatible with 2026. [tested here for the error] |
| pygame | `TypeError: Can't instantiate abstract class PygameBackend`. [Officially deprecated](https://www.psychopy.org/api/visual/window.html). [tested here, docs] |

Use pyglet. Mouse results:

- 4000 frames, 331 of 331 clicks detected, no slowdown. The [reported `getPressed` degradation](https://discourse.psychopy.org/t/mouse-event-getpressed-stops-functioning/14388) did not reproduce. [tested here, forum]
- **A 5 ms sub-frame click is missed by `event.Mouse` polling; the pygame queue catches it.** Real clicks are longer, but a long frame could hide one.
- Pointer position lagged about 20 ms versus about 7 ms, with 48-49 of 50 fast moves seen (pygame 50). Reads were up to 1 px off with pyglet 1.5.27 and exact with 1.4.11. Against the 80 px tolerance, the 1 px offset is negligible. [tested here]
- To build and test: take press and release from pyglet window handlers instead of polling, or [`hardware.Mouse`](https://discourse.psychopy.org/t/getpos-fails-to-record-mouse-position-inside-while-loop/35930). Neither tested.

## 4. Windows delivery

| Option | Verdict |
|---|---|
| (a) Standalone plus our `.py` files | **Choose this.** [Download page](https://www.psychopy.org/download.html): the option that "just works". Installer is 528 MB ([releases](https://github.com/psychopy/psychopy/releases)). |
| (b) venv and pip | Fallback. Windows resolves on 3.11 (100 packages, `esprima` source-only). On 3.12: `all versions of pywinhook ... have no usable wheels`. Resolve only, not installed. [tested here] |
| (c) PyInstaller | No. Team: ["generally painful, it isn't supported by us"](https://discourse.psychopy.org/t/how-to-build-exe-executible-on-windows/1103) (2016). A [2023 success](https://discourse.psychopy.org/t/packaging-a-psychopy-experiment-with-pyinstaller-it-works/34165) needed manual freetype DLLs and dropped ioHub. [psychopy-freeze](https://github.com/jryzkns/psychopy-freeze) dates from 2020. [forum] |
| (d) Builder Code components | No. Drag, tray and resume would all be custom code anyway, and it would displace our tested session layer. |

**Pick the 3.11 installer.** Releases ship both 3.10 and 3.11; `config.py` imports `tomllib`, which fails on 3.10 with `No module named 'tomllib'`. [tested here]

**GitHub Actions cannot replace the lab check.** Hosted Windows runners [have no GPU](https://amiralizadeh9480.medium.com/how-to-run-opengl-based-tests-on-github-actions-60f270b1ea2c), and getting OpenGL there means [adding a Mesa llvmpipe DLL](https://github.com/mmozeiko/build-mesa/). PsychoPy's own `pytests.yaml` covers only macOS and Ubuntu with xvfb, not Windows. On Linux, `from psychopy import visual` or `event` raises `NoSuchDisplayException` with no display, while `core`, `data`, `logging` and `gui` import fine. [tested here, forum; Mesa route untested]

So CI runs logic tests and zips the folder; it would not prove graphics.

## 5. Timing

Mega-study, Windows 10 ([Bridges et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7512138/), Table 2; SD / lag, ms). Expyriment is built on Pygame; pygame-ce itself was not tested. [docs]

| | Visual onset | Audio onset |
|---|---|---|
| PsychoPy (PTB audio) | 0.35 / 7.10 | 0.96 / 0.85 |
| Expyriment | 0.19 / 5.98 | 13.72 / 106.83 |

[PsychoPy recommends a photodiode](https://www.psychopy.org/general/timing/index.html) for your own setup; none was used here.

30 s study, one run each [tested here]:

- PsychoPy: 30,018 ms, 1800 frames, interval SD 0.66 ms, 0 dropped. The final flip blocked 15.6 ms, so it is tied to the display refresh.
- pygame-ce: 30,002 ms, but the flip returned in 1.5 ms, so the number does not show when the pixels changed.
- The transition played at 16.6 ms per frame, max 18.4.

**Frame precision is not needed here.** One frame is 0.06% of 30 s, with no brief stimuli or reaction-time analysis. **Visual timing is not a reason to port.** The audio gap matters only if the game later plays or syncs sound.

## 6. What the project would gain

- **Use:** frame-drop logging (`recordFrameIntervals`, `nDroppedFrames`, `saveFrameIntervals`) as a per-room column, and the vsync-tied cut. [tested here]
- **Later:** PTB audio. `psychtoolbox` imports and its clock runs; no sound played. [tested here, partial]
- **Write-up:** a citable, standard tool.
- **Skip:** ExperimentHandler (writes a wide CSV [tested here], but `data.py` already has per-object rows and resume) and TrialHandler (`schedule.py` covers it; not tested).
- **Low value, not researched:** `expInfo` dialog (Qt loads, dialog not opened), monitor calibration (we work in pixels), Pavlovia (in-lab study).

## 7. The port

**Unchanged:** `session.py`, `schedule.py`, `scoring.py`, `data.py`, `config.py`, `config.toml`, assets, and the CSV format. Canvas coordinates stay top-left and y-down, so data stay comparable.

**Changes:**

- **`app.py`:** rewritten (the largest job, 429 lines today). Map coordinates with `(x-960, 540-y)`, use Pillow for alpha hit-tests, port text, keys and the fade, and preload transition frames. Add our own letterbox scaling: `pygame.SCALED` did this automatically, and a non-1080p display needs a scale factor and `interpolate=True`. Windows DPI scaling is untested.
- **`selftest.py`:** it depends on SDL's dummy driver. Move the drag logic into a graphics-free class and script that instead.
- **`build-windows.yml`:** remove PyInstaller, run the logic tests, upload a zip.
- **New:** `Run Task.bat`, a lab-PC `--smoke-test`, README and `LAB_CHECKLIST.md` updates.

**Lab PC, once:** install `StandalonePsychoPy-2026.2.5post1-win64-3.11.exe` (admin rights unverified), unzip our folder, and confirm the `python.exe` path.

**Experimenter:** double-click `Run Task.bat`, which runs the following ([forum pattern](https://discourse.psychopy.org/t/run-psychopy-experiment-without-opening-builder/9290); the install path varies):

```
"C:\Program Files\PsychoPy\python.exe" run_task.py
```

Then as now: participant number, F8, Space, Ctrl+Shift+Q. **Participant:** no change.

**Must pass on the lab PC before retiring the `.exe`:** fullscreen and scaling, the real mouse through a complete session, crash and resume, `nDroppedFrames` near 0, a very quick click on Done, and ideally a photodiode check of the blink.

If one fails and cannot be fixed, stay on pygame. Session logic and data formats are shared, so the main risk is schedule: a rewritten front end and one more install.

**Not tested:** Windows, Standalone itself, a physical monitor, a real mouse, a visible desktop window, sound playback, dialogs, resume under PsychoPy.
