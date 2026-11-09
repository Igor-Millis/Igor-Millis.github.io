"""Numbers for the research note "From Poisson to the negative binomial".

Usage: python research/negbin/negbin.py      -> writes data/negbin.json
Needs numpy only (tested with 2.5). Every random quantity uses a fixed seed, so the output is reproducible.

Sections (match the note):
  mixture   - Y | Z ~ Poisson(Z), Z ~ Gamma(alpha = 2, rate beta = 0.5): one million draws of the two-stage
              experiment against the closed-form negative binomial and against a Poisson with the same mean
  worked    - one simulated dataset (n = 500, log mu = 1 + 0.5 x, theta = 1.5): Poisson GLM vs negative binomial
              GLM (IRLS + profile ML for theta), dispersion statistics, likelihood-ratio test, observed vs expected
              frequencies
  coverage  - coverage of the 95% Wald interval for the slope under Poisson, quasi-Poisson and negative binomial
              fits, for theta = infinity (Poisson data), 10, 2 and 0.5 (n = 200, M = 2,000 datasets each)

The GLMs are fitted from scratch (no statsmodels) so that every step in the note can be read in this file.
For integer y, lgamma(y + theta) - lgamma(theta) = sum_{j < y} log(theta + j), which keeps the negative binomial
log-likelihood exact and vectorised without scipy.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
Z975 = 1.959963984540054


# ---------------------------------------------------------------- likelihoods
def lfact(y: np.ndarray) -> np.ndarray:
    return np.array([math.lgamma(v + 1.0) for v in np.asarray(y).ravel()]).reshape(np.shape(y))


def _rising_log(y: np.ndarray, theta: float) -> np.ndarray:
    """log Gamma(y + theta) - log Gamma(theta) for integer y >= 0, i.e. sum_{j=0}^{y-1} log(theta + j)."""
    ymax = int(y.max()) if y.size else 0
    if ymax == 0:
        return np.zeros_like(y, dtype=float)
    cum = np.concatenate([[0.0], np.cumsum(np.log(theta + np.arange(ymax)))])
    return cum[y]


def ll_pois(y: np.ndarray, mu: np.ndarray, lf: np.ndarray) -> float:
    return float(np.sum(y * np.log(mu) - mu - lf))


def ll_nb(y: np.ndarray, mu: np.ndarray, theta: float, lf: np.ndarray) -> float:
    return float(np.sum(_rising_log(y, theta) - lf + theta * np.log(theta / (theta + mu)) + y * np.log(mu / (theta + mu))))


def nb_pmf(k: np.ndarray, mu: float | np.ndarray, theta: float) -> np.ndarray:
    k = np.asarray(k)
    lg = np.array([math.lgamma(v + theta) - math.lgamma(theta) - math.lgamma(v + 1.0) for v in k.ravel()]).reshape(k.shape)
    return np.exp(lg + theta * np.log(theta / (theta + mu)) + k * np.log(mu / (theta + mu)))


def pois_pmf(k: np.ndarray, mu: float | np.ndarray) -> np.ndarray:
    k = np.asarray(k)
    lf = np.array([math.lgamma(v + 1.0) for v in k.ravel()]).reshape(k.shape)
    return np.exp(k * np.log(mu) - mu - lf)


# ---------------------------------------------------------------- GLM fitting (IRLS)
def irls(X: np.ndarray, y: np.ndarray, theta: float | None, beta: np.ndarray | None = None,
         tol: float = 1e-10, it: int = 100) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Log-link GLM. theta = None -> Poisson (V = mu); else negative binomial NB2 (V = mu + mu^2 / theta).

    With the log link, d eta / d mu = 1 / mu, so the IRLS weight is w = (d mu/d eta)^2 / V = mu^2 / V and the working
    response is z = eta + (y - mu) / mu. Returns (beta, mu, (X'WX)^-1)."""
    if beta is None:
        beta = np.zeros(X.shape[1])
        beta[0] = math.log(y.mean() + 0.1)
    for _ in range(it):
        eta = X @ beta
        mu = np.exp(eta)
        V = mu if theta is None else mu + mu * mu / theta
        w = mu * mu / V
        z = eta + (y - mu) / mu
        XtW = X.T * w
        new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new
    mu = np.exp(X @ beta)
    V = mu if theta is None else mu + mu * mu / theta
    cov = np.linalg.inv((X.T * (mu * mu / V)) @ X)
    return beta, mu, cov


