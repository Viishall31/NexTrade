# Experiment 2 — rulebook trading on the test year (2024-04-30 → 2025-04-07)

Rules: `11_rulebook.md` (frozen on validation). Start **Rs 1,000,000** for every model and version.

| Model | Version | Parameters | Validation final | **Test: amount left** | **Profit / loss** | of which cash interest | Trading P&L (excl. interest) | Max DD | Trades | Costs | Invested |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LSTM | Default rules, ETF | `buy0.6|sell0.5|confirm2|scaled|stop8|cool5|cash` | Rs 1,193,783 | **Rs 992,193** | **Rs -7,807 (-0.8%)** | Rs 26,542 | Rs -34,348 | -10.2% | 7 | Rs 4,617 | 73% |
| LSTM | Tuned rules, ETF | `buy0.7|sell0.6|confirm2|full|stop5|cool5|cash` | Rs 1,249,577 | **Rs 1,021,018** | **Rs 21,018 (+2.1%)** | Rs 35,416 | Rs -14,398 | -7.2% | 4 | Rs 3,987 | 34% |
| LSTM | Tuned rules, futures (idealized) | `buy0.6|sell0.4|confirm2|scaled|stop5|cool5|short` | Rs 1,316,539 | **Rs 949,524** | **Rs -50,476 (-5.0%)** | Rs 51,681 | Rs -102,156 | -11.0% | 8 | Rs 5,112 | 44% |
| CNN-BiLSTM-Attention | Default rules, ETF | `buy0.6|sell0.5|confirm2|scaled|stop8|cool5|cash` | Rs 1,216,482 | **Rs 1,004,727** | **Rs 4,727 (+0.5%)** | Rs 27,023 | Rs -22,296 | -8.3% | 9 | Rs 5,058 | 79% |
| CNN-BiLSTM-Attention | Tuned rules, ETF | `buy0.5|sell0.6|confirm2|scaled|nostop|cool0|cash` | Rs 1,280,481 | **Rs 1,006,074** | **Rs 6,074 (+0.6%)** | Rs 20,873 | Rs -14,798 | -9.0% | 8 | Rs 4,602 | 100% |
| CNN-BiLSTM-Attention | Tuned rules, futures (idealized) | `buy0.5|sell0.6|confirm3|scaled|stop5|cool0|short` | Rs 1,419,424 | **Rs 1,025,999** | **Rs 25,999 (+2.6%)** | Rs 53,867 | Rs -27,868 | -6.0% | 9 | Rs 3,901 | 36% |
| Transformer | Default rules, ETF | `buy0.6|sell0.5|confirm2|scaled|stop8|cool5|cash` | Rs 1,204,772 | **Rs 990,485** | **Rs -9,515 (-1.0%)** | Rs 32,109 | Rs -41,624 | -7.6% | 10 | Rs 5,987 | 49% |
| Transformer | Tuned rules, ETF | `buy0.5|sell0.5|confirm2|full|stop5|cool5|cash` | Rs 1,247,213 | **Rs 1,019,525** | **Rs 19,525 (+2.0%)** | Rs 34,192 | Rs -14,668 | -6.6% | 4 | Rs 3,969 | 36% |
| Transformer | Tuned rules, futures (idealized) | `buy0.6|sell0.6|confirm3|scaled|nostop|cool5|short` | Rs 1,298,208 | **Rs 1,019,884** | **Rs 19,884 (+2.0%)** | Rs 53,761 | Rs -33,877 | -7.4% | 11 | Rs 4,809 | 55% |
| *Buy & hold ETF* | | | | Rs 981,776 | Rs -18,224 (-1.8%) | Rs -55 | Rs -18,169 | -15.7% | 1 | Rs 1,000 | 100% |
| *Cash at 6%* | | | | Rs 1,055,109 | Rs 55,109 (+5.5%) | Rs 55,109 | Rs 0 | 0.0% | 0 | – | 0% |

## Verdict

- Ended with a profit (above Rs 1,000,000): LSTM (Tuned rules, ETF), CNN-BiLSTM-Attention (Default rules, ETF), CNN-BiLSTM-Attention (Tuned rules, ETF), CNN-BiLSTM-Attention (Tuned rules, futures (idealized)), Transformer (Tuned rules, ETF), Transformer (Tuned rules, futures (idealized))
- Beat buy & hold (Rs 981,776): LSTM (Default rules, ETF), LSTM (Tuned rules, ETF), CNN-BiLSTM-Attention (Default rules, ETF), CNN-BiLSTM-Attention (Tuned rules, ETF), CNN-BiLSTM-Attention (Tuned rules, futures (idealized)), Transformer (Default rules, ETF), Transformer (Tuned rules, ETF), Transformer (Tuned rules, futures (idealized))
- Beat cash at 6% (Rs 1,055,109): none

