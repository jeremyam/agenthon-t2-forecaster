# agenthon-t2-forecaster

This is the "Launchlane Forecast" entry for Agenthon 2026, Track 2 (time-series forecasting).

It is a text-blind, CPU-only probabilistic forecaster that uses filtered historical simulation (`src/fhs.py`):
- an EWMA-filtered 10-day block bootstrap of whole-date standardised residual vectors;
- a per-draw common volatility multiplier;
- joint paths across assets and horizons;
- 2000 draws.

Routing per card (v2, for the Final's short-horizon cards and new series):
- Daily series, horizons up to 10 business days (Final cards: 1-4): FHS with short-horizon
  parameters (EWMA lambda 0.93, 1-day blocks, no long-run blending). History needs 100+ daily
  rows in the last 400 days, so newly added series (T-bills, EM FX) work with short panels.
- Daily series, longer horizons (practice cards): the original tuned FHS.
- Official data releases and other non-daily series (monthly, weekly, quarterly): a per-print
  step model (`src/release.py`). The clock is the number of new prints, not business days. The
  centre adds recent drift; the width blends recent and long step sd; the shape is a smoothed bootstrap.
- Asset names are matched ignoring case and punctuation. Inconsistent monthly metadata falls
  back to cadence-based step counts. If every engine fails, a robust per-asset walk still writes
  a valid forecast, so a card is never left without output.
- Sparse or transfer-style daily cards still use the organizers' reference Gaussian walk.

The runtime package is the organizers' MIT-licensed reference package (Agenthon-2026/track2-forecasting-public, pinned commit) plus `src/fhs.py`, `src/release.py` and `src/cli.patch`. `scripts/assemble.sh` reassembles it and checks the hashes.

    bash scripts/assemble.sh
    docker build --platform linux/amd64 -t agenthon-t2-forecaster .
    docker run --rm --network=none -v <unit>:/input:ro -v <out>:/output agenthon-t2-forecaster \
      forecast --panels /input --text /input/text --asof YYYY-MM-DD --out /output/forecast.parquet

CI (`.github/workflows/publish.yml`) builds linux/amd64 and pushes it to `ghcr.io/jeremyam/agenthon-t2-forecaster`.

License: MIT. The upstream reference package is also MIT; see LICENSE.
