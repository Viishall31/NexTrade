# Trading rulebook (Experiment 2)

Signals come from each trained model (LSTM, CNN-BiLSTM-Attention, Transformer; daily, 5-seed ensemble). At every trading day's close the model outputs the probability of each regime for the **next** day: P(bull), P(sideways), P(bear), P(high-vol). They sum to 1.

## The rules

| # | Rule | Condition | Action |
|---|---|---|---|
| 1 | **BUY** | P(bull) ≥ 0.6 on 2 consecutive days, you hold no position, and no cooldown is active | Buy the Nifty 50 ETF: **100%** of capital if P(bull) ≥ 0.75, otherwise **50%** |
| 2 | **ADD / REDUCE** | Already holding and BUY condition still true | Move to 100% when P(bull) ≥ 0.75, to 50% when it falls below |
| 3 | **SELL** | P(bear) + P(high-vol) ≥ 0.5 on 2 consecutive days | Sell everything, move to cash (SELL beats BUY if both fire) |
| 4 | **HOLD** | Neither BUY nor SELL condition | Do nothing. A sideways forecast alone never causes a trade |
| 5 | **STOP-LOSS** | Portfolio value falls 8% below its highest value since the position was opened | Sell everything at the next close |
| 6 | **COOLDOWN** | After any sell | No new BUY for 5 trading days |
| 7 | **FRESH SIGNAL** | After a stop-loss | No new BUY until P(bull) first drops below the threshold and then meets rule 1 again |

Futures version (idealized): rule 3 opens a **short** instead of moving to cash (50%/100% by the same margin), and a BUY signal first **covers** the short.

## Execution and costs

- Start with Rs 1,000,000. Decisions and trades at the day's close. One action per day.
- ETF: 0.10% of traded value per buy/sell + Rs 15.93 per sell.
- Futures: 0.03% per side + 0.06% monthly roll.
- Uninvested cash earns 6% p.a. (liquid fund).

## Parameters

**Default (fixed in advance, not tuned):** BUY when P(bull) ≥ 0.6 for 2 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.5 for 2 day(s); 8% trailing stop; wait 5 day(s) after an exit.

**Tuned:** 648 combinations searched on validation (Jan 2022 – Apr 2024) per model: buy_threshold [0.5, 0.6, 0.7], sell_threshold [0.4, 0.5, 0.6], confirm_days [1, 2, 3], sizing ['full', 'scaled'], stop_loss [None, 0.05, 0.08], cooldown_days [0, 5], on_sell ['cash', 'short']. Chosen = most money at the end of validation with drawdown no worse than buy & hold. Frozen before the test year.

| Model | Version | Parameters | Validation: final capital | Validation: max DD |
|---|---|---|---|---|
| LSTM | default | BUY when P(bull) ≥ 0.6 for 2 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.5 for 2 day(s); 8% trailing stop; wait 5 day(s) after an exit | Rs 1,193,783 | -6.7% |
| LSTM | tuned, ETF | BUY when P(bull) ≥ 0.7 for 2 day(s) [always 100%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.6 for 2 day(s); 5% trailing stop; wait 5 day(s) after an exit | Rs 1,249,577 | -8.0% |
| LSTM | tuned, futures | BUY when P(bull) ≥ 0.6 for 2 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (go short (futures)) when P(bear)+P(high-vol) ≥ 0.4 for 2 day(s); 5% trailing stop; wait 5 day(s) after an exit | Rs 1,316,539 | -11.1% |
| LSTM | *buy & hold* | – | Rs 1,300,325 | -16.5% |
| CNN-BiLSTM-Attention | default | BUY when P(bull) ≥ 0.6 for 2 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.5 for 2 day(s); 8% trailing stop; wait 5 day(s) after an exit | Rs 1,216,482 | -8.7% |
| CNN-BiLSTM-Attention | tuned, ETF | BUY when P(bull) ≥ 0.5 for 2 day(s) [100% if P(bull) ≥ 0.65, else 50%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.6 for 2 day(s); no stop-loss; wait 0 day(s) after an exit | Rs 1,280,481 | -6.3% |
| CNN-BiLSTM-Attention | tuned, futures | BUY when P(bull) ≥ 0.5 for 3 day(s) [100% if P(bull) ≥ 0.65, else 50%]; SELL (go short (futures)) when P(bear)+P(high-vol) ≥ 0.6 for 3 day(s); 5% trailing stop; wait 0 day(s) after an exit | Rs 1,419,424 | -9.3% |
| CNN-BiLSTM-Attention | *buy & hold* | – | Rs 1,300,325 | -16.5% |
| Transformer | default | BUY when P(bull) ≥ 0.6 for 2 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.5 for 2 day(s); 8% trailing stop; wait 5 day(s) after an exit | Rs 1,204,772 | -6.7% |
| Transformer | tuned, ETF | BUY when P(bull) ≥ 0.5 for 2 day(s) [always 100%]; SELL (move to cash) when P(bear)+P(high-vol) ≥ 0.5 for 2 day(s); 5% trailing stop; wait 5 day(s) after an exit | Rs 1,247,213 | -8.4% |
| Transformer | tuned, futures | BUY when P(bull) ≥ 0.6 for 3 day(s) [100% if P(bull) ≥ 0.75, else 50%]; SELL (go short (futures)) when P(bear)+P(high-vol) ≥ 0.6 for 3 day(s); no stop-loss; wait 5 day(s) after an exit | Rs 1,298,208 | -14.6% |
| Transformer | *buy & hold* | – | Rs 1,300,325 | -16.5% |

Experiment 2 was designed after the Step 10 test-year results were seen (rules 4, 6 and 7 address the whipsaw found there). Parameters were chosen on validation only and the test year is traded once (`11_rulebook_test.md`).