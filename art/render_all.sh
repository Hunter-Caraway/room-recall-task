#!/usr/bin/env bash
# Rebuild all renders. Resumes where it stopped: delete art/_downloads/raw to start over.
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-$HOME/.local/opt/blender-5.2.3-linux-x64/blender}"
for room in kitchen living_room hallway; do
  "$BLENDER" -b --python art/build_rooms.py -- --scene "$room" --mode final --samples 128
  "$BLENDER" -b --python art/build_rooms.py -- --scene "$room" --mode icons --samples 64
done
"$BLENDER" -b --python art/build_rooms.py -- --scene corridor --mode transition --samples 48
echo RENDER_DONE
