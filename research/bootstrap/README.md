# Bootstrap — non-parametric vs parametric

```bash
pip install numpy                       # tested with numpy 2.5
python research/bootstrap/bootstrap.py  # ~1 min; writes data/bootstrap.json
```

Computes every number in the note: the toy resamples, the worked example (15 waiting times generated from
Exp(mean 4); NP and P bootstrap distributions of the mean and the median with B = 10,000, against the true
sampling distribution from 100,000 fresh samples), the Monte Carlo error as a function of B, the coverage study
(M = 2,000 samples × B = 999 resamples; exponential and lognormal data, exponential model; seven 95% intervals
for the mean) and the Uniform(0, θ) maximum example. Every random quantity uses a fixed seed.
The in-browser demo (`static/js/bootstrap.js`) runs the same two algorithms with a seeded PRNG.
