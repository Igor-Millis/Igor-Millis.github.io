"""Numbers for the research note "Why the house wins" (statistics of fixed-odds betting).

Usage: python research/bets/bets.py            -> writes data/bets.json
Standard library only. Every random quantity uses a fixed seed.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Reference bet: decimal odds 1.91 on a true 50/50 event (a typical "even" market with margin).
ODDS, P = 1.91, 0.5
MU = P * ODDS - 1                                   # expected gain per unit staked
SIGMA = ODDS * math.sqrt(P * (1 - P))               # sd of the gain per unit staked


def log_binom_pmf(n: int, k: int, p: float) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log(1 - p)


def p_ahead_exact(n: int, odds: float = ODDS, p: float = P) -> float:
    """P(total profit > 0) after n unit bets: W wins with W*(odds-1) - (n-W) > 0  <=>  W > n/odds."""
    kmin = math.floor(n / odds) + 1
    return sum(math.exp(log_binom_pmf(n, k, p)) for k in range(kmin, n + 1))


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ruin_double(p: float, k: int, n_target: int) -> float:
    """Even-money unit bets (odds 2.0), win prob p: P(reach n_target before 0 starting at k)."""
    if abs(p - 0.5) < 1e-12:
        return k / n_target
    r = (1 - p) / p
    return (1 - r ** k) / (1 - r ** n_target)


def main() -> None:
    out: dict = {"odds": ODDS, "p": P, "mu": MU, "sigma": SIGMA}

    # 1) illustrative 1X2 market: implied probabilities and overround
    market = {"home": 2.10, "draw": 3.40, "away": 3.60}
    implied = {k: 1 / v for k, v in market.items()}
    s = sum(implied.values())
    out["market"] = {"odds": market, "implied": implied, "booksum": s, "overround": s - 1,
                     "fair_odds": {k: 1 / (v / s) for k, v in implied.items()},
                     "ev_if_fair": 1 / s - 1}

    # 2) P(ahead) after n bets: exact binomial vs CLT
    out["p_ahead"] = [{"n": n, "exact": p_ahead_exact(n), "clt": phi(MU * math.sqrt(n) / SIGMA),
                       "expected_loss": -MU * n, "two_sd": 2 * SIGMA * math.sqrt(n)}
                      for n in (1, 10, 50, 100, 500, 1000, 2000, 5000, 10000)]
    out["n_star"] = (2 * SIGMA / MU) ** 2           # where expected loss = 2 sd of luck

    # 3) parlays: k legs, each priced with the same overround
    m = out["market"]["overround"]
    out["parlay"] = [{"legs": k, "ev": (1 / (1 + m)) ** k - 1} for k in (1, 2, 3, 5, 8, 10)]

    # 4) gambler's ruin: start with 50 units, stop at 100 or 0, even-money bets
    out["ruin"] = [{"p": p, "edge": 2 * p - 1, "p_double": ruin_double(p, 50, 100)}
                   for p in (0.50, 0.495, 0.49, 0.48, 0.475, 0.45)]

    # 5) Kelly: growth rate g(f) for a bettor WITH a genuine edge (odds 2.10, true p = 0.52)
    b, pk = 1.10, 0.52
    f_star = (b * pk - (1 - pk)) / b
    out["kelly"] = {"b": b, "p": pk, "f_star": f_star,
                    "curve": [[f, pk * math.log(1 + b * f) + (1 - pk) * math.log(1 - f)]
                              for f in [i / 200 for i in range(0, 41)]]}

    # 6) law of large numbers: running mean return of 24 simulated bettors (seeded), log-spaced checkpoints
    rng = random.Random(2026)
    checkpoints = sorted({int(round(10 ** (e / 20))) for e in range(0, 81)})   # 1 .. 10,000
    cps = set(checkpoints)
    paths = []
    for _ in range(24):
        total, path = 0.0, []
        for i in range(1, 10001):
            total += (ODDS - 1) if rng.random() < P else -1
            if i in cps:
                path.append(round(total / i, 5))
        paths.append(path)
    out["lln"] = {"n": checkpoints, "paths": paths,
                  "band": [[n, MU - 2 * SIGMA / math.sqrt(n), MU + 2 * SIGMA / math.sqrt(n)] for n in checkpoints],
                  "final_mean": sum(p[-1] for p in paths) / len(paths)}
    path = [[checkpoints[-1], out["lln"]["final_mean"]]]

    (ROOT / "data" / "bets.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"mu={MU:.4f} sigma={SIGMA:.4f} n*={out['n_star']:.0f} overround={m:.4f} ev_fair={out['market']['ev_if_fair']:.4f}")
    for r in out["p_ahead"]:
        print(f"  n={r['n']:6d} exact={r['exact']:.6f} clt={r['clt']:.6f} loss={r['expected_loss']:.1f} 2sd={r['two_sd']:.1f}")
    print("parlay:", [(r["legs"], round(r["ev"], 4)) for r in out["parlay"]])
    print("ruin:", [(r["p"], round(r["p_double"], 4)) for r in out["ruin"]])
    print(f"kelly f*={f_star:.4f} g(f*)={pk*math.log(1+b*f_star)+(1-pk)*math.log(1-f_star):.5f}")
    print("lln last:", path[-3:])


if __name__ == "__main__":
    main()
