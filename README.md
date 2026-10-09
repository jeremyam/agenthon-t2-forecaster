# agenthon-t2-forecaster

This is the "Launchlane Forecast" entry for Agenthon 2026, Track 2 (time-series forecasting).

It is a text-blind, CPU-only probabilistic forecaster that uses filtered historical simulation (`src/fhs.py`):
- an EWMA-filtered 10-day block bootstrap of whole-date standardised residual vectors;
- a per-draw common volatility multiplier;
- joint paths across assets and horizons;
- 2000 draws.

Cards with short or sparse history use the organizers' reference Gaussian walk.

The runtime package is the organizers' MIT-licensed reference package (Agenthon-2026/track2-forecasting-public, pinned commit) plus `src/fhs.py` and `src/cli.patch`. `scripts/assemble.sh` reassembles it and checks the hashes.

    bash scripts/assemble.sh
    docker build --platform linux/amd64 -t agenthon-t2-forecaster .
    docker run --rm --network=none -v <unit>:/input:ro -v <out>:/output agenthon-t2-forecaster \
      forecast --panels /input/panels --text /input/text --asof YYYY-MM-DD --out /output/forecast.parquet

CI (`.github/workflows/publish.yml`) builds linux/amd64 and pushes it to `ghcr.io/jeremyam/agenthon-t2-forecaster`.

License: MIT. The upstream reference package is also MIT; see LICENSE.
