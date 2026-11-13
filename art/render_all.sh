#!/usr/bin/env bash
# Rebuild every picture the task uses from the drawings in art/drawings/ (needs cairosvg),
# then check that every participant number up to 120 gets a deal that fits the rooms.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
"$PY" art/build_drawn.py
