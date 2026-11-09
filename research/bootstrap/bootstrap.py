"""Numbers for the research note "Bootstrap: non-parametric vs parametric".

Usage: python research/bootstrap/bootstrap.py      -> writes data/bootstrap.json
Needs numpy (tested with 2.5). Every random quantity uses a fixed seed, so the output is reproducible.

Sections (match the note):
  toy        - five observations, a few non-parametric and parametric resamples written out by hand
  worked     - one dataset of n = 15 waiting times: ECDF vs fitted exponential, bootstrap distributions
               of the mean and the median (NP, P and the true sampling distribution), SEs and intervals
  b_choice   - Monte Carlo error of the bootstrap SE and of the 2.5% endpoint as a function of B
  coverage   - coverage and width of 95% intervals for the mean, model right (exponential data)
               and model wrong (lognormal data, exponential model), n = 10, 20, 50, 100, 250
  maximum    - Uniform(0, theta), statistic = sample maximum: where the NP bootstrap breaks
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
N01 = NormalDist()
ALPHA = 0.05


def q(a: np.ndarray, p: float, axis: int = -1) -> np.ndarray:
    return np.quantile(a, p, axis=axis)


def hist(values: np.ndarray, lo: float, hi: float, bins: int) -> list[float]:
    """Density histogram on a fixed grid (values outside the grid are dropped from the counts)."""
    counts, _ = np.histogram(values, bins=bins, range=(lo, hi))
    width = (hi - lo) / bins
    return [round(float(c) / (len(values) * width), 5) for c in counts]


# ---------------------------------------------------------------- 1) toy example
def toy() -> dict:
    x = np.array([2.1, 0.4, 3.8, 1.2, 6.5])
    rng = np.random.default_rng(11)
    np_rows = []
    for _ in range(4):
        idx = rng.integers(0, len(x), len(x))
        s = x[idx]
        np_rows.append({"idx": [int(i) + 1 for i in idx], "x": s.tolist(),
                        "mean": float(s.mean()), "median": float(np.median(s))})
    p_rows = []
    for _ in range(4):
        s = np.round(rng.exponential(x.mean(), len(x)), 1)
        p_rows.append({"x": s.tolist(), "mean": float(s.mean()), "median": float(np.median(s))})
    n = len(x)
    return {"x": x.tolist(), "mean": float(x.mean()), "median": float(np.median(x)),
            "np": np_rows, "p": p_rows, "distinct": math.comb(2 * n - 1, n),
            "distinct_15": math.comb(29, 15), "distinct_20": math.comb(39, 20),
            "p_out_5": (1 - 1 / 5) ** 5, "p_out_15": (1 - 1 / 15) ** 15, "p_out_inf": math.exp(-1)}


# ---------------------------------------------------------------- 2) worked example
MU_TRUE = 4.0          # true mean waiting time (minutes) of the generating exponential
N_WORK = 15
B_WORK = 10_000


def worked() -> tuple[dict, np.ndarray]:
    rng = np.random.default_rng(2026)
    x = np.round(rng.exponential(MU_TRUE, N_WORK), 1)
    x[x == 0] = 0.1
    n, xbar, s, med = len(x), float(x.mean()), float(x.std(ddof=1)), float(np.median(x))

    # ECDF vs fitted exponential vs true exponential (for the figure)
    grid = np.linspace(0, 16, 161)
    cdf = {"grid": grid.round(2).tolist(),
           "fit": (1 - np.exp(-grid / xbar)).round(4).tolist(),
           "true": (1 - np.exp(-grid / MU_TRUE)).round(4).tolist(),
           "data": np.sort(x).tolist()}
    ks = float(np.max(np.abs(np.arange(1, n + 1) / n - (1 - np.exp(-np.sort(x) / xbar)))))

    rng = np.random.default_rng(1)
    np_s = x[rng.integers(0, n, (B_WORK, n))]                                 # non-parametric resamples
    p_s = rng.exponential(xbar, (B_WORK, n))                                  # parametric resamples
    true_s = rng.exponential(MU_TRUE, (100_000, n))                           # the real sampling distribution

    stats = {}
    for name, f in (("mean", lambda a: a.mean(axis=1)), ("median", lambda a: np.median(a, axis=1))):
        t_np, t_p, t_true = f(np_s), f(p_s), f(true_s)
        est = xbar if name == "mean" else med
        lo, hi, bins = (0, 10, 50) if name == "mean" else (0, 10, 50)
        row = {
            "est": est,
            "se_true": float(t_true.std(ddof=1)), "se_np": float(t_np.std(ddof=1)), "se_p": float(t_p.std(ddof=1)),
            "bias_true": float(t_true.mean() - (MU_TRUE if name == "mean" else MU_TRUE * math.log(2))),
            "bias_np": float(t_np.mean() - est), "bias_p": float(t_p.mean() - est),
            "pct_np": [float(q(t_np, ALPHA / 2)), float(q(t_np, 1 - ALPHA / 2))],
            "pct_p": [float(q(t_p, ALPHA / 2)), float(q(t_p, 1 - ALPHA / 2))],
            "basic_np": [float(2 * est - q(t_np, 1 - ALPHA / 2)), float(2 * est - q(t_np, ALPHA / 2))],
            "basic_p": [float(2 * est - q(t_p, 1 - ALPHA / 2)), float(2 * est - q(t_p, ALPHA / 2))],
            "normal_np": [est - 1.96 * float(t_np.std(ddof=1)), est + 1.96 * float(t_np.std(ddof=1))],
            "distinct_np": int(len(np.unique(t_np))),
            "hist": {"lo": lo, "hi": hi, "bins": bins,
                     "np": hist(t_np, lo, hi, bins), "p": hist(t_p, lo, hi, bins), "true": hist(t_true, lo, hi, bins)},
        }
        stats[name] = row
    # closed forms used in the text
    tq = 2.1447866879169273                          # t_{0.975, 14}
    stats["mean"]["t_interval"] = [xbar - tq * s / math.sqrt(n), xbar + tq * s / math.sqrt(n)]
    stats["mean"]["se_formula"] = s / math.sqrt(n)
    stats["mean"]["se_np_ideal"] = math.sqrt((n - 1) / n) * s / math.sqrt(n)   # exact B -> infinity NP value
    stats["mean"]["se_p_ideal"] = xbar / math.sqrt(n)                          # exact B -> infinity P value
    stats["mean"]["se_true_exact"] = MU_TRUE / math.sqrt(n)
    # exact parametric interval from the pivot xbar/mu ~ Gamma(n, 1)/n (simulated with many draws)
    g = np.random.default_rng(5).gamma(n, 1.0, 2_000_000) / n
    stats["mean"]["exact_pivot"] = [xbar / float(q(g, 1 - ALPHA / 2)), xbar / float(q(g, ALPHA / 2))]
    stats["median"]["true_value"] = MU_TRUE * math.log(2)
    stats["median"]["mle_plugin"] = xbar * math.log(2)

    out = {"x": x.tolist(), "n": n, "mean": xbar, "sd": s, "median": med, "mu_true": MU_TRUE,
           "lambda_hat": 1 / xbar, "ks_fit": ks, "B": B_WORK, "cdf": cdf, "stats": stats}
    return out, x


# ---------------------------------------------------------------- 3) choosing B
def b_choice(x: np.ndarray) -> dict:
    n = len(x)
    ideal = math.sqrt((n - 1) / n) * float(x.std(ddof=1)) / math.sqrt(n)
    rng = np.random.default_rng(3)
    rows = []
    for B in (25, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
        reps = 400
        se, lo = np.empty(reps), np.empty(reps)
        for r in range(reps):
            m = x[rng.integers(0, n, (B, n))].mean(axis=1)
            se[r], lo[r] = m.std(ddof=1), q(m, ALPHA / 2)
        rows.append({"B": B, "se_mean": float(se.mean()), "se_sd": float(se.std(ddof=1)),
                     "se_cv": float(se.std(ddof=1) / ideal), "lo_sd": float(lo.std(ddof=1))})
    return {"ideal_se": ideal, "reps": 400, "rows": rows}


# ---------------------------------------------------------------- 4) coverage study for the mean
M_COV = 2000
B_COV = 999


def _bca_mean(x: np.ndarray, t: np.ndarray, est: np.ndarray) -> np.ndarray:
    """BCa interval for the mean. x: (m, n) samples, t: (m, B) bootstrap means, est: (m,)."""
    n = x.shape[1]
    prop = np.clip((t < est[:, None]).mean(axis=1), 1e-4, 1 - 1e-4)
    z0 = np.array([N01.inv_cdf(p) for p in prop])
    jack = (x.sum(axis=1, keepdims=True) - x) / (n - 1)                       # leave-one-out means
    d = jack.mean(axis=1, keepdims=True) - jack
    a = (d ** 3).sum(axis=1) / (6 * ((d ** 2).sum(axis=1)) ** 1.5)
    out = np.empty((x.shape[0], 2))
    for j, z in enumerate((N01.inv_cdf(ALPHA / 2), N01.inv_cdf(1 - ALPHA / 2))):
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        lev = np.array([N01.cdf(v) for v in adj])
        out[:, j] = [np.quantile(t[i], lev[i]) for i in range(len(lev))]
    return out


def coverage() -> dict:
    scenarios = {
        "right": {"draw": lambda r, size: r.exponential(1.0, size), "mean": 1.0},
        "wrong": {"draw": lambda r, size: r.lognormal(0.0, 1.0, size), "mean": math.exp(0.5)},
    }
    methods = ["np_pct", "np_basic", "np_t", "np_bca", "p_pct", "p_basic", "classic_t"]
    tq = {10: 2.2621571627409915, 20: 2.0930240544082634, 50: 2.009575234489209, 100: 1.9842169515086827,
          250: 1.9695368676395764}
    res: dict = {}
    for key, sc in scenarios.items():
        res[key] = []
        for n in (10, 20, 50, 100, 250):
            rng = np.random.default_rng(1000 + n + (0 if key == "right" else 7))
            hits = {m: 0 for m in methods}
            width = {m: 0.0 for m in methods}
            chunk = 50 if n <= 100 else 20
            for start in range(0, M_COV, chunk):
                x = sc["draw"](rng, (chunk, n))
                xbar, s = x.mean(axis=1), x.std(axis=1, ddof=1)
                idx = rng.integers(0, n, (chunk, B_COV, n))
                xs = np.take_along_axis(x[:, None, :].repeat(B_COV, axis=1), idx, axis=2)
                t = xs.mean(axis=2)
                ss = np.maximum(xs.std(axis=2, ddof=1), 1e-12)
                tstar = (t - xbar[:, None]) / (ss / math.sqrt(n))
                pt = rng.exponential(1.0, (chunk, B_COV, n)).mean(axis=2) * xbar[:, None]   # Exp(xbar) resamples
                ivs = {
                    "np_pct": np.stack([q(t, .025), q(t, .975)], 1),
                    "np_basic": np.stack([2 * xbar - q(t, .975), 2 * xbar - q(t, .025)], 1),
                    "np_t": np.stack([xbar - q(tstar, .975) * s / math.sqrt(n), xbar - q(tstar, .025) * s / math.sqrt(n)], 1),
                    "np_bca": _bca_mean(x, t, xbar),
                    "p_pct": np.stack([q(pt, .025), q(pt, .975)], 1),
                    "p_basic": np.stack([2 * xbar - q(pt, .975), 2 * xbar - q(pt, .025)], 1),
                    "classic_t": np.stack([xbar - tq[n] * s / math.sqrt(n), xbar + tq[n] * s / math.sqrt(n)], 1),
                }
                mu = sc["mean"]
                for m, iv in ivs.items():
                    hits[m] += int(((iv[:, 0] <= mu) & (mu <= iv[:, 1])).sum())
                    width[m] += float((iv[:, 1] - iv[:, 0]).sum())
            res[key].append({"n": n, **{m: hits[m] / M_COV for m in methods},
                             **{f"w_{m}": width[m] / M_COV / sc["mean"] for m in methods}})
            print(key, n, {m: round(hits[m] / M_COV, 3) for m in methods})
    cv_ln = math.sqrt(math.e - 1)
    return {"M": M_COV, "B": B_COV, "mc_se": math.sqrt(0.95 * 0.05 / M_COV), "methods": methods,
            "cv_lognormal": cv_ln, "asymptotic_p_cov_wrong": 2 * N01.cdf(1.959964 / cv_ln) - 1, **res}


# ---------------------------------------------------------------- 5) the maximum of a uniform
def maximum() -> dict:
    n, theta, B = 30, 1.0, 10_000
    rng = np.random.default_rng(30)
    x = rng.uniform(0, theta, n)
    mx = float(x.max())
    t_np = x[rng.integers(0, n, (B, n))].max(axis=1)
    t_p = rng.uniform(0, mx, (B, n)).max(axis=1)
    t_true = rng.uniform(0, theta, (100_000, n)).max(axis=1)
    lo, hi, bins = 0.80, 1.02, 44
    single = {"max": mx, "second": float(np.sort(x)[-2]), "p_tie_np": float((t_np == mx).mean()),
              "p_tie_theory": 1 - (1 - 1 / n) ** n, "lo": lo, "hi": hi, "bins": bins,
              "np": hist(t_np, lo, hi, bins), "p": hist(t_p, lo, hi, bins), "true": hist(t_true, lo, hi, bins),
              "np_atoms": [[float(v), float((t_np == v).mean())] for v in np.sort(x)[-5:]]}
    # coverage
    M, Bc = 2000, 999
    rng = np.random.default_rng(31)
    meth = ["np_pct", "np_basic", "p_pct", "p_basic", "p_pivot"]
    hits = {m: 0 for m in meth}
    for start in range(0, M, 100):
        xs = rng.uniform(0, theta, (100, n))
        m_ = xs.max(axis=1)
        idx = rng.integers(0, n, (100, Bc, n))
        tn = np.take_along_axis(xs[:, None, :].repeat(Bc, axis=1), idx, axis=2).max(axis=2)
        tp = rng.uniform(0, 1, (100, Bc, n)).max(axis=2) * m_[:, None]
        r = tp / m_[:, None]                                               # theta_hat*/theta_hat, pivot
        ivs = {
            "np_pct": (q(tn, .025), q(tn, .975)),
            "np_basic": (2 * m_ - q(tn, .975), 2 * m_ - q(tn, .025)),
            "p_pct": (q(tp, .025), q(tp, .975)),
            "p_basic": (2 * m_ - q(tp, .975), 2 * m_ - q(tp, .025)),
            "p_pivot": (m_ / q(r, .975), m_ / q(r, .025)),
        }
        for k, (a, b) in ivs.items():
            hits[k] += int(((a <= theta) & (theta <= b)).sum())
    cov = {k: v / M for k, v in hits.items()}
    print("maximum", cov)
    # exact interval from the pivot max/theta ~ Beta(n, 1): P(max/theta <= u) = u^n
    return {"n": n, "theta": theta, "single": single, "coverage": cov, "M": M, "B": Bc,
            "exact_interval": [mx / (1 - ALPHA / 2) ** (1 / n), mx / (ALPHA / 2) ** (1 / n)],
            "bias": -theta / (n + 1)}


def main() -> None:
    w, x = worked()
    out = {"toy": toy(), "worked": w, "b_choice": b_choice(x), "coverage": coverage(), "maximum": maximum()}
    path = ROOT / "data" / "bootstrap.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