def theta_ml(y: np.ndarray, mu: np.ndarray, lf: np.ndarray, lo: float = -6.0, hi: float = 14.0) -> float:
    """Maximise the NB log-likelihood in theta for fixed mu (golden-section search on log theta)."""
    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = ll_nb(y, mu, math.exp(c), lf), ll_nb(y, mu, math.exp(d), lf)
    while b - a > 1e-6:
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = ll_nb(y, mu, math.exp(c), lf)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = ll_nb(y, mu, math.exp(d), lf)
    return math.exp((a + b) / 2)


def fit_nb(X: np.ndarray, y: np.ndarray, lf: np.ndarray, beta0: np.ndarray | None = None) -> dict:
    """Alternate IRLS for beta (theta fixed) and profile ML for theta (beta fixed) - what MASS::glm.nb does."""
    beta, mu, _ = irls(X, y, None, beta0)
    theta = theta_ml(y, mu, lf)
    ll_old = -np.inf
    for _ in range(100):
        beta, mu, cov = irls(X, y, theta, beta)
        theta = theta_ml(y, mu, lf)
        ll = ll_nb(y, mu, theta, lf)
        if abs(ll - ll_old) < 1e-9:
            break
        ll_old = ll
    beta, mu, cov = irls(X, y, theta, beta)
    return {"beta": beta, "mu": mu, "cov": cov, "theta": theta, "ll": ll_nb(y, mu, theta, lf)}


def theta_se(y: np.ndarray, mu: np.ndarray, theta: float) -> float:
    """Observed-information SE of theta (beta and theta are orthogonal, so this block stands alone)."""
    ymax = int(y.max())
    j = np.arange(max(ymax, 1))
    inv2 = 1.0 / (theta + j) ** 2
    cum2 = np.concatenate([[0.0], np.cumsum(inv2)])
    # d2 l / d theta2 = sum[ -sum_{j<y} 1/(theta+j)^2 + 1/theta - 2/(theta+mu) + (y+theta)/(theta+mu)^2 ]
    h = np.sum(-cum2[y] + 1 / theta - 2 / (theta + mu) + (y + theta) / (theta + mu) ** 2)
    return float(1 / math.sqrt(-h))


# ---------------------------------------------------------------- 1) the mixture, by simulation
def mixture() -> dict:
    alpha, beta = 2.0, 0.5                       # Z ~ Gamma(shape alpha, rate beta): E Z = 4, Var Z = 8
    N = 1_000_000
    rng = np.random.default_rng(20261109)
    z = rng.gamma(shape=alpha, scale=1 / beta, size=N)
    y = rng.poisson(z)
    mean_th = alpha / beta
    var_th = alpha / beta + alpha / beta ** 2
    K = 21
    k = np.arange(K)
    emp = np.bincount(y, minlength=K)[:K] / N
    p = beta / (1 + beta)
    nb = np.array([math.exp(math.lgamma(v + alpha) - math.lgamma(alpha) - math.lgamma(v + 1)) * p ** alpha * (1 - p) ** v for v in k])
    po = pois_pmf(k, mean_th)
    # law of total variance, piece by piece, from the simulation
    return {
        "alpha": alpha, "beta": beta, "N": N, "p": p,
        "mean_th": mean_th, "var_th": var_th, "mean_sim": float(y.mean()), "var_sim": float(y.var(ddof=1)),
        "ez_sim": float(z.mean()), "varz_sim": float(z.var(ddof=1)),
        "k": k.tolist(), "emp": [round(float(v), 6) for v in emp], "nb": [round(float(v), 6) for v in nb],
        "pois": [round(float(v), 6) for v in po],
        "p0": {"emp": float(emp[0]), "nb": float(nb[0]), "pois": float(po[0])},
        "tail10": {"emp": float(np.mean(y >= 10)), "nb": float(1 - nb[:10].sum()), "pois": float(1 - po[:10].sum())},
        "max_abs_err": float(np.max(np.abs(emp - nb))),
    }


