"""Numbers for the research note "Quasi-likelihood in GLMs".

Usage: python research/quasi/quasi.py      -> writes data/quasi.json
Needs numpy only (tested with 2.5). Every random quantity uses a fixed seed, so the output is reproducible.

Sections (match the note):
  qpois     - quasi-Poisson: insect counts, 4 sprays x 12 plots, Var(Y) = 3 mu (NB1 data). Poisson vs quasi-Poisson
              fits, group mean/variance table, IRLS trace, LR chi-square vs quasi F test for the spray effect
  qbin      - quasi-binomial: germination, 2 seed types x 2 extracts x 8 plates of 30 seeds, beta-binomial
              (rho = 0.06, so phi = 1 + 29 rho = 2.74), no true interaction. Binomial vs quasi-binomial fits,
              interaction test
  wedd      - Wedderburn's variance mu^2 (1 - mu)^2: continuous proportions (leaf area affected), 10 varieties x
              9 sites, logit mu = site + variety, Beta data with Var = mu^2 (1 - mu)^2. Fits with V = mu (1 - mu)
              and V = mu^2 (1 - mu)^2, Pearson residuals by fitted value, extended quasi-likelihood
  sim       - coverage of the 95% interval for a slope (M = 2,000 datasets per scenario):
              S1 NB1 counts n = 50; S2 continuous data with Var = 0.25 mu^2 fitted with V = mu and V = mu^2;
              S3 NB1 counts n = 12 (normal vs t quantiles); S4 binary data with heterogeneity (phi-hat);
              S5 type I error of the interaction test in the germination design (binomial LR vs quasi F)

The models are fitted from scratch (IRLS, Pearson phi, quasi-deviance, sandwich) so that every formula in the note
can be read in this file. Distribution functions (t, F, chi-square) come from the regularised incomplete beta and
gamma functions implemented below.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
Z975 = 1.959963984540054
SEED = 20261112


# ---------------------------------------------------------------- special functions (no scipy)
def _betacf(a: float, b: float, x: float) -> float:
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def gammaincc(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x)."""
    if x <= 0.0:
        return 1.0
    if x < a + 1.0:
        s = term = 1.0 / a
        ap = a
        for _ in range(1000):
            ap += 1.0
            term *= x / ap
            s += term
            if abs(term) < abs(s) * 1e-16:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny = 1e-300
    b = x + 1.0 - a
    c, d = 1.0 / tiny, 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b; d = d if abs(d) > tiny else tiny
        c = b + an / c; c = c if abs(c) > tiny else tiny
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-16:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x: float, k: int) -> float:
    return gammaincc(k / 2.0, x / 2.0)


def f_sf(f: float, d1: int, d2: int) -> float:
    return betainc(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * f))


def t_sf2(t: float, df: int) -> float:
    """Two-sided p-value P(|T| > |t|)."""
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def norm_sf2(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))


