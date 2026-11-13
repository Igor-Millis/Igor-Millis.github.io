"""Numbers for the research note "Hyperparameters for statisticians".

Usage: python research/hyper/hyper.py [ridge|opt|ard ...]   -> writes data/hyper.json (all parts by default)
Needs numpy only (tested with 2.5). Every random quantity uses a fixed seed, so the output is reproducible.

Sections (match the note):
  ridge   - ridge regression, n = 50, p = 40, AR(1) predictors (rho = 0.6), sigma = 1 (R^2 about 0.66), no intercept.
            One dataset: training MSE, true prediction error, 10-fold CV, LOOCV, GCV, AIC and the marginal
            likelihood (empirical Bayes) as functions of lambda. Then M = 1,000 datasets: the lambda each criterion
            picks and its excess risk relative to the oracle lambda
  opt     - kernel ridge regression with 3 hyperparameters (log10 lambda, log10 gamma, linear-kernel weight a),
            n_train = 324, n_val = 200, n_test = 5,000, d = 5. R = 100 replications of four optimisers at the same
            budget of 27 full fits: grid 3x3x3, random search, Bayesian optimisation (GP + expected improvement) and
            successive halving (81 configs on 36 points -> 27 on 108 -> 9 on 324, same number of training points used)
  curse   - winner's curse: validation error of the best of k random configurations vs its test error
  import  - how much of the variation in validation error each hyperparameter explains (main effects)
  ard     - the same data with one RBF bandwidth per input (6 hyperparameters; x5 is pure noise, x4 enters linearly),
            budget 64: grid 2^6, random search, Bayesian optimisation. R = 40 replications
  surface - validation-error surface over (log lambda, log gamma) at a = 0 for one replication, with the points each
            optimiser evaluated

The models and the optimisers are written from scratch so every formula in the note can be read here.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261113
_erf = np.frompyfunc(math.erf, 1, 1)


def ncdf(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + _erf(np.asarray(z) / math.sqrt(2.0)).astype(float))


def npdf(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z ** 2) / math.sqrt(2 * math.pi)


# =============================================================== part 1: ridge regression
N_R, P_R, RHO, SIG = 50, 40, 0.6, 1.0
LAMS = np.logspace(-1, 5, 121)
SIGMA = RHO ** np.abs(np.subtract.outer(np.arange(P_R), np.arange(P_R)))
CHOL = np.linalg.cholesky(SIGMA)
BETA = np.array([(1.2 if j % 2 == 0 else -1.2) * 0.88 ** j for j in range(P_R)])


def ridge_paths(X: np.ndarray, y: np.ndarray, beta: np.ndarray = BETA) -> dict:
    """All criteria on the lambda grid for one dataset."""
    n = len(y)
    U, d, Vt = np.linalg.svd(X, full_matrices=False)
    uy = U.T @ y
    shrink = d[None, :] ** 2 / (d[None, :] ** 2 + LAMS[:, None])          # (L, p)
    B = (shrink / d[None, :] * uy[None, :]) @ Vt                            # (L, p) coefficient paths
    fit = (shrink * uy[None, :]) @ U.T                                      # (L, n)
    res = y[None, :] - fit
    rss = (res ** 2).sum(1)
    df = shrink.sum(1)
    h = (U ** 2) @ shrink.T                                                 # (n, L) leverages
    loo = ((res.T / (1 - h)) ** 2).mean(0)
    gcv = n * rss / (n - df) ** 2
    aic = n * np.log(rss / n) + 2 * df
    aicc = n * np.log(rss / n) + n * (1 + 2 * (df + 1) / np.maximum(n - df - 2, 1e-9))   # Hurvich, Simonoff & Tsai (1998)
    # marginal likelihood: y ~ N(0, s2 (I + X X'/lam)), s2 profiled out
    out_ss = y @ y - uy @ uy
    q = (uy[None, :] ** 2 / (1 + d[None, :] ** 2 / LAMS[:, None])).sum(1) + out_ss
    logdet = np.log1p(d[None, :] ** 2 / LAMS[:, None]).sum(1)
    nml = n * np.log(q / n) + logdet                                        # -2 log L up to a constant
    # 10-fold CV
    folds = np.arange(n) % 10
    cv = np.zeros(len(LAMS))
    for k in range(10):
        tr, te = folds != k, folds == k
        Uk, dk, Vk = np.linalg.svd(X[tr], full_matrices=False)
        sk = dk[None, :] / (dk[None, :] ** 2 + LAMS[:, None])
        Bk = (sk * (Uk.T @ y[tr])[None, :]) @ Vk
        cv += ((y[te][None, :] - Bk @ X[te].T) ** 2).sum(1)
    cv /= n
    diff = B - beta[None, :]
    pe = SIG ** 2 + np.einsum("lj,jk,lk->l", diff, SIGMA, diff)
    return {"train": rss / n, "pe": pe, "cv10": cv, "loo": loo, "gcv": gcv, "aic": aic, "aicc": aicc, "ml": nml, "df": df}


TAU = math.sqrt(BETA @ SIGMA @ BETA / np.trace(SIGMA))     # prior sd giving the same expected signal variance


def ridge_data(rng: np.random.Generator, prior: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    beta = TAU * rng.standard_normal(P_R) if prior else BETA
    X = rng.standard_normal((N_R, P_R)) @ CHOL.T
    y = X @ beta + SIG * rng.standard_normal(N_R)
    return X, y, beta


CRIT = ["cv10", "loo", "gcv", "aic", "aicc", "ml"]


def ridge_sim(prior: bool, M: int = 1000) -> tuple[dict, list]:
    picks = {c: [] for c in CRIT + ["pe"]}
    ratio = {c: [] for c in CRIT}
    for i in range(M):
        X, y, beta = ridge_data(np.random.default_rng([SEED, int(prior), i]), prior)
        P = ridge_paths(X, y, beta)
        io = int(np.argmin(P["pe"]))
        picks["pe"].append(np.log10(LAMS[io]))
        best = P["pe"][io] - SIG ** 2
        for c in CRIT:
            j = int(np.argmin(P[c]))
            picks[c].append(np.log10(LAMS[j]))
            ratio[c].append((P["pe"][j] - SIG ** 2) / best)
    summ = {}
    for c in CRIT + ["pe"]:
        a = np.array(picks[c])
        s = {"med": float(np.median(a)), "q1": float(np.quantile(a, .25)), "q3": float(np.quantile(a, .75)),
             "sd": float(a.std(ddof=1)), "edge": float(np.isin(a, np.log10(LAMS[[0, -1]])).mean())}
        if c != "pe":
            r = np.array(ratio[c])
            s.update({"r_med": float(np.median(r)), "r_mean": float(r.mean()), "r_q90": float(np.quantile(r, .9)),
                      "p_within10": float((r <= 1.1).mean()),
                      "corr_oracle": float(np.corrcoef(a, picks["pe"])[0, 1])})
        summ[c] = s
    return summ, np.abs(np.array(picks["cv10"]) - np.array(picks["pe"])).tolist()


def part_ridge() -> dict:
    summ, miss = ridge_sim(False)
    summ_prior, _ = ridge_sim(True)
    # illustration: the replication whose 10-fold miss |log lambda_cv - log lambda_opt| is the median one
    i = int(np.argsort(miss)[len(miss) // 2])
    X, y, beta = ridge_data(np.random.default_rng([SEED, 0, i]))
    P = ridge_paths(X, y)
    ols = np.linalg.lstsq(X, y, rcond=None)[0]
    one = {"rep": i, "loglam": np.log10(LAMS).round(3).tolist(),
           **{k: np.round(P[k], 5).tolist() for k in ("train", "pe", "cv10", "gcv", "df")},
           "pick": {c: float(np.log10(LAMS[np.argmin(P[c])])) for c in CRIT + ["pe"]},
           "pe_ols": float(SIG ** 2 + (ols - BETA) @ SIGMA @ (ols - BETA)), "pe_min": float(P["pe"].min()),
           "pe_null": float(SIG ** 2 + BETA @ SIGMA @ BETA)}
    return {"n": N_R, "p": P_R, "rho": RHO, "sigma": SIG, "tau": TAU, "signal_var": float(BETA @ SIGMA @ BETA),
            "M": 1000, "one": one, "summary": summ, "summary_prior": summ_prior}


# =============================================================== part 2: kernel ridge, 3 hyperparameters
D, NTR, NVA, NTE, NOISE = 5, 324, 200, 5000, 0.5
BOX = np.array([[-5.0, 1.0], [-3.0, 1.0], [0.0, 1.0]])     # log10 lambda, log10 gamma, a


def f_true(X: np.ndarray) -> np.ndarray:
    return np.sin(1.5 * X[:, 0]) + 0.5 * X[:, 1] * X[:, 2] + 0.6 * X[:, 3]


def to_theta(u: np.ndarray) -> np.ndarray:
    return BOX[:, 0] + np.asarray(u) * (BOX[:, 1] - BOX[:, 0])


class Problem:
    def __init__(self, rng: np.random.Generator):
        self.Xtr = rng.standard_normal((NTR, D))
        self.Xva = rng.standard_normal((NVA, D))
        self.Xte = rng.standard_normal((NTE, D))
        self.ytr = f_true(self.Xtr) + NOISE * rng.standard_normal(NTR)
        self.yva = f_true(self.Xva) + NOISE * rng.standard_normal(NVA)
        self.yte = f_true(self.Xte) + NOISE * rng.standard_normal(NTE)
        sq = lambda A, B: (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T   # noqa: E731
        self.D_tt, self.D_vt, self.D_et = sq(self.Xtr, self.Xtr), sq(self.Xva, self.Xtr), sq(self.Xte, self.Xtr)
        self.L_tt, self.L_vt, self.L_et = self.Xtr @ self.Xtr.T / D, self.Xva @ self.Xtr.T / D, self.Xte @ self.Xtr.T / D
        self.order = rng.permutation(NTR)       # nested subsets for successive halving
        self.cache: dict = {}

    def _fit(self, th: np.ndarray, m: int) -> tuple[np.ndarray, np.ndarray]:
        lam, gam, a = 10 ** th[0], 10 ** th[1], th[2]
        idx = self.order[:m]
        K = (1 - a) * np.exp(-gam * self.D_tt[np.ix_(idx, idx)]) + a * self.L_tt[np.ix_(idx, idx)]
        mu = self.ytr[idx].mean()
        c = np.linalg.solve(K + lam * np.eye(m), self.ytr[idx] - mu)
        return c, idx

    def _pred(self, th, c, idx, Dx, Lx):
        gam, a = 10 ** th[1], th[2]
        return ((1 - a) * np.exp(-gam * Dx[:, idx]) + a * Lx[:, idx]) @ c + self.ytr[idx].mean()

    def val(self, u: np.ndarray, m: int = NTR) -> float:
        th = to_theta(u)
        c, idx = self._fit(th, m)
        return float(((self.yva - self._pred(th, c, idx, self.D_vt, self.L_vt)) ** 2).mean())

    def test(self, u: np.ndarray) -> float:
        th = to_theta(u)
        c, idx = self._fit(th, NTR)
        return float(((self.yte - self._pred(th, c, idx, self.D_et, self.L_et)) ** 2).mean())


# ---------------------------------------------------------------- optimisers (all minimise validation MSE)
BUDGET = 27


def opt_grid(pb: Problem, rng) -> list:
    g = np.array([1 / 6, 1 / 2, 5 / 6])
    U = np.array(np.meshgrid(g, g, g, indexing="ij")).reshape(3, -1).T
    return [(u, pb.val(u)) for u in U]


def opt_random(pb: Problem, rng, k: int = BUDGET) -> list:
    return [(u, pb.val(u)) for u in rng.random((k, 3))]


def _matern(A: np.ndarray, B: np.ndarray, ell: np.ndarray) -> np.ndarray:
    r = np.sqrt((((A[:, None, :] - B[None, :, :]) / ell) ** 2).sum(-1))
    s = math.sqrt(5) * r
    return (1 + s + s ** 2 / 3) * np.exp(-s)


def _gp_fit(U: np.ndarray, z: np.ndarray, rng) -> tuple:
    """Matern-5/2 ARD GP on standardised z; length scales by maximising the marginal likelihood over candidates."""
    mz, sz = z.mean(), z.std() + 1e-12
    zs = (z - mz) / sz
    cands = 10 ** rng.uniform(-1.3, 0.4, size=(150, 3))
    best = None
    for ell in cands:
        K = _matern(U, U, ell) + 1e-4 * np.eye(len(U))
        try:
            Lc = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            continue
        al = np.linalg.solve(Lc.T, np.linalg.solve(Lc, zs))
        ll = -0.5 * zs @ al - np.log(np.diag(Lc)).sum()
        if best is None or ll > best[0]:
            best = (ll, ell, Lc, al)
    return best[1], best[2], best[3], mz, sz


def opt_bo(pb: Problem, rng, n0: int = 5) -> list:
    hist = [(u, pb.val(u)) for u in rng.random((n0, 3))]
    while len(hist) < BUDGET:
        U = np.array([h[0] for h in hist])
        z = np.log(np.array([h[1] for h in hist]))
        ell, Lc, al, mz, sz = _gp_fit(U, z, rng)
        ub = U[np.argmin(z)]
        C = np.vstack([rng.random((3000, 3)), np.clip(ub + 0.05 * rng.standard_normal((500, 3)), 0, 1)])
        Ks = _matern(C, U, ell)
        m = Ks @ al
        v = np.linalg.solve(Lc, Ks.T)
        s = np.sqrt(np.maximum(1 - (v ** 2).sum(0), 1e-12))
        fbest = (z.min() - mz) / sz
        g = (fbest - m) / s
        ei = s * (g * ncdf(g) + npdf(g))
        u = C[int(np.argmax(ei))]
        hist.append((u, pb.val(u)))
    return hist


def opt_sh(pb: Problem, rng) -> list:
    """Successive halving, eta = 3: 81 configs on 36 points, best 27 on 108, best 9 on 324 (= 27 full fits)."""
    U = rng.random((81, 3))
    rungs = []
    for m, keep in ((36, 27), (108, 9), (324, None)):
        sc = np.array([pb.val(u, m) for u in U])
        rungs.append((U.copy(), sc, m))
        if keep:
            U = U[np.argsort(sc)[:keep]]
    U, sc, _ = rungs[-1]
    return [(u, s) for u, s in zip(U, sc)], rungs


def part_opt() -> dict:
    rng = np.random.default_rng(SEED + 1)
    R = 100
    methods = ["grid", "random", "bo", "sh"]
    test = {m: [] for m in methods}
    valsel = {m: [] for m in methods}
    curves = {m: [] for m in ("random", "bo")}
    curse = {k: {"val": [], "test": []} for k in (1, 3, 9, 27, 81, 243)}
    imp_U, imp_v = [], []
    surface = None
    oracle = []
    for r in range(R):
        pb = Problem(rng)
        oracle.append(float(((pb.yte - f_true(pb.Xte)) ** 2).mean()))
        res = {"grid": opt_grid(pb, rng), "random": opt_random(pb, rng), "bo": opt_bo(pb, rng)}
        sh_hist, rungs = opt_sh(pb, rng)
        res["sh"] = sh_hist
        for m in methods:
            u, v = min(res[m], key=lambda t: t[1])
            valsel[m].append(v)
            test[m].append(pb.test(u))
        for m in ("random", "bo"):
            curves[m].append(np.minimum.accumulate([h[1] for h in res[m]]))
        # winner's curse with nested random searches of growing size
        big = opt_random(pb, rng, 243)
        for k in curse:
            u, v = min(big[:k], key=lambda t: t[1])
            curse[k]["val"].append(v)
            curse[k]["test"].append(pb.test(u))
        if r < 20:
            for u, v in big:
                imp_U.append(u); imp_v.append(math.log(v))
        if r == 0:
            n = 31
            gl = np.linspace(0, 1, n)
            Z = [[math.log10(pb.val(np.array([a, b, 0.0]))) for a in gl] for b in gl]
            surface = {"n": n, "z": np.round(Z, 4).tolist(),
                       "grid": [h[0].tolist() for h in res["grid"]],
                       "random": [h[0].tolist() for h in res["random"]],
                       "bo": [h[0].tolist() for h in res["bo"]],
                       "best": {m: min(res[m], key=lambda t: t[1])[0].tolist() for m in methods},
                       "sh_rungs": [len(x[0]) for x in rungs]}
    test = {m: np.array(v) for m, v in test.items()}
    bayes = float(np.mean(oracle))
    summ = {}
    for m in methods:
        t = test[m]
        summ[m] = {"test_med": float(np.median(t)), "test_mean": float(t.mean()), "test_q1": float(np.quantile(t, .25)),
                   "test_q3": float(np.quantile(t, .75)), "test_q90": float(np.quantile(t, .9)),
                   "val_mean": float(np.mean(valsel[m])),
                   "win_vs_random": float((t < test["random"]).mean()) if m != "random" else None}
    # Bergstra: distinct values of each hyperparameter visited
    curves_out = {m: {"med": np.median(np.array(c), 0).round(5).tolist(),
                      "q1": np.quantile(np.array(c), .25, 0).round(5).tolist(),
                      "q3": np.quantile(np.array(c), .75, 0).round(5).tolist()} for m, c in curves.items()}
    curse_out = []
    for k, d in curse.items():
        v, t = np.array(d["val"]), np.array(d["test"])
        curse_out.append({"k": k, "val": float(v.mean()), "test": float(t.mean()), "gap": float((t - v).mean()),
                          "gap_se": float((t - v).std(ddof=1) / math.sqrt(len(v)))})
    # main-effect importance: share of variance of log val error explained by binned means of each coordinate
    U, v = np.array(imp_U), np.array(imp_v)
    tot = v.var()
    imp = {}
    for j, name in enumerate(("lam", "gam", "a")):
        bins = np.minimum((U[:, j] * 10).astype(int), 9)
        means = np.array([v[bins == b].mean() for b in range(10)])
        imp[name] = float(((means[bins] - v.mean()) ** 2).mean() / tot)
    return {"R": R, "budget": BUDGET, "d": D, "n_train": NTR, "n_val": NVA, "n_test": NTE, "noise": NOISE,
            "box": BOX.tolist(), "bayes": bayes, "summary": summ, "curves": curves_out, "curse": curse_out,
            "importance": imp, "surface": surface,
            "bo_beats_random_med": float(np.median(test["random"] - test["bo"]))}


# =============================================================== part 3: six hyperparameters, two of them nearly useless
class ProblemARD(Problem):
    """Same data; RBF kernel with one bandwidth per input: exp(-sum_j g_j (x_j - x'_j)^2). u = (log lambda, log g_1..g_5)."""

    def __init__(self, rng):
        super().__init__(rng)
        sqj = lambda A, B: (A[:, None, :] - B[None, :, :]) ** 2          # noqa: E731
        self.Dj_tt, self.Dj_vt, self.Dj_et = sqj(self.Xtr, self.Xtr), sqj(self.Xva, self.Xtr), sqj(self.Xte, self.Xtr)

    @staticmethod
    def th(u):
        return np.concatenate([[-5 + 6 * u[0]], -3 + 4 * np.asarray(u[1:])])

    def _err(self, u, Dx, y):
        th = self.th(u)
        g = 10 ** th[1:]
        c = np.linalg.solve(np.exp(-self.Dj_tt @ g) + 10 ** th[0] * np.eye(NTR), self.ytr - self.ytr.mean())
        return float(((y - np.exp(-Dx @ g) @ c - self.ytr.mean()) ** 2).mean())

    def val(self, u, m=NTR):
        return self._err(u, self.Dj_vt, self.yva)

    def test(self, u):
        return self._err(u, self.Dj_et, self.yte)


def part_ard() -> dict:
    global BUDGET
    rng = np.random.default_rng(SEED + 2)
    R, B = 40, 64
    old, BUDGET = BUDGET, B
    test = {m: [] for m in ("grid", "random", "bo")}
    val = {m: [] for m in test}
    curves = {m: [] for m in ("random", "bo")}
    best_g = []
    for _ in range(R):
        pb = ProblemARD(rng)
        g = np.array([1 / 4, 3 / 4])
        G = np.array(np.meshgrid(*([g] * 6), indexing="ij")).reshape(6, -1).T
        res = {"grid": [(u, pb.val(u)) for u in G],
               "random": [(u, pb.val(u)) for u in rng.random((B, 6))]}
        res["bo"] = _bo_d(pb, rng, 6, B, 8)
        for m in test:
            u, v = min(res[m], key=lambda t: t[1])
            val[m].append(v); test[m].append(pb.test(u))
            if m == "bo":
                best_g.append(pb.th(u)[1:].tolist())
        for m in curves:
            curves[m].append(np.minimum.accumulate([h[1] for h in res[m]]))
    BUDGET = old
    t = {m: np.array(v) for m, v in test.items()}
    return {"R": R, "budget": B,
            "summary": {m: {"test_med": float(np.median(t[m])), "test_mean": float(t[m].mean()),
                            "test_q1": float(np.quantile(t[m], .25)), "test_q3": float(np.quantile(t[m], .75)),
                            "val_mean": float(np.mean(val[m])),
                            "win_vs_random": float((t[m] < t["random"]).mean()) if m != "random" else None} for m in t},
            "curves": {m: np.median(np.array(c), 0).round(5).tolist() for m, c in curves.items()},
            "bo_log_gamma_med": np.median(np.array(best_g), 0).round(2).tolist()}


def _bo_d(pb, rng, dim, budget, n0):
    hist = [(u, pb.val(u)) for u in rng.random((n0, dim))]
    while len(hist) < budget:
        U = np.array([h[0] for h in hist])
        z = np.log(np.array([h[1] for h in hist]))
        mz, sz = z.mean(), z.std() + 1e-12
        zs = (z - mz) / sz
        best = None
        for ell in 10 ** rng.uniform(-1.0, 0.7, size=(80, dim)):
            try:
                Lc = np.linalg.cholesky(_matern(U, U, ell) + 1e-4 * np.eye(len(U)))
            except np.linalg.LinAlgError:
                continue
            al = np.linalg.solve(Lc.T, np.linalg.solve(Lc, zs))
            ll = -0.5 * zs @ al - np.log(np.diag(Lc)).sum()
            if best is None or ll > best[0]:
                best = (ll, ell, Lc, al)
        _, ell, Lc, al = best
        ub = U[np.argmin(z)]
        C = np.vstack([rng.random((3000, dim)), np.clip(ub + 0.05 * rng.standard_normal((1000, dim)), 0, 1)])
        Ks = _matern(C, U, ell)
        m = Ks @ al
        s = np.sqrt(np.maximum(1 - (np.linalg.solve(Lc, Ks.T) ** 2).sum(0), 1e-12))
        gz = (zs.min() - m) / s
        u = C[int(np.argmax(s * (gz * ncdf(gz) + npdf(gz))))]
        hist.append((u, pb.val(u)))
    return hist


def main() -> None:
    import sys
    p = ROOT / "data" / "hyper.json"
    out = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    parts = sys.argv[1:] or ["ridge", "opt", "ard"]
    for name in parts:
        out[name] = {"ridge": part_ridge, "opt": part_opt, "ard": part_ard}[name]()
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    if "ard" in out:
        print("ard:", out["ard"]["summary"], out["ard"]["bo_log_gamma_med"])
    r, o = out["ridge"]["summary"], out["opt"]
    print("ridge:", {k: (round(v["med"], 2), round(v.get("r_med", 0), 3), round(v.get("r_mean", 0), 3)) for k, v in r.items()})
    print("opt:", {k: (round(v["test_med"], 4), round(v["test_mean"], 4), v["win_vs_random"]) for k, v in o["summary"].items()})
    print("bayes", round(o["bayes"], 4), "importance", o["importance"])
    print("curse", [(c["k"], round(c["val"], 4), round(c["test"], 4), round(c["gap"], 4)) for c in o["curse"]])
    print("one-dataset picks", out["ridge"]["one"]["pick"])


if __name__ == "__main__":
    main()
