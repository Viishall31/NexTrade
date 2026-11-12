# Step 3 — HMM regime labelling: design decisions

Chart: `03_regimes.png` · Numbers: `03_hmm.json` · Model: `models/hmm_daily.pkl`

## Configuration
Gaussian HMM, 4 states, full covariance, 10 random restarts, n_iter 1000, tol 1e-4.
Fitted on the train split only (Feb 2016 – Dec 2021, 1,450 days), then frozen.

## Decision 1 — Filtered, not smoothed, posteriors
`hmmlearn.predict_proba` runs forward-backward, so a day's label depends on later days.
That label cannot be reproduced live. Labels here use the forward pass only,
p(state_t | observations up to t), so historical and live labels come from the same
procedure. Verified by `tests/test_hmm.py::test_labels_are_causal`.

## Decision 2 — Emissions: 20-day return instead of 1-day return (deviation from spec)
The spec's emissions were [1-day log return, 20-day realised vol]. With those, the HMM
separated days by volatility only, and the return-based names became meaningless:

| Emissions | Feb–Apr 2020 crash | H1 2022 correction | 2023 rally | Sep–Oct 2018 selloff |
|---|---|---|---|---|
| 1-day return, rv20 (spec) | 67% high_vol | **70% bull** | **80% sideways** | — |
| 5-day return, rv20 | 71% high_vol | 79% sideways | 76% bull | 46% sideways |
| 10-day return, rv20 | 73% high_vol | 74% sideways | 76% bull | 46% sideways |
| **20-day return, rv20 (chosen)** | **69% high_vol, 21% bear** | **65% bear** | **72% bull** | **46% bear** |
| 20-day return, rv60 | 47% bear | 66% bear | 100% sideways | 100% sideways |

## State → name mapping (train split)
high_vol = highest mean volatility; of the rest, highest mean 20-day return = bull,
lowest = bear, remaining = sideways.

| Regime | Mean 20d return | Mean ann. vol | Train days |
|---|---|---|---|
| bull | +2.4% | 9.3% | 609 |
| sideways | +1.2% | 13.8% | 503 |
| bear | +0.3% | 20.9% | 284 |
| high_vol | −8.6% | 55.6% | 54 |

## Known limitations (for the report)
- **"Bear" is relative.** The 2016–2021 training market mostly went up, so the bear state is
  "weak trend with elevated volatility" (mean 20-day return slightly positive), not a deep
  downtrend. Deep crashes fall into high_vol.
- **Labels lag turning points** by days to weeks (20-day window + causal filtering), e.g. bear
  labels persist into the May 2020 rebound.
- **BIC prefers k = 5 over 4** (2011 vs 2542; k = 3: 3446). k = 4 is kept because the project
  defines four regimes; the spec requires reporting this.
- **Class imbalance:** high_vol is 3.7% of train days and 1.9% of validation days, so
  class-weighted loss and macro-F1 (both already in the spec) matter.