# ---------------------------------------------------------------- 2) worked example
def worked() -> dict:
    n, b0, b1, theta = 500, 1.0, 0.5, 1.5
    rng = np.random.default_rng(7)
    x = rng.normal(size=n)
    mu = np.exp(b0 + b1 * x)
    z = rng.gamma(shape=theta, scale=1 / theta, size=n)     # E Z = 1, Var Z = 1/theta
    y = rng.poisson(mu * z)
    X = np.column_stack([np.ones(n), x])
    lf = lfact(y)
    p = X.shape[1]

    bp, mup, covp = irls(X, y, None)
    ll_p = ll_pois(y, mup, lf)
    pearson_p = float(np.sum((y - mup) ** 2 / mup))
    with np.errstate(divide="ignore", invalid="ignore"):
        dev_p = float(2 * np.sum(np.where(y > 0, y * np.log(y / mup), 0.0) - (y - mup)))
    phi = pearson_p / (n - p)

    nb = fit_nb(X, y, lf, bp)
    mun, th = nb["mu"], nb["theta"]
    pearson_nb = float(np.sum((y - mun) ** 2 / (mun + mun ** 2 / th)))
    with np.errstate(divide="ignore", invalid="ignore"):
        dev_nb = float(2 * np.sum(np.where(y > 0, y * np.log(y / mun), 0.0) - (y + th) * np.log((y + th) / (mun + th))))
    lr = 2 * (nb["ll"] - ll_p)
    # H0: theta = infinity is on the boundary -> LR ~ 0.5 chi2_0 + 0.5 chi2_1 ; P(chi2_1 > t) = erfc(sqrt(t/2))
    p_lr = 0.5 * math.erfc(math.sqrt(lr / 2))
    log10_p = (math.log10(p_lr) if p_lr > 0 else
               math.log10(0.5) + (-lr / 2 - 0.5 * math.log(math.pi * lr / 2)) / math.log(10))   # erfc tail asymptotic

    # observed vs expected frequencies: E[#{Y = k}] = sum_i P(Y_i = k)
    K = 16
    ks = np.arange(K)
    obs = np.bincount(np.minimum(y, K), minlength=K + 1)[:K + 1]
    exp_p = np.array([pois_pmf(np.full(n, k), mup).sum() for k in ks])
    exp_nb = np.array([nb_pmf(np.full(n, k), mun, th).sum() for k in ks])
    exp_p = np.append(exp_p, n - exp_p.sum())
    exp_nb = np.append(exp_nb, n - exp_nb.sum())

    # binned mean-variance: groups of 50 observations by fitted mean
    order = np.argsort(mun)
    bins = []
    for g in np.array_split(order, 10):
        bins.append({"m": float(y[g].mean()), "v": float(y[g].var(ddof=1)), "mu_hat": float(mun[g].mean())})

    se_p = np.sqrt(np.diag(covp))
    se_n = np.sqrt(np.diag(nb["cov"]))

    def ci(b, s):
        return [float(b - Z975 * s), float(b + Z975 * s)]

    return {
        "n": n, "true": {"b0": b0, "b1": b1, "theta": theta},
        "y_mean": float(y.mean()), "y_var": float(y.var(ddof=1)), "y_max": int(y.max()), "zeros": int(np.sum(y == 0)),
        "pois": {"beta": bp.tolist(), "se": se_p.tolist(), "ll": ll_p, "aic": -2 * ll_p + 2 * p,
                 "pearson": pearson_p, "deviance": dev_p, "df": n - p, "phi": phi,
                 "se_quasi": (se_p * math.sqrt(phi)).tolist(),
                 "ci_b1": ci(bp[1], se_p[1]), "ci_b1_quasi": ci(bp[1], se_p[1] * math.sqrt(phi))},
        "nb": {"beta": nb["beta"].tolist(), "se": se_n.tolist(), "ll": nb["ll"], "aic": -2 * nb["ll"] + 2 * (p + 1),
               "theta": th, "theta_se": theta_se(y, mun, th), "pearson": pearson_nb, "deviance": dev_nb,
               "phi": pearson_nb / (n - p - 1), "ci_b1": ci(nb["beta"][1], se_n[1])},
        "lr": lr, "log10_p_lr": log10_p,
        "freq": {"k": ks.tolist(), "obs": obs.tolist(), "pois": [round(float(v), 2) for v in exp_p],
                 "nb": [round(float(v), 2) for v in exp_nb], "K": K},
        "mv_bins": bins,
    }


