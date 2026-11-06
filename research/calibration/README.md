# Calibration check — credit-default-api

Reproduces every number in the research note *Is τ = 0.24 really a cost ratio?*.

```bash
git clone https://github.com/Igor-Millis/credit-default-api
python -m venv .venv && .venv/Scripts/pip install scikit-learn==1.9.0 xgboost==3.3.0 pandas==3.0.3 numpy==2.4.6 joblib==1.5.3 xlrd==2.0.2
.venv/Scripts/python -I calibration.py credit-default-api calibration.json
.venv/Scripts/python -I calibration_bootstrap.py credit-default-api calibration.json ../../data/calibration.json
```

- `calibration.py` — reproduces the split of `notebooks/010_model_validation.ipynb`; evaluates the saved model on
  the test set; refits the same hyperparameters on the 19,200-row training split, fits Platt and isotonic
  calibrators on the 4,800-row validation split and evaluates everything on the 6,000-row test set.
- `calibration_bootstrap.py` — 500 bootstrap resamples: ECE on test and the F1-optimal threshold on validation.

Sanity check against the notebooks: the saved model gives test ROC AUC 0.7770; the refit gives validation
τ = 0.24, F1 = 0.5405, ROC AUC 0.7833 — identical to `010_model_validation.ipynb`.
