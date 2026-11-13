#!/usr/bin/env bash
# Rebuild every picture the task uses. Resumes where it stopped: finished renders are kept.
#   1. cut the dataset photos out of their white background
#   2. studio shots of the made objects (decoys, practice, filler)
#   3. the four basements (empty room + spots)
#   4. assemble assets/ and check the spots
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-$HOME/.local/opt/blender-5.2.3-linux-x64/blender}"
PY="${PY:-.venv/bin/python}"
"$PY" art/cutout_photos.py art/dataset_photos art/dataset_cutouts
"$BLENDER" -b --python art/render_objects.py
for room in storage laundry workshop practice; do
  "$BLENDER" -b --python art/build_basements.py -- --room "$room" --mode final --samples 128
done
"$PY" art/assemble_assets.py
echo RENDER_DONE