# ---------------------------------------------------------------- 3) coverage of the slope interval
def coverage() -> dict:
    n, M, b0, b1 = 200, 2000, 1.0, 0.5
    thetas = [None, 10.0, 2.0, 0.5]
    rng = np.random.default_rng(1979)
    rows = []
    for th in thetas:
        hit = {"pois": 0, "quasi": 0, "nb": 0}
        width = {"pois": 0.0, "quasi": 0.0, "nb": 0.0}
        b1s = {"pois": [], "nb": []}
        th_hat = []
        for _ in range(M):
            x = rng.normal(size=n)
            mu = np.exp(b0 + b1 * x)
            lam = mu if th is None else mu * rng.gamma(shape=th, scale=1 / th, size=n)
            y = rng.poisson(lam)
            X = np.column_stack([np.ones(n), x])
            lf = lfact(y)
            bp, mup, covp = irls(X, y, None)
            phi = float(np.sum((y - mup) ** 2 / mup)) / (n - 2)
            s_p = math.sqrt(covp[1, 1])
            nb = fit_nb(X, y, lf, bp)
            s_n = math.sqrt(nb["cov"][1, 1])
            for key, b, s in (("pois", bp[1], s_p), ("quasi", bp[1], s_p * math.sqrt(phi)), ("nb", nb["beta"][1], s_n)):
                hit[key] += abs(b - b1) <= Z975 * s
                width[key] += 2 * Z975 * s
            b1s["pois"].append(bp[1])
            b1s["nb"].append(nb["beta"][1])
            th_hat.append(nb["theta"])
        rows.append({
            "theta": th, "M": M,
            **{f"cov_{k}": hit[k] / M for k in hit},
            **{f"w_{k}": width[k] / M for k in width},
            "sd_b1_pois": float(np.std(b1s["pois"], ddof=1)), "sd_b1_nb": float(np.std(b1s["nb"], ddof=1)),
            "mean_b1_pois": float(np.mean(b1s["pois"])), "mean_b1_nb": float(np.mean(b1s["nb"])),
            "theta_hat_median": float(np.median(th_hat)),
        })
        print("theta", th, {k: round(v, 3) for k, v in rows[-1].items() if k.startswith(("cov", "sd", "mean", "theta_hat"))})
    return {"n": n, "M": M, "b0": b0, "b1": b1, "mc_se": math.sqrt(0.95 * 0.05 / M), "rows": rows}


def main() -> None:
    out = {"mixture": mixture()}
    print("mixture ok", out["mixture"]["mean_sim"], out["mixture"]["var_sim"], out["mixture"]["max_abs_err"])
    out["worked"] = worked()
    w = out["worked"]
    print("worked: phi", round(w["pois"]["phi"], 3), "theta", round(w["nb"]["theta"], 3), "lr", round(w["lr"], 1))
    out["coverage"] = coverage()
    (ROOT / "data" / "negbin.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print("wrote data/negbin.json")


if __name__ == "__main__":
    main()
