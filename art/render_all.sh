#!/usr/bin/env bash
# Rebuild all renders. Resumes where it stopped: delete art/_downloads/raw to start over.
# Each room type has three arrangements (one per condition); they share one set of icons.
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-$HOME/.local/opt/blender-5.2.3-linux-x64/blender}"
for room in bedroom living_room garage hallway; do
  for arrangement in 1 2 3; do
    "$BLENDER" -b --python art/build_rooms.py -- --scene "$room" --arrangement "$arrangement" --mode final --samples 128
  done
  "$BLENDER" -b --python art/build_rooms.py -- --scene "$room" --arrangement 1 --mode icons --samples 64
done
if [ ! -d art/_downloads/raw/transition ]; then
  "$BLENDER" -b --python art/build_rooms.py -- --scene corridor --mode transition --samples 48
fi
echo RENDER_DONE
