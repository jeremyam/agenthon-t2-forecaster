"""Launchlane T2 forecaster: filtered historical simulation (FHS) with vol mean-reversion.

Text-blind, CPU-only, numpy/pandas only. Everything is estimated from the panels handed to the
unit, at or before the as-of. No data is baked into the image.

Method, per card (daily cadence, dense history):
  1. Steps: first differences (level) or log(1+r) (log_return), dropping steps that span holes.
  2. Per-asset EWMA variance (lambda) and a long-run variance (trailing `lr_window` steps).
  3. Standardised residuals z_t = step_t / sigma_{t-1} (vector, by date) -> fat tails and
     cross-asset dependence come from the data itself.
  4. Simulate daily paths: future variance mean-reverts from the EWMA level to the long-run
     level at rate `phi` per step; innovations are block-bootstrapped residual vectors (whole
     dates, so correlation is kept), re-standardised by an EWMA-correlation-free scale.
     A per-draw lognormal vol multiplier adds parameter uncertainty (fatter long-horizon tails).
  5. Horizons are read off the same path, so cross-horizon dependence is a real path.
  6. Centre: zero drift for levels; for log returns a shrunk long-run mean.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FHSParams:
    lam: float = 0.97          # EWMA decay for current variance
    lr_window: int = 1260      # long-run variance window (steps)
    phi: float = 0.985         # daily persistence of variance deviation from long-run
    w_ewma: float = 1.0        # weight on EWMA (vs long-run) for the starting variance
    block: int = 5             # bootstrap block length
    resid_window: int = 2520   # residual pool (steps)
    volvol: float = 0.15       # sd of per-draw log vol multiplier
    scale: float = 1.0         # global width multiplier
    ret_drift_shrink: float = 0.5  # fraction of long-run mean log return used as drift
    level_drift: float = 0.0   # fraction of trailing mean level step used as drift
    min_steps: int = 250


def _gap_mask(idx: pd.DatetimeIndex) -> np.ndarray:
    d = np.diff(idx.values).astype("timedelta64[D]").astype(float)
    if len(d) == 0:
        return np.zeros(0, bool)
    thr = max(float(np.median(d)) * 10.0, 5.0)
    return d <= thr


def steps_frame(hist: dict[str, pd.Series], target_type: str) -> pd.DataFrame:
    cols = {}
    for a, s in hist.items():
        s = s.copy()
        s.index = pd.to_datetime(pd.Index(s.index).astype(str).str.slice(0, 10))
        s = s[~s.index.duplicated(keep="last")].sort_index().astype(float)
        if target_type == "log_return":
            st = np.log1p(s)
        else:
            st = s.diff()
        ok = np.r_[False, _gap_mask(s.index)]
        st = st.where(ok)
        cols[a] = st
    return pd.DataFrame(cols).dropna()


def ewma_var(x: np.ndarray, lam: float, init: float) -> np.ndarray:
    """sigma2[t] = variance forecast for step t made with info up to t-1."""
    out = np.empty(len(x))
    v = init
    for t in range(len(x)):
        out[t] = v
        v = lam * v + (1 - lam) * x[t] * x[t]
    return np.append(out, v)  # last element: forecast for the next (future) step


def simulate(
    hist: dict[str, pd.Series],
    assets: list[str],
    horizons: list[int],
    target_type: str,
    n_draws: int,
    seed: int,
    p: FHSParams | None = None,
) -> tuple[np.ndarray, dict]:
    p = p or FHSParams()
    rng = np.random.default_rng(seed)
    st = steps_frame({a: hist[a] for a in assets}, target_type)
    if len(st) < p.min_steps:
        raise ValueError(f"only {len(st)} aligned steps")
    X = st[assets].to_numpy(float)
    n, A = X.shape
    lr = X[-p.lr_window:]
    lr_var = lr.var(axis=0) + 1e-18
    init = X[: min(60, n)].var(axis=0) + 1e-18
    sig2 = np.column_stack([ewma_var(X[:, i], p.lam, init[i]) for i in range(A)])  # (n+1, A)
    cur = p.w_ewma * sig2[-1] + (1 - p.w_ewma) * lr_var
    Z = X / np.sqrt(sig2[:-1])
    Z = Z[60:][-p.resid_window:]
    Z = Z / Z.std(axis=0)  # unit variance per asset, keeps cross-correlation + tails
    m = len(Z)
    H = max(horizons)
    # future variance path (deterministic part)
    k = np.arange(1, H + 1)[:, None]
    var_path = lr_var + (cur - lr_var) * p.phi ** (k - 1)  # (H, A)
    sd_path = np.sqrt(var_path) * p.scale
    # block bootstrap indices
    nb = int(np.ceil(H / p.block))
    starts = rng.integers(0, max(m - p.block, 1), size=(n_draws, nb))
    idx = (starts[:, :, None] + np.arange(p.block)[None, None, :]).reshape(n_draws, -1)[:, :H]
    eps = Z[idx]  # (n_draws, H, A)
    mult = np.exp(p.volvol * rng.standard_normal((n_draws, 1, A)) - 0.5 * p.volvol**2)
    # common multiplier across assets is more realistic (vol regimes co-move)
    mult = np.exp(p.volvol * rng.standard_normal((n_draws, 1, 1)) - 0.5 * p.volvol**2)
    incr = eps * sd_path[None] * mult
    if target_type == "log_return":
        drift = p.ret_drift_shrink * X[-p.lr_window:].mean(axis=0)
        anchor = np.zeros(A)
    else:
        drift = p.level_drift * X[-300:].mean(axis=0)
        anchor = np.array([float(hist[a].sort_index().iloc[-1]) for a in assets])
    path = np.cumsum(incr + drift[None, None, :], axis=1)
    out = np.empty((n_draws, A, len(horizons)))
    for j, h in enumerate(horizons):
        out[:, :, j] = anchor[None, :] + path[:, h - 1, :]
    stats = {
        "n_steps": int(n),
        "lr_sd": {a: float(np.sqrt(lr_var[i])) for i, a in enumerate(assets)},
        "cur_sd": {a: float(np.sqrt(cur[i])) for i, a in enumerate(assets)},
        "drift": {a: float(drift[i]) for i, a in enumerate(assets)},
        "anchor": {a: float(anchor[i]) for i, a in enumerate(assets)},
        "params": p.__dict__,
    }
    return out, stats


#: Parameters selected on the 2003-2014 development backtest (see /workspace/agenthon/README.md).
TUNED = FHSParams(lam=0.97, lr_window=1260, phi=0.999, w_ewma=1.0, block=10, resid_window=2520, volvol=0.35, scale=0.9, ret_drift_shrink=0.0, level_drift=0.0, min_steps=250)
