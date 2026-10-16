#!/usr/bin/env bash
# Rebuilds the runtime package: organizers' MIT reference package at a pinned commit,
# plus our FHS engine (src/fhs.py), release engine (src/release.py) and our CLI changes (src/cli.patch). Hash-checked.
set -euo pipefail
UPSTREAM_SHA=30c8019d997f930eab9ba569d089d12298d86d8c
cd "$(dirname "$0")/.."
rm -rf qfbench2_track_forecasting /tmp/upstream && mkdir -p /tmp/upstream
curl -fsSL "https://github.com/Agenthon-2026/track2-forecasting-public/archive/${UPSTREAM_SHA}.tar.gz" | tar -xz -C /tmp/upstream
cp -r /tmp/upstream/*/qfbench2_track_forecasting ./qfbench2_track_forecasting
patch qfbench2_track_forecasting/cli.py src/cli.patch
cp src/fhs.py qfbench2_track_forecasting/fhs.py
cp src/release.py qfbench2_track_forecasting/release.py
echo "7a96adc2492820abaeae23fa5ef95d45c05dd37091e614e691990d26b9ef8593  qfbench2_track_forecasting/cli.py
9c784fc4a9a22ece3f5842e2386b0eb4e6377cdb439224819af8faf4501d6ca0  qfbench2_track_forecasting/fhs.py
7684aa4b4f3f028c14d2c847dc19336cc7db0ab6824f446d0d5f52f557611b4d  qfbench2_track_forecasting/release.py" | sha256sum -c -
