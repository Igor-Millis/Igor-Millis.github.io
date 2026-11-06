"""Calibration study for credit-default-api (XGBoost tuned).

Usage: python -I calibration.py <repo_dir> <out_json>
Reproduces the split of notebooks/010_model_validation.ipynb:
  train/test 80/20 stratified (rs=42), then train -> model_train/val 80/20 stratified (rs=42).
A) Saved model (trained on full train, 24k) evaluated on test.
B) Same hyperparameters refit on model_train (19.2k); calibrators fitted on val; evaluated on test.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

repo = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
sys.path.insert(0, str(repo))
from src.preprocessing import create_preprocessor  # noqa: E402

TARGET = "default payment next month"
df = pd.read_excel(repo / "data/raw/default_of_credit_card_clients.xls", header=1)
X, y = df.drop(columns=["ID", TARGET]), df[TARGET]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
X_mt, X_va, y_mt, y_va = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=42)
y_te, y_va = y_te.to_numpy(), y_va.to_numpy()

BINS = np.linspace(0, 1, 11)


def reliability(p, yv):
    idx = np.clip(np.digitize(p, BINS[1:-1]), 0, 9)
    rows = []
    for b in range(10):
        m = idx == b
        if m.sum() == 0:
            continue
        rows.append({"bin": b, "n": int(m.sum()), "mean_p": float(p[m].mean()), "obs": float(yv[m].mean())})
    return rows


def ece(p, yv):
    return float(sum(r["n"] * abs(r["mean_p"] - r["obs"]) for r in reliability(p, yv)) / len(p))


def summary(p, yv, tau):
    pred = (p >= tau).astype(int)
    return {
        "brier": float(brier_score_loss(yv, p)), "logloss": float(log_loss(yv, p)), "ece": ece(p, yv),
        "auc": float(roc_auc_score(yv, p)), "mean_p": float(p.mean()), "base_rate": float(yv.mean()),
        "f1_at_tau": float(f1_score(yv, pred)), "tau": tau,
    }


def f1_curve(p, yv):
    taus = np.round(np.arange(0.05, 0.91, 0.01), 2)
    f1s = [f1_score(yv, (p >= t).astype(int)) for t in taus]
    i = int(np.argmax(f1s))
    return float(taus[i]), float(f1s[i])


res = {}

# ---- A) saved model on test -----------------------------------------------------------
saved = joblib.load(repo / "models/xgboost_tuned_pipeline.pkl")
tau_saved = float(joblib.load(repo / "models/xgboost_tuned_threshold.pkl"))
p_saved = saved.predict_proba(X_te)[:, 1]
res["saved"] = summary(p_saved, y_te, round(tau_saved, 2))
res["saved"]["reliability"] = reliability(p_saved, y_te)
res["saved"]["recall_at_tau"] = float(((p_saved >= 0.24) & (y_te == 1)).sum() / (y_te == 1).sum())

# ---- B) refit on model_train, calibrate on val, evaluate on test ------------------------
params = dict(colsample_bytree=0.8, learning_rate=0.05, max_depth=7, min_child_weight=5,
              n_estimators=100, reg_lambda=5, subsample=0.8)
m = Pipeline([("preprocessor", create_preprocessor()),
              ("classifier", XGBClassifier(**params, objective="binary:logistic", eval_metric="logloss",
                                           random_state=42, n_jobs=-1))])
m.fit(X_mt, y_mt)
p_va, p_te = m.predict_proba(X_va)[:, 1], m.predict_proba(X_te)[:, 1]
tau_va, f1_va = f1_curve(p_va, y_va)
res["refit_check"] = {"tau_val": tau_va, "f1_val": f1_va, "auc_val": float(roc_auc_score(y_va, p_va))}

logit = lambda q: np.log(np.clip(q, 1e-6, 1 - 1e-6) / (1 - np.clip(q, 1e-6, 1 - 1e-6)))  # noqa: E731
platt = LogisticRegression(C=1e6).fit(logit(p_va).reshape(-1, 1), y_va)
iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p_va, y_va)
cal = {
    "raw": lambda q: q,
    "platt": lambda q: platt.predict_proba(logit(q).reshape(-1, 1))[:, 1],
    "isotonic": lambda q: iso.predict(q),
}
res["platt_coef"] = {"a": float(platt.coef_[0][0]), "b": float(platt.intercept_[0])}
for name, g in cal.items():
    pv, pt = g(p_va), g(p_te)
    t_star, f_star = f1_curve(pv, y_va)          # F1-optimal threshold chosen on validation
    s = summary(pt, y_te, t_star)
    s.update({"tau_f1_val": t_star, "f1_star_val": f_star, "reliability": reliability(pt, y_te),
              "g_of_024": float(g(np.array([0.24]))[0])})
    res[name] = s

out.write_text(json.dumps(res, indent=2), encoding="utf-8")
for k in ("saved", "raw", "platt", "isotonic"):
    r = res[k]
    print(f"{k:9s} brier={r['brier']:.4f} ll={r['logloss']:.4f} ece={r['ece']:.4f} auc={r['auc']:.4f} "
          f"mean_p={r['mean_p']:.4f} base={r['base_rate']:.4f} tau={r['tau']} f1={r['f1_at_tau']:.4f}"
          + (f" g(0.24)={r['g_of_024']:.4f} tauF1val={r['tau_f1_val']} F1*val={r['f1_star_val']:.4f}" if k != "saved" else ""))
print("refit:", res["refit_check"], "platt:", res["platt_coef"])