## Trade log — LSTM, default rules (ETF)

| Date | Action | Nifty | Why | Portfolio before |
|---|---|---|---|---|
| 2024-05-02 | BUY 50% | 22,648 | P(bull) = 0.75 >= 0.6 for 2 day(s) | Rs 1,000,231 |
| 2024-05-24 | ADD to 100% | 22,956 | P(bull) = 0.82 rose to >= 0.75 | Rs 1,008,275 |
| 2024-06-12 | SELL | 23,315 | P(bear)+P(high_vol) = 0.63 >= 0.5 for 2 day(s) | Rs 1,023,551 |
| 2024-07-11 | BUY 100% | 24,336 | P(bull) = 0.75 >= 0.6 for 2 day(s) | Rs 1,027,251 |
| 2024-10-07 | REDUCE to 50% | 24,802 | P(bull) = 0.72 fell below 0.75 | Rs 1,045,870 |
| 2025-01-27 | STOP-LOSS | 22,826 | portfolio 8% below its peak since entry | Rs 1,012,944 |
| 2025-03-27 | BUY 50% | 23,603 | P(bull) = 0.65 >= 0.6 for 2 day(s) | Rs 1,022,327 |

## Trade log — CNN-BiLSTM-Attention, default rules (ETF)

| Date | Action | Nifty | Why | Portfolio before |
|---|---|---|---|---|
| 2024-05-02 | BUY 100% | 22,648 | P(bull) = 0.90 >= 0.6 for 2 day(s) | Rs 1,000,231 |
| 2024-05-10 | REDUCE to 50% | 22,054 | P(bull) = 0.71 fell below 0.75 | Rs 973,011 |
| 2024-05-21 | ADD to 100% | 22,516 | P(bull) = 0.78 rose to >= 0.75 | Rs 983,357 |
| 2024-06-05 | REDUCE to 50% | 22,601 | P(bull) = 0.72 fell below 0.75 | Rs 986,590 |
| 2024-07-11 | ADD to 100% | 24,336 | P(bull) = 0.75 rose to >= 0.75 | Rs 1,026,807 |
| 2024-08-07 | REDUCE to 50% | 24,309 | P(bull) = 0.64 fell below 0.75 | Rs 1,025,194 |
| 2024-09-13 | ADD to 100% | 25,351 | P(bull) = 0.79 rose to >= 0.75 | Rs 1,049,727 |
| 2024-10-07 | REDUCE to 50% | 24,802 | P(bull) = 0.70 fell below 0.75 | Rs 1,026,440 |
| 2025-01-27 | STOP-LOSS | 22,826 | portfolio 8% below its peak since entry | Rs 994,125 |

## Trade log — Transformer, default rules (ETF)

| Date | Action | Nifty | Why | Portfolio before |
|---|---|---|---|---|
| 2024-05-02 | BUY 100% | 22,648 | P(bull) = 0.95 >= 0.6 for 2 day(s) | Rs 1,000,231 |
| 2024-05-08 | REDUCE to 50% | 22,305 | P(bull) = 0.66 fell below 0.75 | Rs 984,076 |
| 2024-05-22 | ADD to 100% | 22,611 | P(bull) = 0.79 rose to >= 0.75 | Rs 991,336 |
| 2024-05-29 | REDUCE to 50% | 22,706 | P(bull) = 0.75 fell below 0.75 | Rs 995,024 |
| 2024-06-03 | ADD to 100% | 23,286 | P(bull) = 0.76 rose to >= 0.75 | Rs 1,007,566 |
| 2024-06-05 | SELL | 22,601 | P(bear)+P(high_vol) = 0.72 >= 0.5 for 2 day(s) | Rs 977,415 |
| 2024-07-09 | BUY 50% | 24,426 | P(bull) = 0.63 >= 0.6 for 2 day(s) | Rs 981,628 |
| 2024-07-15 | ADD to 100% | 24,585 | P(bull) = 0.77 rose to >= 0.75 | Rs 984,767 |
| 2024-10-07 | REDUCE to 50% | 24,802 | P(bull) = 0.68 fell below 0.75 | Rs 992,959 |
| 2024-11-19 | SELL | 23,486 | P(bear)+P(high_vol) = 0.57 >= 0.5 for 2 day(s) | Rs 969,451 |