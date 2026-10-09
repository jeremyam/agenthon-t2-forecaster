#!/usr/bin/env bash
# Rebuilds the runtime package: organizers' MIT reference package at a pinned commit,
# plus our FHS engine (src/fhs.py) and our CLI changes (src/cli.patch). Hash-checked.
set -euo pipefail
UPSTREAM_SHA=30c8019d997f930eab9ba569d089d12298d86d8c
cd "$(dirname "$0")/.."
rm -rf qfbench2_track_forecasting /tmp/upstream && mkdir -p /tmp/upstream
curl -fsSL "https://github.com/Agenthon-2026/track2-forecasting-public/archive/${UPSTREAM_SHA}.tar.gz" | tar -xz -C /tmp/upstream
cp -r /tmp/upstream/*/qfbench2_track_forecasting ./qfbench2_track_forecasting
patch qfbench2_track_forecasting/cli.py src/cli.patch
cp src/fhs.py qfbench2_track_forecasting/fhs.py
echo "8d2f928f4e5ee9c971caab5a83e7edb7009883a3bbc6b92b6ffbc7bbc368b2d5  qfbench2_track_forecasting/cli.py
6d04491f49b7c1c23b70844ab75c65bfd1ea1303316b10ee28f02c3aeaf060ff  qfbench2_track_forecasting/fhs.py" | sha256sum -c -
