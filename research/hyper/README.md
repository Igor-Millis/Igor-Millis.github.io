# Hyperparameters for statisticians

```bash
pip install numpy                       # tested with numpy 2.5
python research/hyper/hyper.py          # ~15 minutes; writes data/hyper.json
python research/hyper/hyper.py ridge    # recompute one part only (ridge | opt | ard)
```

Computes every number in the note: ridge regression (n = 50, p = 40, AR(1) predictors) with 10-fold CV, LOOCV,
GCV, AIC, AICc and the marginal likelihood compared over 1,000 datasets in two scenarios (fixed decaying
coefficients; coefficients drawn from the normal prior), with the true prediction risk known in closed form; kernel
ridge regression with three hyperparameters tuned by a 3x3x3 grid, random search, Bayesian optimisation (Matern-5/2
Gaussian process + expected improvement) and successive halving at the same budget, over 100 datasets; the same data
with six hyperparameters (one RBF width per input) over 40 datasets; and the winner's curse of picking the best of k
configurations. Everything is written from scratch in numpy. Fixed seeds throughout.