def t_q975(df: int) -> float:
    lo, hi = 0.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_sf2(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- quasi-likelihood GLM (IRLS)
VAR = {
    "mu": lambda m: m,
    "mu2": lambda m: m * m,
    "binom": lambda m: m * (1 - m),
    "wedd": lambda m: (m * (1 - m)) ** 2,
}


def _xlogy(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    out = np.zeros(np.broadcast(x, y).shape)
    nz = x != 0
    out[nz] = (x * np.log(np.where(y > 0, y, 1.0)))[nz]
    return out


def dev_units(var: str, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Quasi-deviance units d_i = 2 * int_mu^y (y - t) / V(t) dt."""
    if var == "mu":
        return 2 * (_xlogy(y, y / mu) - (y - mu))
    if var == "binom":
        return 2 * (_xlogy(y, y / mu) + _xlogy(1 - y, (1 - y) / (1 - mu)))
    if var == "mu2":
        return 2 * (-np.log(y / mu) + (y - mu) / mu)
    if var == "wedd":
        q = lambda m: (2 * y - 1) * np.log(m / (1 - m)) - y / m - (1 - y) / (1 - m)   # noqa: E731
        return 2 * (q(y) - q(mu))
    raise ValueError(var)


def fit(X: np.ndarray, y: np.ndarray, link: str, var: str, m: np.ndarray | None = None,
        maxit: int = 100, tol: float = 1e-12, trace: bool = False) -> dict:
    n, p = X.shape
    m = np.ones(n) if m is None else np.asarray(m, float)
    V = VAR[var]
    if link == "log":
        ginv, dmu, g = np.exp, (lambda mu: mu), np.log
        mu = (y + y.mean()) / 2 + 0.1
    else:
        ginv = lambda e: 1 / (1 + np.exp(-e))   # noqa: E731
        dmu = lambda mu: mu * (1 - mu)            # noqa: E731
        g = lambda mu: np.log(mu / (1 - mu))      # noqa: E731
        mu = (m * y + 0.5) / (m + 1)
    eta = g(mu)
    beta = np.zeros(p)
    steps = []
    dev_old = np.inf
    for it in range(1, maxit + 1):
        d = dmu(mu)
        w = m * d * d / V(mu)
        z = eta + (y - mu) / d
        XtW = X.T * w
        beta = np.linalg.solve(XtW @ X, XtW @ z)
        eta = X @ beta
        mu = ginv(eta)
        dev = float(np.sum(m * dev_units(var, y, mu)))
        if trace:
            steps.append({"it": it, "beta": beta.tolist(), "dev": dev})
        if abs(dev - dev_old) < tol * (abs(dev) + 0.1):
            break
        dev_old = dev
    d = dmu(mu)
    w = m * d * d / V(mu)
    A = (X.T * w) @ X
    Ainv = np.linalg.inv(A)
    resid = y - mu
    X2 = float(np.sum(m * resid ** 2 / V(mu)))
    phi = X2 / (n - p)
    s = (m * d / V(mu) * resid)[:, None] * X           # per-observation quasi-score contributions
    sand = Ainv @ (s.T @ s) @ Ainv
    return {"beta": beta, "mu": mu, "Ainv": Ainv, "X2": X2, "phi": phi, "dev": dev, "df": n - p, "it": it,
            "sand": sand, "pearson": np.sqrt(m) * resid / np.sqrt(V(mu)), "steps": steps}


def r(x, k=6):
    return [round(float(v), k) for v in x] if np.ndim(x) else round(float(x), k)


# ---------------------------------------------------------------- 1. quasi-Poisson: insect counts
def nb1(rng, mu, delta):
    """Var(Y) = mu (1 + delta): Poisson with a Gamma(shape mu/delta, scale delta) rate."""
    return rng.poisson(rng.gamma(shape=mu / delta, scale=delta))


def section_qpois(rng) -> dict:
    sprays = ["A", "B", "C", "D"]
    means = np.array([15.0, 12.0, 4.0, 6.0])
    k, delta = 12, 2.0
    g = np.repeat(np.arange(4), k)
    y = nb1(rng, means[g], delta).astype(float)
    X = np.column_stack([np.ones(len(y))] + [(g == j).astype(float) for j in (1, 2, 3)])
    P = fit(X, y, "log", "mu", trace=True)
    X0 = np.ones((len(y), 1))
    P0 = fit(X0, y, "log", "mu")
    se_p = np.sqrt(np.diag(P["Ainv"]))
    se_q = np.sqrt(P["phi"]) * se_p
    se_s = np.sqrt(np.diag(P["sand"]))
    df = P["df"]
    tq = t_q975(df)
    lr = P0["dev"] - P["dev"]
    F = (lr / 3) / P["phi"]
    groups = [{"spray": s, "true": means[j], "mean": float(y[g == j].mean()), "var": float(y[g == j].var(ddof=1))}
              for j, s in enumerate(sprays)]
    # contrast B vs A (beta_1)
    b1 = P["beta"][1]
    return {
        "n": len(y), "k": k, "phi_true": 1 + delta, "true_means": means.tolist(), "groups": groups,
        "beta": r(P["beta"]), "se_pois": r(se_p), "se_quasi": r(se_q), "se_sand": r(se_s),
        "phi": r(P["phi"]), "X2": r(P["X2"]), "dev": r(P["dev"]), "df": df, "t975": r(tq),
        "b1_ci_pois": r([b1 - Z975 * se_p[1], b1 + Z975 * se_p[1]]),
        "b1_ci_quasi": r([b1 - tq * se_q[1], b1 + tq * se_q[1]]),
        "b1_p_pois": norm_sf2(b1 / se_p[1]), "b1_p_quasi": t_sf2(b1 / se_q[1], df),
        "lr": r(lr), "lr_p": chi2_sf(lr, 3), "F": r(F), "F_p": f_sf(F, 3, df),
        "trace": [{"it": s["it"], "beta": r(s["beta"]), "dev": r(s["dev"])} for s in P["steps"]],
        "dev_null": r(P0["dev"]),
    }


# ---------------------------------------------------------------- 2. quasi-binomial: germination
GERM = {"m": 30, "plates": 8, "rho": 0.06}


def germ_data(rng) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Beta-binomial germination counts; logit p = 0.6 seed - 0.8 extract, no interaction."""
    mseeds, plates, rho = GERM["m"], GERM["plates"], GERM["rho"]
    rows = []
    for s, e in ((0, 0), (0, 1), (1, 0), (1, 1)):
        pr = 1 / (1 + math.exp(-(0.6 * s - 0.8 * e)))
        a, b = pr * (1 - rho) / rho, (1 - pr) * (1 - rho) / rho
        for _ in range(plates):
            rows.append((s, e, rng.binomial(mseeds, rng.beta(a, b))))
    arr = np.array(rows, float)
    return arr[:, 0], arr[:, 1], arr[:, 2]


def section_qbin(rng) -> dict:
    mseeds, plates, rho = GERM["m"], GERM["plates"], GERM["rho"]
    cells = [(s, e) for s in (0, 1) for e in (0, 1)]
    S, E, cnt = germ_data(rng)
    m = np.full(len(cnt), float(mseeds))
    y = cnt / m
    X = np.column_stack([np.ones(len(y)), S, E, S * E])
    X0 = X[:, :3]
    B = fit(X, y, "logit", "binom", m=m)
    B0 = fit(X0, y, "logit", "binom", m=m)
    se_b = np.sqrt(np.diag(B["Ainv"]))
    se_q = np.sqrt(B["phi"]) * se_b
    df = B["df"]
    lr = B0["dev"] - B["dev"]
    F = lr / B["phi"]
    b3 = B["beta"][3]
    cellsum = []
    for s, e in cells:
        k = (S == s) & (E == e)
        cellsum.append({"seed": s, "extract": e, "prop": float(cnt[k].sum() / m[k].sum()),
                        "true": 1 / (1 + math.exp(-(0.6 * s - 0.8 * e))),
                        "min": int(cnt[k].min()), "max": int(cnt[k].max())})
    return {
        "n": len(y), "m": mseeds, "plates": plates, "rho": rho, "phi_true": 1 + (mseeds - 1) * rho,
        "beta": r(B["beta"]), "se_bin": r(se_b), "se_quasi": r(se_q), "phi": r(B["phi"]), "X2": r(B["X2"]),
        "dev": r(B["dev"]), "df": df, "lr": r(lr), "lr_p": chi2_sf(lr, 1), "F": r(F), "F_p": f_sf(F, 1, df),
        "z_bin": r(b3 / se_b[3]), "t_quasi": r(b3 / se_q[3]), "cells": cellsum, "counts": cnt.astype(int).tolist(),
    }


# ---------------------------------------------------------------- 3. Wedderburn: continuous proportions
def section_wedd(rng) -> dict:
    nv, ns, phi_true = 10, 9, 1.0
    site = np.linspace(-5.0, -0.5, ns)
    var = np.linspace(0.0, 3.5, nv)
    vi, si = np.meshgrid(np.arange(nv), np.arange(ns), indexing="ij")
    vi, si = vi.ravel(), si.ravel()
    mu = 1 / (1 + np.exp(-(site[si] + var[vi])))
    # Beta with mean mu and variance phi mu^2 (1 - mu)^2:  a + b = 1 / (phi mu (1 - mu)) - 1
    ab = 1 / (phi_true * mu * (1 - mu)) - 1
    y = rng.beta(mu * ab, (1 - mu) * ab)
    n = len(y)
    X = np.column_stack([np.ones(n)] + [(si == j).astype(float) for j in range(1, ns)]
                        + [(vi == j).astype(float) for j in range(1, nv)])
    Bn = fit(X, y, "logit", "binom")
    W = fit(X, y, "logit", "wedd")
    out = {"n": n, "nv": nv, "ns": ns, "phi_true": phi_true, "y_min": float(y.min()), "y_max": float(y.max())}
    for key, F, var_name in (("binom", Bn, "binom"), ("wedd", W, "wedd")):
        eta = np.log(F["mu"] / (1 - F["mu"]))
        w = (F["mu"] * (1 - F["mu"])) ** 2 / VAR[var_name](F["mu"])
        h = w * np.einsum("ij,jk,ik->i", X, F["Ainv"], X)                 # leverages
        rs = F["pearson"] / np.sqrt(F["phi"] * (1 - h))                     # standardised Pearson residuals
        order = np.argsort(eta)
        bins = []
        for chunk in np.array_split(order, 5):
            bins.append({"lo": float(F["mu"][chunk].min()), "hi": float(F["mu"][chunk].max()),
                         "rvar": float(np.mean(rs[chunk] ** 2))})
        # extended quasi-likelihood with phi profiled out: phi = D / n
        Dn = F["dev"]
        eql = -0.5 * (n + n * math.log(2 * math.pi * Dn / n) + float(np.sum(np.log(VAR[var_name](y)))))
        j = 1 + (ns - 1) + (nv - 1) - 1          # column of the last variety (variety 10 vs variety 1)
        se = math.sqrt(F["phi"] * F["Ainv"][j, j])
        out[key] = {
            "phi": r(F["phi"]), "dev": r(Dn), "df": F["df"], "eql": r(eql), "bins": bins,
            "b_v10": r(F["beta"][j]), "se_v10": r(se), "sand_v10": r(math.sqrt(F["sand"][j, j])),
            "points": [[round(float(e), 3), round(float(v), 3)] for e, v in zip(eta, rs)],
            "it": F["it"],
        }
    out["b_v10_true"] = float(var[-1] - var[0])
    return out


# ---------------------------------------------------------------- 4. coverage simulations
def _cover(b, se, q, true):
    return (b - q * se <= true) & (true <= b + q * se)


def section_sim(rng) -> dict:
    M = 2000
    res = {"M": M}

    # S1: NB1 counts (Var = 3 mu), n = 50, log mu = 1 + 0.5 x, x ~ U(0, 2)
    def counts(n):
        x = rng.uniform(0, 2, n)
        X = np.column_stack([np.ones(n), x])
        y = nb1(rng, np.exp(1 + 0.5 * x), 2.0).astype(float)
        return X, y

    for key, n in (("s1", 50), ("s3", 12)):
        tq = t_q975(n - 2)
        c = {"pois": [], "quasi_z": [], "quasi_t": [], "sand": []}
        b1s, phis = [], []
        for _ in range(M):
            X, y = counts(n)
            F = fit(X, y, "log", "mu")
            b = F["beta"][1]
            se = math.sqrt(F["Ainv"][1, 1])
            c["pois"].append(_cover(b, se, Z975, 0.5))
            c["quasi_z"].append(_cover(b, math.sqrt(F["phi"]) * se, Z975, 0.5))
            c["quasi_t"].append(_cover(b, math.sqrt(F["phi"]) * se, tq, 0.5))
            c["sand"].append(_cover(b, math.sqrt(F["sand"][1, 1]), Z975, 0.5))
            b1s.append(b)
            phis.append(F["phi"])
        res[key] = {"n": n, **{k: float(np.mean(v)) for k, v in c.items()}, "sd_b1": float(np.std(b1s)),
                    "phi_mean": float(np.mean(phis)), "phi_q": r(np.quantile(phis, [0.1, 0.9]), 3)}

    # S2: continuous positive data with Var = 0.25 mu^2 (Gamma, cv 0.5), log mu = 1 + 1.5 x, n = 50
    n, shape = 50, 4.0
    tq = t_q975(n - 2)
    c = {"v_mu": [], "v_mu_sand": [], "v_mu2": []}
    b_mu, b_mu2, se_mu, se_mu2 = [], [], [], []
    for _ in range(M):
        x = rng.uniform(0, 2, n)
        X = np.column_stack([np.ones(n), x])
        mu = np.exp(1 + 1.5 * x)
        y = rng.gamma(shape, mu / shape)
        A = fit(X, y, "log", "mu")
        B = fit(X, y, "log", "mu2")
        sa = math.sqrt(A["phi"] * A["Ainv"][1, 1])
        sb = math.sqrt(B["phi"] * B["Ainv"][1, 1])
        c["v_mu"].append(_cover(A["beta"][1], sa, tq, 1.5))
        c["v_mu_sand"].append(_cover(A["beta"][1], math.sqrt(A["sand"][1, 1]), Z975, 1.5))
        c["v_mu2"].append(_cover(B["beta"][1], sb, tq, 1.5))
        b_mu.append(A["beta"][1]); b_mu2.append(B["beta"][1]); se_mu.append(sa); se_mu2.append(sb)
    res["s2"] = {"n": n, "phi_true": 1 / shape, **{k: float(np.mean(v)) for k, v in c.items()},
                 "sd_mu": float(np.std(b_mu)), "sd_mu2": float(np.std(b_mu2)),
                 "mse_mu": float(np.mean(se_mu)), "mse_mu2": float(np.mean(se_mu2)),
                 "bias_mu": float(np.mean(b_mu) - 1.5), "bias_mu2": float(np.mean(b_mu2) - 1.5)}

    # S4: binary data with strong unobserved heterogeneity: phi-hat of a quasi-binomial fit
    n = 200
    phis = []
    for _ in range(M):
        x = rng.normal(0, 1, n)
        u = rng.normal(0, 1.5, n)
        p = 1 / (1 + np.exp(-(-0.5 + 1.0 * x + u)))
        y = (rng.uniform(size=n) < p).astype(float)
        F = fit(np.column_stack([np.ones(n), x]), y, "logit", "binom")
        phis.append(F["phi"])
    res["s4"] = {"n": n, "sd_u": 1.5, "phi_mean": float(np.mean(phis)), "phi_q": r(np.quantile(phis, [0.025, 0.975]), 3)}
    # S5: type I error of the interaction test in the germination design (no true interaction)
    rej = {"lr": [], "F": []}
    phis = []
    for _ in range(M):
        S, E, cnt = germ_data(rng)
        m = np.full(len(cnt), float(GERM["m"]))
        X = np.column_stack([np.ones(len(cnt)), S, E, S * E])
        B1 = fit(X, cnt / m, "logit", "binom", m=m)
        B0 = fit(X[:, :3], cnt / m, "logit", "binom", m=m)
        lr = B0["dev"] - B1["dev"]
        rej["lr"].append(chi2_sf(lr, 1) < 0.05)
        rej["F"].append(f_sf(lr / B1["phi"], 1, B1["df"]) < 0.05)
        phis.append(B1["phi"])
    res["s5"] = {"lr": float(np.mean(rej["lr"])), "F": float(np.mean(rej["F"])), "phi_mean": float(np.mean(phis)),
                 "phi_q": r(np.quantile(phis, [0.1, 0.9]), 3)}
    res["mc_se"] = math.sqrt(0.95 * 0.05 / M)
    return res


def main() -> None:
    out = {
        "qpois": section_qpois(np.random.default_rng(SEED)),
        "qbin": section_qbin(np.random.default_rng(SEED + 1)),
        "wedd": section_wedd(np.random.default_rng(SEED + 2)),
        "sim": section_sim(np.random.default_rng(SEED + 3)),
    }
    path = ROOT / "data" / "quasi.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
