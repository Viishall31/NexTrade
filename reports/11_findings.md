# Experiment 2 — rulebook findings (for the report)

Rules: `11_rulebook.md` · Frozen parameters: `11_rulebook_frozen.json` · Results: `11_rulebook_test.md` · Trades: `11_trades_*.csv`

## What changed from Experiment 1
- Uses the models' **probabilities**, not just the top regime: BUY on P(bull), SELL on P(bear)+P(high-vol).
- A **sideways** forecast never triggers a trade (Experiment 1 bought on sideways and whipsawed).
- Position size scales with conviction (50% / 100%).
- Wider default stop (8%), a 5-day cooldown, and a fresh-signal requirement after a stop.
- Designed **after** seeing Experiment 1's test results, so the whole experiment is post-hoc. Parameters were still
  chosen on validation only and the test year was traded once.

## Test year results (start Rs 10,00,000)
| Model | Default rules, ETF | Tuned rules, ETF | Tuned rules, futures (idealized) |
|---|---|---|---|
| LSTM | Rs 9,92,193 (−0.8%) | Rs 10,21,018 (+2.1%) | Rs 9,49,524 (−5.0%) |
| CNN-BiLSTM-Attention | Rs 10,04,727 (+0.5%) | Rs 10,06,074 (+0.6%) | Rs 10,25,999 (+2.6%) |
| Transformer | Rs 9,90,485 (−1.0%) | Rs 10,19,525 (+2.0%) | Rs 10,19,884 (+2.0%) |
| Buy & hold ETF | Rs 9,81,776 (−1.8%) | | |
| Cash at 6% | Rs 10,55,109 (+5.5%) | | |

- 6 of 9 versions ended above Rs 10 lakh; 8 of 9 beat buy & hold; **none beat cash at 6%**.
- Drawdowns are much smaller than buy & hold's (−6% to −11% vs −15.7%).

## The key caveat: the profit is interest, not trading
Split each result into interest on idle cash and trading P&L:

| Version | Profit | Cash interest | **Trading P&L** |
|---|---|---|---|
| LSTM, tuned ETF | +Rs 21,018 | Rs 35,416 | **−Rs 14,398** |
| CNN, tuned futures | +Rs 25,999 | Rs 53,867 | **−Rs 27,868** |
| Transformer, tuned ETF | +Rs 19,525 | Rs 34,192 | **−Rs 14,668** |

**Every one of the 9 versions has negative trading P&L.** The positive totals exist because the rules kept
money out of a falling market, where it earned 6%. Buy & hold's trading P&L was −Rs 18,169.

## Did the timing help? Compare with "just stay partly invested"
A portfolio with the same average share invested every day and no signals (approximate: it counts 50% positions as
fully invested):

| Version | Rulebook | Same % invested, no signals | Timing added |
|---|---|---|---|
| LSTM, default | Rs 9,92,193 | ~Rs 10,03,156 | ✗ |
| LSTM, tuned | Rs 10,21,018 | ~Rs 10,31,826 | ✗ |
| CNN, default | Rs 10,04,727 | ~Rs 9,98,503 | ✓ small |
| CNN, tuned | Rs 10,06,074 | ~Rs 9,82,177 | ✓ ~Rs 24k |
| Transformer, default | Rs 9,90,485 | ~Rs 10,21,254 | ✗ |
| Transformer, tuned | Rs 10,19,525 | ~Rs 10,30,292 | ✗ |

Only the CNN-BiLSTM-Attention's buy/sell timing beat simply holding less equity. It was also the best trader in
Experiment 1, while being the weakest classifier by macro-F1. This is consistent: the model that copies the lagging
HMM labels least closely trades best.

## Conclusion for the report
Probability-based rules turn Experiment 1's losses into small gains and cut drawdowns roughly in half. But the gains
come from reduced exposure plus interest on cash, not from profitable buy/sell timing. In May 2024 – Apr 2025, none
of the three models produced trading signals that beat a liquid fund, and only the CNN-BiLSTM-Attention's timing
beat a constant partial allocation.
