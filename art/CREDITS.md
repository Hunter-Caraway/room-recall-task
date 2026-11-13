# Art credits

## Target photos

The 42 target photos come from the **Bank of Standardized Stimuli (BOSS)**, licensed
under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/):

- Brodeur, M. B., Dionne-Dostie, E., Montreuil, T., & Lepage, M. (2010). The Bank of
  Standardized Stimuli (BOSS), a new set of 480 normative photos of objects to be used as
  visual stimuli in cognitive research. *PLoS ONE, 5*(5), e10773.
  https://doi.org/10.1371/journal.pone.0010773
- Brodeur, M. B., Guérard, K., & Bouras, M. (2014). Bank of Standardized Stimuli (BOSS)
  phase II: 930 new normative photos. *PLoS ONE, 9*(9), e106953.
  https://doi.org/10.1371/journal.pone.0106953

Changes made here: the white background is removed (`cutout_photos.py`), and when a
session runs, each photo is scaled, sometimes turned, tinted and given a shadow to place
it in a room. These cut-outs (`assets/objects/photos/`) and the room pictures shown with
them are adaptations, shared under the same CC BY-SA 3.0 license. The MIT license of the
code does not cover them.

## Everything else

All 3D models and textures, and the HDRI, come from [Poly Haven](https://polyhaven.com)
and are released under CC0 (public domain). `assets_manifest.py` lists every one used
(`ALL_MODELS`, `TEXTURES`, `HDRIS`).

- The four basements are original layouts built in `build_basements.py` and rendered in
  Blender. Pipes, wall shelves, the workbench, the sink and the light fittings are simple
  geometry built there.
- The decoys, practice objects and room filler are Poly Haven models shot in
  `render_objects.py` in the dataset's photo style. `made_objects.csv` lists which model
  each one is.
