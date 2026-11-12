# Quasi-likelihood in GLMs

```bash
pip install numpy                     # tested with numpy 2.5
python research/quasi/quasi.py        # a few seconds; writes data/quasi.json
```

Computes every number in the note: a quasi-Poisson example (insect counts, 4 sprays x 12 plots, Var = 3 mu) with
the IRLS trace and the chi-square vs F test; a quasi-binomial example (germination, beta-binomial plates, no true
interaction); Wedderburn's variance mu^2 (1 - mu)^2 on simulated leaf-blotch-style proportions (10 varieties x
9 sites) against the binomial variance, with residuals by fitted value and extended quasi-likelihood; and four
simulation studies (M = 2,000 datasets each): coverage under Var = 3 mu with n = 50 and n = 12, a wrong vs right
variance function for continuous data, phi-hat for binary data, and the type I error of the germination test.
The models are fitted from scratch (IRLS, Pearson phi, quasi-deviance, sandwich), numpy only. Fixed seeds throughout.
