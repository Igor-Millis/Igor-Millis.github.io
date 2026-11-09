# From Poisson to the negative binomial

```bash
pip install numpy                     # tested with numpy 2.5
python research/negbin/negbin.py      # ~1 min; writes data/negbin.json
```

Computes every number in the note: the Poisson–Gamma mixture simulated one million times (Z ~ Gamma(2, rate 0.5),
Y | Z ~ Poisson(Z)) against the closed-form negative binomial and a Poisson with the same mean; one worked dataset
(n = 500, log mu = 1 + 0.5 x, theta = 1.5) fitted by Poisson, quasi-Poisson and negative binomial GLMs, with
dispersion statistics, the boundary likelihood-ratio test and observed vs expected frequencies; and the coverage of
the 95% Wald interval for the slope (n = 200, M = 2,000 datasets per theta, theta = infinity, 10, 2, 0.5).
The GLMs are fitted from scratch (IRLS + profile maximum likelihood for theta), numpy only. Fixed seeds throughout.
