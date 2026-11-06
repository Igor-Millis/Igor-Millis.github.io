"""Extra analyses: reliability bins (saved model, test), bootstrap of ECE and of the F1-optimal threshold.
Usage: python -I calibration_extra.py <repo_dir> <in_json> <out_json>"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

repo = Path(sys.argv[1]).resolve()
res = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
sys.path.insert(0, str(repo))
from src.preprocessing import create_preprocessor  # noqa: E402

TARGET = "default payment next month"
df = pd.read_excel(repo / "data/raw/default_of_credit_card_clients.xls", header=1)
X, y = df.drop(columns=["ID", TARGET]), df[TARGET]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
X_mt, X_va, y_mt, y_va = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=42)
y_te, y_va = y_te.to_numpy(), y_va.to_numpy()

saved = joblib.load(repo / "models/xgboost_tuned_pipeline.pkl")
p_te = saved.predict_proba(X_te)[:, 1]

params = dict(colsample_bytree=0.8, learning_rate=0.05, max_depth=7, min_child_weight=5,
              n_estimators=100, reg_lambda=5, subsample=0.8)
m = Pipeline([("preprocessor", create_preprocessor()),
              ("classifier", XGBClassifier(**params, objective="binary:logistic", eval_metric="logloss",
                                           random_state=42, n_jobs=-1))]).fit(X_mt, y_mt)
p_va = m.predict_proba(X_va)[:, 1]

BINS = np.linspace(0, 1, 11)
TAUS = np.round(np.arange(0.05, 0.91, 0.01), 2)


def ece(p, yv):
    idx = np.clip(np.digitize(p, BINS[1:-1]), 0, 9)
    return sum((idx == b).sum() * abs(p[idx == b].mean() - yv[idx == b].mean()) for b in range(10) if (idx == b).any()) / len(p)


def f1_argmax(p, yv):
    f1s = np.array([f1_score(yv, (p >= t).astype(int)) for t in TAUS])
    return TAUS[int(np.argmax(f1s))], f1s


rng = np.random.default_rng(42)
B = 500
eces, taus, f1max = [], [], []
for _ in range(B):
    i = rng.integers(0, len(y_te), len(y_te))
    eces.append(ece(p_te[i], y_te[i]))
    j = rng.integers(0, len(y_va), len(y_va))
    t, f = f1_argmax(p_va[j], y_va[j])
    taus.append(t); f1max.append(f.max())
eces, taus, f1max = map(np.array, (eces, taus, f1max))

_, f1_val_curve = f1_argmax(p_va, y_va)
res["bootstrap"] = {
    "B": B,
    "ece_test_ci": [float(np.percentile(eces, 2.5)), float(np.percentile(eces, 97.5))],
    "tau_val_ci": [float(np.percentile(taus, 2.5)), float(np.percentile(taus, 97.5))],
    "tau_val_median": float(np.median(taus)),
    "f1max_val_ci": [float(np.percentile(f1max, 2.5)), float(np.percentile(f1max, 97.5))],
}
res["f1_val_curve"] = [[float(t), float(f)] for t, f in zip(TAUS, f1_val_curve)]
# expected cost at implied ratio for comparison (test, saved model)
Path(sys.argv[3]).write_text(json.dumps(res, indent=2), encoding="utf-8")

print("bootstrap:", res["bootstrap"])
print("F1 val at 0.20..0.30:", [(t, round(f, 4)) for t, f in res["f1_val_curve"] if 0.195 < t < 0.305])
print("reliability saved/test:")
for r in res["saved"]["reliability"]:
    print(f"  bin {r['bin']}: n={r['n']:5d} mean_p={r['mean_p']:.3f} obs={r['obs']:.3f}")
