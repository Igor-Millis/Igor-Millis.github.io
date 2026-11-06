# Betting statistics — "Why the house wins"

```bash
python research/bets/bets.py     # standard library only; writes data/bets.json
```

Computes every number in the note: implied probabilities and overround of an illustrative 1X2 market,
exact binomial P(ahead) vs the CLT approximation, the crossover n* = (2σ/|μ|)², accumulator expected values,
gambler's-ruin probabilities, the Kelly growth curve, and 24 seeded law-of-large-numbers paths.
The in-browser simulator (`static/js/bets.js`) uses the same model with a seeded PRNG.
