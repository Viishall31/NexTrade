# NexTrade — Complete Study Guide for Review 2

This guide teaches the whole project from zero: every concept, every method, why we chose it, what came out, and what it means. All numbers are our real results.

**How to use it**
1. Read **Part 0** until you can say it without notes.
2. Read Parts 1–17 once, slowly. Each part ends with a "What to say" box.
3. Memorise **Part 18** (the numbers sheet).
4. Practise **Part 20** (slide-by-slide script) and **Part 21** (viva questions).

---

## Part 0 — The whole project in 60 seconds (memorise this)

> "The Nifty 50 keeps switching between market moods: bull, bear, sideways and high-volatility. We call these **regimes**. NexTrade first labels every trading day with its regime using a **Hidden Markov Model**, using only past data. Then we trained three deep-learning models, **LSTM, CNN-BiLSTM-Attention and Transformer**, to predict *tomorrow's* regime from the last 30 days of 13 technical indicators. We tuned all three with **Optuna**, chose the Transformer on validation data, and tested it **once** on a year it had never seen: it was right **88%** of the time, and **81%** on 17 more months of completely new data. Then we asked the real question: does trading on these predictions make money? We simulated trading from **₹10 lakh** with realistic costs. The answer was **no, not reliably**: the regimes are only identified *after* the market moves, so even an accurate model acts late. The strategies did cut losses (smaller drawdowns), but none beat a 6% liquid fund. That honest finding, plus a pipeline with no data leakage, is our contribution."

---

## Part 1 — Basics from zero

### 1.1 Stock market words
- **Nifty 50**: an index that tracks the 50 largest companies on the National Stock Exchange (NSE) of India. It is a number (around 22,000–26,000 in 2024–26), not a share you can buy directly.
- **ETF (Exchange-Traded Fund)**: a fund that copies the Nifty 50 and trades like a share. This is how a normal investor "buys the Nifty". Our realistic trading uses a Nifty ETF.
- **Futures**: a contract to buy/sell later; lets you go **short** (profit when prices fall). We report futures only as an "idealised" comparison.
- **Long** = you own it, profit if price rises. **Short** = profit if price falls. **Flat / cash** = no position.

### 1.2 Price data
- **Bar / candle**: a summary of price over a time slice. A **15-minute bar** covers 15 minutes; a **daily bar** covers one day.
- **OHLC**: **O**pen (first price), **H**igh (highest), **L**ow (lowest), **C**lose (last price) of the bar. **OHLCV** adds **V**olume; our index data has **no volume**.
- NSE trades 09:15–15:30, so a day has **25 fifteen-minute bars** (starting 09:15, 09:30, … 15:15).
- **Resampling**: turning 25 fifteen-minute bars into 1 daily bar: open = first open, high = max, low = min, close = last close.

### 1.3 Returns, volatility, risk
- **Return**: percentage change. From 100 to 110 is +10%.
- **Log return**: ln(close_t / close_{t−1}). Almost the same as % return for small moves, but adds up nicely over time. The **20-day log return** is ln(close_t / close_{t−20}).
- **Volatility**: how much prices jump around = standard deviation of returns. **Annualised realised volatility** = std of daily log returns × √252 (252 trading days in a year).
- **Drawdown**: how far your money has fallen from its highest point. **Maximum drawdown (MDD)** = the worst such fall. Buy & hold had −15.7% in the test year.
- **Risk-free rate**: what you get with no risk (liquid fund / T-bill). We use **6% a year**.
- **Sharpe ratio**: (return − risk-free return) ÷ volatility, annualised. It means "extra return per unit of risk". Above 1 is good; negative means you did worse than cash.
- **Sortino ratio**: like Sharpe, but only counts downside volatility.

### 1.4 Market regimes
A **regime** is a persistent "mood" of the market:
| Regime | Meaning in our project |
|---|---|
| **Bull** | steady rise, low volatility |
| **Sideways** | small drift, moderate volatility |
| **Bear** | weak or falling trend, higher volatility |
| **High-volatility** | big swings, usually crashes (e.g. COVID March 2020) |

Why care? A strategy that works in a bull market (stay invested) can hurt in a bear market. If you knew the regime in advance, you could adjust.

> **What to say:** "Regimes are persistent market moods. Knowing the current regime could tell an investor how much risk to take."

---

## Part 2 — The problem, the literature and our gap

### 2.1 Problem statement (slide 2)
Can a model trained on HMM regime labels predict the **next day's** regime on **unseen** Nifty 50 data, which of three architectures does it best, and does **trading** on the prediction make money?

### 2.2 Objectives (slide 3)
1. Regime labelling with HMM + training on time-ordered data — **Done**
2. Implement and compare CNN-BiLSTM-Attention, LSTM, Transformer — **Done**
3. Hyperparameter optimisation with Optuna — **Done**
4. Validate on unseen and 15-minute data — **Adapted** (no broker API → replay + forward test instead of live Kite)

### 2.3 The 10 papers in one line each (slides 4–5)
| # | Paper | What it did | Gap for us |
|---|---|---|---|
| 1 | Yuan & Mitra 2016 | HMM finds regimes in European indices | Only labels, no prediction/trading, not India |
| 2 | Lu et al. 2020 | CNN-BiLSTM + attention beats LSTM/MLP/SVM | Predicts price, no regimes, no Transformer |
| 3 | Al Ridhawi et al. 2026 | Autoencoder + dual Transformers + RL for regime shifts | Too heavy, US only |
| 4 | Xiao, Bi & Deng 2024 | LSTM vs GRU vs Transformer on Tesla | One US stock, price regression |
| 5 | ScienceDirect 2025 | LSTM/Transformer vs ARIMA | No CNN-BiLSTM-Attn, no regimes, no India |
| 6 | Research Square 2025 | Tuning methods on Nifty BeES; **Optuna TPE best** | Only LSTM/1D-CNN → **why we use Optuna TPE** |
| 7 | IEEE 2022 | LSTM on Nifty 50 daily | One model, no regimes |
| 8 | MDPI 2024 | Many DL models on Indian stocks | Error metrics only, no trading |
| 9 | Evolving Systems 2022 | Online/incremental learning for live data | Not regimes, not Nifty 15-min |
| 10 | **Mishra et al. 2025** (likely our mentor's paper) | DQN/DDQN/Dueling DDQN on 15-min Nifty 50 | Single fixed policy, no regime classifier |

**Be respectful about paper 10:** "It is the closest Indian study and uses the same kind of data. NexTrade *extends* that direction by adding an explicit regime layer and a three-model comparison."

### 2.4 Research gap (slide 6)
- Regime papers stop at labelling; they never test trading.
- Model papers compare at most two of our three models, on price error.
- Nobody tests "money after costs on data never used for design".
- **Our novelty:** causal HMM labels + fair three-model comparison with multi-seed tuning + frozen selection and one-time test + rupee trading + untouched forward test.

---

## Part 3 — Tools (slide 7) and why each

| Tool | What it is | Why we used it |
|---|---|---|
| **Python 3.13** | programming language | standard for data science |
| **pandas, NumPy** | tables and maths | data cleaning, indicators |
| **Parquet (PyArrow)** | fast file format | stores processed data |
| **hmmlearn** | HMM library | fits Gaussian HMMs with EM |
| **SciPy** | scientific maths | our own forward filter (log-space) |
| **PyTorch 2.14** | deep-learning framework | builds and trains the 3 models; runs on CPU and GPU |
| **Google Colab (T4 GPU)** | free cloud GPU | 15-min model was ~5 h on laptop CPU, ~1–2 min/seed on GPU |
| **Optuna 4.9** | hyperparameter tuning | TPE sampler (paper 6 showed it works best on Indian data) |
| **scikit-learn** | ML utilities | accuracy, F1, confusion matrix, logistic-regression baseline |
| **yfinance** | free market data | fresh Nifty data after our files end |
| **SQLite** | small database | logs every replay prediction |
| **Streamlit + Plotly** | web dashboard | shows results to non-technical reviewers |
| **pytest** | automated tests | 52 tests check leakage, causality, maths |

Hardware: laptop, 12 logical cores, 8 GB RAM, no NVIDIA GPU → Colab for the 15-minute model.

---

## Part 4 — Step 1: Data and cleaning (slide 11)

### 4.1 What we received
- `Nifty50_train.csv`: **57,478** 15-min bars, 23 Apr 2015 – 30 Apr 2024
- `Nifty50_test.csv`: **6,014** bars, 2 May 2024 – 8 Apr 2025
- Columns: date, time, open, high, low, close, plus vendor columns (pivot, 200_EMA, three Supertrends). **No volume.**

### 4.2 Problems we found (data audit) and how we fixed them
| Problem | Evidence | Fix | Why |
|---|---|---|---|
| **Duplicate rows** | 1,850 rows; 74 days appear twice | Keep the **first** copy | The file was exported in chunks that overlap. The second copy's 09:15 open was ~55 points away from the previous close (the first copy: < 1 point) → the second copy is corrupted |
| **Vendor indicators unreliable** | Duplicate days had *different* 200-EMA values | Dropped; recomputed all indicators ourselves | The vendor restarted the calculation at every chunk |
| **Special sessions** | Bars after 15:30 (Diwali **Muhurat** evening trading, 24-Feb-2021 NSE outage day) | Keep only 09:15–15:15 bars; drop days with gaps | These are not normal trading and would distort indicators |
| **Missing bars** | 1 single missing bar | Forward-fill only single gaps; drop days with longer gaps (3 days dropped) | Filling long gaps invents data |
| **Unsorted rows** | Timestamps out of order | Sorted | Time series must be in order |

Result: **55,575 bars, 2,223 trading days, each with exactly 25 bars.** Full Saturday sessions (Budget day 1-Feb-2020) were kept because they are real trading days.

We then **resampled to daily bars** because (a) the HMM and the main models work on days, (b) daily regimes are more stable than 15-min ones.

> **What to say:** "Before any modelling we audited the data. The vendor file had 1,850 duplicated rows from a chunked export, and its own indicators restarted at each chunk, so we removed the duplicates and recomputed everything ourselves."

---

## Part 5 — Step 2: Features (13 technical indicators)

A **feature** is an input number the model sees each day. We used 13, all computed from OHLC only:

| Feature | What it measures | Intuition |
|---|---|---|
| **RSI (14)** | momentum 0–100 | > 70 "overbought", < 30 "oversold" |
| **MACD line** (12, 26) | difference of fast and slow EMAs | trend direction and strength |
| **MACD signal** (9) | EMA of MACD | smoother trend |
| **MACD histogram** | MACD − signal | trend acceleration |
| **close / EMA20, EMA50, EMA200** | price relative to short/medium/long averages | above 1 = above the average (uptrend) |
| **ATR / close** (14) | average bar size as % of price | volatility |
| **ADX (14)** | trend strength 0–100 | > 25 = trending |
| **Bollinger %B** (20, 2σ) | where price sits inside the bands | near 1 = top of band |
| **Bollinger bandwidth** | band width / middle | volatility squeeze or expansion |
| **Stochastic RSI %K, %D** (14, 3, 3) | RSI's position in its recent range | fast momentum turns |

Terms: **EMA** = exponential moving average (recent days weigh more). **Wilder smoothing** = the classic RSI/ATR averaging.

**Design choices and why**
- **Scale-free**: MACD divided by price, EMAs as ratios, ATR as % → a Nifty of 8,000 (2016) and 22,000 (2024) look comparable.
- **Causal**: every value at day t uses only days ≤ t. Tested by deleting/scrambling future data and checking past features don't change.
- **Warm-up**: first 200 bars dropped, because the 200-EMA needs history to be meaningful.
- **Scaling (z-score)**: (value − mean) / std, where mean and std come from the **training period only**. If we used all data, the model would secretly "know" the future average → **data leakage**.
- **Dropped from the spec**: OBV and VWAP need volume (none in index data); India VIX not used (team decision).

Two extra columns are **not model inputs**; they feed the HMM: **20-day log return** and **20-day realised volatility**.

---

## Part 6 — Step 3: Hidden Markov Model (slide 11)

### 6.1 What is an HMM (simple)
Imagine the market has a hidden "mood" you cannot see directly. Each day:
1. The mood may stay the same or switch, following fixed **transition probabilities** (e.g. bull stays bull 98.7% of days).
2. Given the mood, the market produces observable numbers (return, volatility) from that mood's **Gaussian (bell-curve) distribution**.

The HMM learns (a) the typical return/volatility of each mood, (b) how moods switch, and then tells us the probability of each mood on each day.

- **Gaussian HMM**: each state's observations follow a multivariate normal distribution.
- **Full covariance**: return and volatility are allowed to be correlated within a state.
- **Fitting = Baum-Welch (EM)**: guess parameters → compute state probabilities → re-estimate parameters → repeat until stable. We used **10 random restarts** and kept the best likelihood (EM can get stuck).
- **Fitted on training data only** (Feb 2016 – Dec 2021) and then **frozen** (never refitted).

### 6.2 The most important design choice: filtered, not smoothed
There are three ways to read the state:
| Method | Uses | Problem |
|---|---|---|
| **Viterbi / smoothed (forward-backward)** | past **and future** days | a day's label depends on what happened later → impossible live, leaks the future |
| **Filtered (forward only)** ✅ | past and today only | exactly what you would know in real time |

We implemented the **forward filter** ourselves:
α_t(j) = [Σ_i α_{t−1}(i) · a_ij] · b_j(o_t), then normalise → P(state_t = j | data up to t).
A unit test proves that changing future days never changes past labels.

### 6.3 Naming the states
The HMM just gives states 0–3. We named them from their training statistics:
- highest volatility → **high-volatility**
- of the rest: highest mean 20-day return → **bull**, lowest → **bear**, middle → **sideways**

Training statistics:
| Regime | Mean 20-day return | Mean annual volatility | Training days |
|---|---|---|---|
| Bull | +2.4% | 9.3% | 609 |
| Sideways | +1.2% | 13.8% | 503 |
| Bear | +0.3% | 20.9% | 284 |
| High-vol | −8.6% | 55.6% | 54 |

### 6.4 Why we changed the HMM inputs (deviation from spec)
The spec said: 1-day return + 20-day volatility. Result: nonsense labels (2023 rally = 80% "sideways", H1-2022 correction = 70% "bull"), because a single day's return is mostly noise and the HMM grouped days by volatility only.
We compared alternatives and chose **20-day return + 20-day volatility**:

| Period | What happened | Label (20-day return) |
|---|---|---|
| Feb–Apr 2020 | COVID crash | 69% high-vol + 21% bear ✅ |
| Jan–Jun 2022 | Correction | 65% bear ✅ |
| 2023 | Rally | 72% bull ✅ |
| Sep–Oct 2018 | IL&FS selloff | 46% bear ✅ |

### 6.5 BIC and number of states
**BIC (Bayesian Information Criterion)** = fit quality penalised for complexity; lower is better. k=3: 3,446; k=4: 2,542; **k=5: 2,012 (best)**. We kept **4** because the project defines four regimes; the spec requires reporting this, and we did.

### 6.6 Limitations of the labels (know these well)
- **Lag**: a regime is identified *after* the move (20-day window + filtering). Example: 4-June-2024 election crash → labelled "bear" *on* the crash day, after the loss.
- **"Bear" is relative**: 2016–2021 mostly rose, so "bear" means "weak trend + higher volatility", not a deep fall. Deep crashes go to high-vol.
- **Slow calm declines look sideways**: Oct 2024 – Mar 2025 fell ~16% but was mostly "sideways".
- Regimes switch ~**9 times a year**; high-vol is rare (3.7% of training days).

> **What to say:** "The HMM labels match real events: COVID is high-volatility, 2022 is bear, 2023 is bull. We use forward-filtered probabilities so labels never use future data."

---

## Part 7 — Step 4: Turning it into a learning problem

### 7.1 Samples
- **Input**: the last **30 trading days** × **13 features** = a 30×13 table.
- **Target**: the HMM regime of **the next day (t+1)**.
- Why t+1? Predicting today's label from today's data would be trivial and useless; a forecast must be about the future.

### 7.2 Splits (never shuffled — time order matters)
| Split | Period | Used for |
|---|---|---|
| **Train** | Feb 2016 – Dec 2021 (1,420 windows) | learning weights, scaler, HMM |
| **Validation** | Jan 2022 – Apr 2024 (573 windows) | early stopping, tuning, model selection, trading-rule choice |
| **Test** | May 2024 – Apr 2025 (test file) | scored **once**, after selection was frozen |
| **Fresh** | 8 Apr 2025 – 15 Sep 2026 (yfinance) | forward test, everything frozen |

**Why not shuffle?** Shuffling puts future days in training → the model "remembers" the future → fake accuracy.

### 7.3 Class imbalance
High-vol is rare (~4%). Without care a model ignores it. We used **class-weighted cross-entropy**: weight = N / (4 × count of that class), so rare classes count more.

### 7.4 Metrics
- **Accuracy**: % correct. Misleading when classes are unbalanced.
- **Precision**: of days predicted "bear", how many were bear. **Recall**: of true bear days, how many we caught. **F1** = harmonic mean of the two.
- **Macro-F1**: average F1 over the classes, each class counting equally → the main metric for imbalanced regimes.
- **Confusion matrix**: table of true vs predicted classes.
- In the test year high-vol never occurred, so we report macro-F1 over the **3 regimes present**.

---

## Part 8 — Step 4: The three models (slide 9)

### 8.1 Neural network basics (enough for the viva)
- **Neuron / weight**: numbers the model learns. **Parameters** = total weights.
- **Layer**: a group of neurons. **Dense (fully connected)** layer: every input connects to every output.
- **Activation (ReLU)**: max(0, x); lets networks learn non-linear patterns.
- **Softmax**: turns 4 output scores into 4 probabilities that sum to 1.
- **Loss (cross-entropy)**: how wrong the probabilities are; training lowers it.
- **Adam optimiser**: an algorithm that adjusts weights to lower the loss. **Learning rate** = step size.
- **Batch**: number of samples per weight update. **Epoch**: one full pass through training data.
- **Dropout**: randomly switches off neurons while training → prevents memorising (overfitting).
- **Overfitting**: great on training data, poor on new data.
- **Early stopping**: after each epoch check validation macro-F1; if no improvement for **10** epochs, stop and restore the best weights.
- **Seed**: starting random number; different seeds give slightly different models. We train **5 seeds** and report mean ± std.

### 8.2 LSTM (Long Short-Term Memory)
A recurrent network that reads the 30 days **one by one**, keeping a memory cell. **Gates** (input, forget, output) decide what to remember or forget, which fixes the "vanishing gradient" problem of simple RNNs.
- Default (spec): 2 LSTM layers × 64 units → Dense 32 → softmax (55,716 params)
- **Tuned: 3 layers × 128 units, dropout 0.38, lr 0.0034, batch 64 (341,668 params)**

### 8.3 CNN-BiLSTM-Attention
Three ideas stacked:
1. **CNN (1-D convolution)**: small filters slide over 3 days at a time to spot local patterns (e.g. a 3-day reversal). **Causal padding** = each position only sees earlier days. **MaxPool 2** halves the length 30 → 15.
2. **BiLSTM (bidirectional LSTM)**: one LSTM reads the window forward, one backward. Both directions are *inside the past window*, so no future leakage.
3. **Additive (Bahdanau) attention**: learns a weight for each time step ("which days matter most") and takes a weighted average.
- Default: conv 64→128, BiLSTM 64/direction (139,172 params)
- **Tuned: 3 conv layers (64–128–128), BiLSTM 128/direction, dropout 0.43, lr 0.0050, batch 16 (365,604 params)**
- Why this model: paper [2] showed this hybrid is strong for markets.
- Note: the spec said "tune attention heads" for this model, but additive attention has no heads, so we did not tune heads (documented deviation).

### 8.4 Transformer encoder
Instead of reading step by step, **self-attention** lets every day compare itself with every other day in the window at once.
- **Linear projection**: 13 features → d_model numbers per day.
- **Sinusoidal positional encoding**: adds "which position in the window" information (attention itself ignores order).
- **Multi-head attention**: several attention "views" in parallel (4 heads).
- **Feed-forward** block after attention; **mean pooling** over the 30 days → Dense 32 → softmax.
- Default: d_model 64, 2 layers, 4 heads, FF 128 (70,052 params)
- **Tuned: d_model 128, 2 layers, 4 heads, FF 256, dropout 0.31, lr 0.0015, batch 64 (271,012 params)**
- Why: the modern standard architecture [17]; paper [4] compared it with LSTM.

### 8.5 Fairness rules (spec C-2)
Same input window, same features, same splits, same loss, same metrics, same early stopping, same 5 seeds for all three.

---

## Part 9 — Step 4 results: default models (before tuning)

Validation (Jan 2022 – Apr 2024), 5-seed mean:
| Model | Accuracy | Macro-F1 |
|---|---|---|
| LSTM | 0.764 | 0.631 |
| CNN-BiLSTM-Attention | 0.777 | 0.689 |
| Transformer | 0.762 | 0.709 |
| Always predict most common regime | 0.483 | 0.163 |
| Logistic regression on last day only | 0.787 | 0.592 |
| Persistence reference (uses today's true label) | 0.941 | 0.932 |

What it means:
- All models learn something real (0.63–0.71 vs 0.16).
- A simple logistic regression has higher accuracy but never catches high-vol → the deep models' advantage is mainly on the rare class.
- **Persistence** ("tomorrow = today's label") is 94% because regimes last weeks. The models never see today's label, so it is a *reference*, not a competitor. It shows regimes are "sticky".
- High-vol F1 swung 0.00–0.82 across seeds because validation had only 11 high-vol days → why we use 5 seeds.

---

## Part 10 — Step 5: The backtester (how trading is measured)

A **backtest** simulates a strategy on past data.

**Spec strategy**: exposure by predicted regime — bull **100%**, sideways **50%**, high-vol **25%**, bear **0%**.

**How one day works (no look-ahead):**
1. At the close of day t the model predicts the regime of t+1.
2. We set the position at that close.
3. We earn the return from close t to close t+1.
Nothing from day t+1 is used to choose the position.

- **Costs**: 5 basis points (0.05%) × change in exposure.
- **Cash** (uninvested part) earns 6%/year → 100% cash has Sharpe exactly 0.
- Metrics: Sharpe, Sortino, max drawdown, cumulative return.

Validation results (default models): Sharpe LSTM **0.80**, CNN **0.75**, Transformer **0.71** vs buy & hold **0.49**; drawdown ~−7% vs −16.5%.
- The strategies earned about the same as buy & hold with less than half the drawdown (they reduced exposure in the 2022 fall).
- They even beat trading on the *true* HMM labels (Sharpe 0.53) — because the labels lag, and the models react earlier via price/EMA features. First sign that **"accurate label copying ≠ best trading"**.

---

## Part 11 — Step 6: Hyperparameter tuning with Optuna (slide 12)

### 11.1 Concepts
- **Hyperparameters**: settings *we* choose (learning rate, layers, units, dropout, batch size, heads), not learned weights.
- **Optuna**: a tuning library. Each **trial** = train one model with one setting and score it.
- **TPE (Tree-structured Parzen Estimator)**: a Bayesian method. It builds a model of which settings scored well vs badly and proposes new settings more likely to be good — smarter than grid or random search.
- **Median pruner**: stops a trial early if, at the same epoch, it is worse than the median of earlier trials → saves time. 37 of 150 trials were pruned.

### 11.2 Search space
| Setting | Range |
|---|---|
| Learning rate | 0.0001–0.01 (log scale) |
| Batch size | 16, 32, 64, 128 |
| Dropout | 0.1–0.5 |
| Layers | 1–3 (LSTM layers; CNN conv layers) |
| Hidden units / d_model | 32, 64, 128, 256 |
| Heads (Transformer) | 2, 4, 8 |
| Feed-forward size (Transformer) | 64, 128, 256 |

### 11.3 Objective
**0.6 × validation macro-F1 + 0.4 × normalised Sharpe**, where normalised Sharpe = clip((Sharpe + 1) / 3, 0, 1) so both parts are on a 0–1 scale. Why both? The spec says a model that classifies well but trades badly is not the goal.

### 11.4 Seed luck and our fix (key methodology point)
The best **single-seed** trials scored ~**0.71**. Re-run with **5 seeds**, they averaged only **0.63–0.68**. The trial with the best single-seed score was **never** the final winner.
→ We re-ran the **top 3 trials of every model on 5 seeds** and picked the best **mean**. This is called avoiding the "winner's curse".

| Model | Best single seed → its 5-seed mean | Chosen trial 5-seed mean |
|---|---|---|
| LSTM | 0.710 → 0.632 | 0.637 ± 0.032 |
| CNN-BiLSTM-Attention | 0.707 → 0.666 | 0.680 ± 0.036 |
| Transformer | 0.714 → 0.631 | 0.691 ± 0.020 |

### 11.5 Results (validation, 5-seed means)
| Model | Default F1 → Tuned F1 | Objective default → tuned | Tuned Sharpe |
|---|---|---|---|
| LSTM | 0.631 → 0.685 | 0.619 → 0.637 | 0.70 |
| CNN-BiLSTM-Attention | 0.689 → **0.762** | 0.647 → 0.680 | 0.67 |
| Transformer | 0.709 → 0.758 | 0.654 → **0.691** | **0.77** |

- **Most important hyperparameters (fANOVA)**: learning rate and dropout. Model size barely mattered (only ~1,400 training days).
- Tuning improved F1 for all; Sharpe went down for LSTM and CNN (objective weights F1 at 60%).

---

## Part 12 — Step 7: Model selection and the one-time test

### 12.1 Selection rule (spec 9.3), written to a file **before** opening the test data
1. Keep models with macro-F1 within **2 percentage points** of the best (0.762) → CNN (0.762) and Transformer (0.758); LSTM (0.685) out.
2. Among them, highest Sharpe → **Transformer (0.77 vs 0.67)**.
CNN was flagged "best classifier but not best Sharpe" (spec FR-E4 asks to flag, not hide, such conflicts).
**Deployment**: average the softmax outputs of the 5 tuned Transformer seeds (a **seed ensemble**) — also decided before testing.

### 12.2 Preparing the test file
Same cleaning rules (200 duplicates, special sessions, partial days dropped) → **5,800 bars, 232 days**. Indicators were computed with the training data as history (so no test days lost to warm-up), the frozen scaler and frozen HMM were applied, and an integrity check confirmed all pre-test features and labels were identical to training files.

### 12.3 Classification results on the test year (May 2024 – Apr 2025)
| | Accuracy | Macro-F1 (3 regimes) |
|---|---|---|
| **Transformer 5-seed ensemble (deployed)** | **0.879** | **0.836** |
| Transformer single seeds (mean) | 0.802 | 0.708 |
| Logistic regression baseline | 0.815 | 0.730 |

- **Ensembling** added ~13 F1 points: averaging 5 models cancels their individual random mistakes.
- Validation → test F1 gap for a single Transformer: 0.758 → 0.708 (only −0.05) → good generalisation.
- Recall: bull 0.87, bear 0.85, sideways 0.89; only 0.4% of predictions below 50% confidence.
- Test labels: sideways 151 days, bull 61, bear 20, high-vol 0.

### 12.4 Trading the test year with the spec strategy
Every strategy had a **negative Sharpe**, including trading on the true labels, because the market was roughly flat (below 6% cash). Transformer ensemble: −7.7% return, drawdown −10.1%; buy & hold −1.8%, drawdown −15.7%.

**Why (verified day by day):**
- 3 June 2024: model says bull → fully invested.
- 4 June 2024 (election results): Nifty −5.65% → full loss.
- The crash itself turns the HMM label to "bear" for 4 weeks → model follows → goes to cash → **misses the +9% rebound**.
→ The labels lag, and the model learned the lag. It is not a bug; it's a limitation of backward-looking labels.

---

## Part 13 — Steps 8–9: 15-minute model and walk-forward replay (slide 15)

### 13.1 Why a 15-minute model
The spec wanted live validation on 15-minute data. We trained the selected architecture (Transformer, with its tuned daily settings) on **48-bar windows** (~2 days) of 15-min bars. Each bar gets its day's HMM regime.
- 36,202 training and 14,325 validation windows → too slow on CPU (~5 h) → **Google Colab T4 GPU** (~1–2 min per seed).
- Validation: ensemble accuracy **0.702**, macro-F1 **0.613** — weaker than daily. Best epochs were 1–4 → overfits fast; the daily learning rate is probably too high for 25× more data.

### 13.2 Walk-forward replay (replaces live Kite)
No broker API, so we **replayed the test file as if live**:
- Bars arrive **one at a time**. For each bar: recompute indicators on the last 2,000 bars (the 200-EMA's memory after 2,000 bars is < 1e-8, so this equals using full history), predict with the 5-seed ensemble, log timestamp, probabilities, confidence and latency to **SQLite**.
- At each day's close the frozen HMM advances **one forward step** → that day's true label.
- Predictions below 0.5 confidence are flagged.
- No component can place orders (spec C-4).

### 13.3 Replay results
| Check | Result | Meaning |
|---|---|---|
| Bars processed | **5,800 / 5,800** | 100% uptime (spec ≥ 95%) |
| Latency per bar (p95) | **163 ms** | spec < 2,000 ms |
| Match with batch pipeline | **100%** predictions, max prob diff 3e-07 | the live path has **no hidden look-ahead** |
| 15-min accuracy | **51.8%** (vs 70.2% validation) | the 15-min model does not generalise well |
| Low-confidence share | 16.6% | |

> **What to say:** "The replay proves the system works bar by bar exactly like the offline pipeline and fast enough for live use; the 15-minute model itself needs separate tuning, which is future work."

---

## Part 14 — Steps 10–11: Trading in rupees (slides 16–17)

### 14.1 The simulator
- Start **₹10,00,000**. Decide at each day's close, trade at that close.
- **Nifty ETF** (realistic): cost **0.10% per buy/sell** + **₹15.93 per sell** (DP charge); idle cash earns **6%**.
- **Futures (idealised)**: 0.03% per side + 0.06% monthly rollover; can short; uses spot prices and fractional contracts (one real Nifty lot is worth more than ₹10 lakh), so only a comparison.
- Rebalance only if the target changes by ≥ 25% of the portfolio (avoids tiny costly trades).

### 14.2 Experiment 1: regime rules
Each rule = 4 settings:
1. **Exposure map**: e.g. `risk_off` = 100% in bull and sideways, 0% in bear and high-vol; `spec` = 100/50/25/0; `bull_only`; `prob_weighted`
2. **Confirmation**: switch only after N identical predictions (1, 2, 3)
3. **Confidence filter**: ignore predictions below 60% (on/off)
4. **Stop-loss**: sell if the position falls 5% from its peak (on/off)

42 ETF + 30 futures rules per model, simulated on **validation**; winner = most money with drawdown no worse than buy & hold; **frozen**, then traded the test year once.
Example (Transformer): `risk_off, confirm 2, 5% stop` → validation ₹14.04 lakh → **test ₹9,29,569**.

**Why it lost:** repeated whipsaw — stop-loss sells after a drop → label soon changes to "sideways" (counted as invested) → buys back higher. Happened 4 times (Jun, Oct, Nov/Dec 2024, Jan 2025).

### 14.3 Experiment 2: probability rulebook (post-hoc)
Designed **after** seeing Experiment 1's test result, so we label it **post-hoc**. Uses probabilities directly:
| Rule | Default |
|---|---|
| BUY | P(bull) ≥ 0.60 for 2 days → 100% if P(bull) ≥ 0.75, else 50% |
| SELL | P(bear) + P(high-vol) ≥ 0.50 for 2 days → cash (futures: short) |
| HOLD | otherwise; **sideways never trades** |
| STOP-LOSS | 8% trailing |
| COOLDOWN | no buy for 5 days after a sell; fresh signal needed after a stop |
Default fixed in advance; tuned version: 324 settings searched on validation.

### 14.4 Test-year results (ETF, from ₹10 lakh)
| Model | Exp 1 rules | Exp 2 tuned |
|---|---|---|
| LSTM | ₹9,70,051 | ₹10,21,018 |
| CNN-BiLSTM-Attention | ₹9,62,903 | ₹10,06,074 |
| Transformer | ₹9,29,569 | ₹10,19,525 |
| Buy & hold | ₹9,81,776 | |
| Cash at 6% | ₹10,55,109 | |

**The crucial check — where did Exp 2's profit come from?**
Profit = interest on idle cash + trading P&L. Example LSTM tuned: +₹21,018 = +₹35,416 interest **−₹14,398 trading**. Trading P&L was **negative in all 9 versions** → the "profit" was just being in cash while the market fell.

**Timing check:** a portfolio holding the same average % invested every day, with no signals, did better than the LSTM and Transformer rules; only the CNN's timing added a little.

---

## Part 15 — Step 12: Forward test on fresh data (slide 18)

### 15.1 Why
Experiment 2 was designed after seeing test results → it could be hindsight. The only honest check: data **nobody** used. Our files end 7-Apr-2025; today is Sep 2026 → **17 months of new data**.

### 15.2 How
- Downloaded daily ^NSEI from **yfinance**. Checked it against our vendor data on 2,413 overlapping days: median close difference **0.024%**, return correlation **0.998**.
- Dropped the 21-Oct-2025 Muhurat session; kept 3-Nov-2025 (normal prices, glitchy volume).
- Integrity: all features/labels before 7-Apr-2025 identical to earlier files.
- **Nothing changed**: frozen scaler, HMM, models, Experiment 1 rules, Experiment 2 rulebook.
- 354 trading days; Nifty 22,203 → 23,119 (+4%); labels: bull 190, sideways 88, bear 72, high-vol 4.

### 15.3 Results
| | Result |
|---|---|
| Transformer accuracy / macro-F1 | **0.811 / 0.652** (LSTM 0.703/0.495, CNN 0.630/0.419) |
| Exp 2 rulebook | **0 of 9** versions profitable → the test-year gain did **not** persist |
| Exp 1 rules | 5 of 6 profitable |
| Best realistic | **CNN-BiLSTM-Attention + Exp 1: ₹11,24,388** (beat buy & hold ₹10,40,165 and cash ₹10,85,297; trading P&L +₹1,06,102) |

**Both unseen periods chained (May 2024 – Sep 2026):** best realistic = CNN Exp 1 **₹10,82,677** > buy & hold ₹10,21,208 but < cash ₹11,45,107. No ETF system profitable in both periods. The only system that beat cash in both is the **idealised** CNN futures version (₹12,12,346).

---

## Part 16 — The dashboard (slide 19)

Streamlit web app, read-only, 6 pages:
1. **Overview** — verdict and key numbers
2. **Regimes** — Nifty price + one row per regime for HMM truth and a model's forecast; date and regime filters
3. **Models** — default vs tuned, accuracy by period, confusion matrices
4. **Replay** — 15-min confidence/accuracy over time, prediction log from SQLite
5. **Trading** — equity curves, profit vs interest, trade logs with the reason for each trade, scorecard
6. **Method & limitations**

Design detail you can mention: colours were checked with a colour-blindness validator; regimes are shown as separate rows so meaning doesn't depend on colour alone.
Run: `streamlit run dashboard/app.py`.

---

## Part 17 — Engineering quality (why the results are trustworthy)

| Practice | What we did |
|---|---|
| Single config file | every parameter in `config/config.yaml` |
| Reproducibility | fixed seeds (42–46); results regenerate from scripts |
| Experiment log | every training run, tuning trial and evaluation in `reports/experiments.jsonl` |
| Frozen decisions | selection and rules saved with timestamps; scripts refuse to overwrite them |
| **52 automated tests** | data validity, indicator causality, train-only scaling, HMM causality, forward-filter correctness, window alignment (target = t+1), model shapes, backtest maths (costs, cash, drawdown), trading rules (stop-loss, cooldown, confirmation) |
| Standards | requirements written as an SRS following **IEEE Std 830-1998** |

---

## Part 18 — Numbers sheet (memorise)

| Topic | Number |
|---|---|
| Raw → clean training bars | 57,478 → 55,575 (1,850 duplicates removed), 2,223 days |
| Features | 13 |
| HMM | 4 states, fitted 2016–2021, 20-day return + 20-day volatility, filtered |
| HMM checks | COVID 69% high-vol + 21% bear; 2022 H1 65% bear; 2023 72% bull |
| BIC | k=5 best (2,012) vs k=4 (2,542); kept 4 |
| Window / target | 30 days × 13 features → next-day regime |
| Tuning | 50 trials × 3 models, top 3 re-run × 5 seeds |
| Seed luck | 0.71 single seed → 0.63–0.68 on 5 seeds |
| Tuned validation F1 | LSTM 0.685, CNN 0.762, Transformer 0.758 |
| Selected | Transformer (Sharpe 0.77 vs CNN 0.67) |
| Test year | Transformer ensemble 87.9% accuracy, macro-F1 0.836 (baseline 0.730) |
| Fresh data | Transformer 81.1% accuracy, macro-F1 0.652 |
| Replay | 5,800/5,800 bars, p95 163 ms, 100% match, 15-min accuracy 51.8% |
| Test-year trading (ETF) | Exp 1: ₹9.30–9.70 L; Exp 2 tuned: ₹10.06–10.21 L; B&H ₹9.82 L; cash ₹10.55 L |
| Exp 2 trading P&L excl. interest | negative in all 9 versions |
| Fresh trading | CNN Exp 1 ₹11.24 L (best); Exp 2: 0 of 9 profitable |
| 2.4-year chained best | CNN Exp 1 ₹10.83 L vs B&H ₹10.21 L vs cash ₹11.45 L |
| Drawdown | realistic systems −6.6% to −13.0% vs B&H −15.7% (test year) |
| Tests | 52 |

---

## Part 19 — Significance: what our results mean

1. **Regime classification works.** A Transformer can forecast HMM-defined regimes on unseen data (88% test, 81% fresh). Averaging 5 seeds matters a lot.
2. **Accuracy ≠ profit.** The best classifier (Transformer) was the worst trader; the weakest classifier (CNN) traded best. Reason: HMM labels are identified after moves, so faithfully copying them means acting late.
3. **The limiting factor is the label definition, not the model.** Future work should label regimes by what the market does *next*.
4. **Risk reduction is real.** Every realistic system had smaller drawdowns than buy & hold.
5. **Honest evaluation changed the story twice**: multi-seed re-runs exposed lucky tuning; the untouched forward test exposed the post-hoc rulebook. This matches the known danger of "backtest overfitting" (Bailey et al. [20]).
6. **Engineering contribution**: a leakage-free, tested, reproducible pipeline + replay + dashboard that others can build on.

**Limitations to state yourself (evaluators respect this):** label lag; slow declines look sideways; few regime episodes; 15-min model untuned; Experiment 2 post-hoc; futures idealised; approximate costs; no volume/VIX.

**Future work (Weeks 8–15):** forward-looking regime labels; walk-forward yearly retraining; tune the 15-min model; revise rules on validation; live paper trading when API access exists; add VIX and futures volume; Bank Nifty.

---

## Part 20 — Slide-by-slide script (26 slides)

Suggested split: Speaker A slides 1–8, Speaker B 9–15, Speaker C 16–26 (adjust to who built what).

1. **Title** — "Good morning, we are Group 17. Our project is NexTrade, a regime-aware AI trading system for the Nifty 50. This is our midterm progress."
2. **Overview** — Problem: markets switch regimes; regime papers only label, model papers ignore trading. Solution: HMM labels → 3 models → tune/select → test → replay → trade → forward test. End with the question: "Can we predict tomorrow's regime, and does trading on it make money?"
3. **Objective** — Objectives 1–3 done; 4 adapted because no broker API: replay + forward test.
4–5. **Literature review** — Don't read the table. Say the pattern: regime papers stop at labelling; model papers compare ≤ 2 models on price error; paper 6 → Optuna TPE; paper 10 (Mishra et al.) closest Indian 15-min study, we extend it with a regime layer.
6. **Research gap** — left: what's missing; right: our 4 additions.
7. **Tools** — PyTorch, hmmlearn, Optuna, scikit-learn, Streamlit, pytest (52 tests), Colab GPU.
8. **Architecture** — walk the 12 boxes: data → labels (blue), modelling (green), validation/trading/delivery (orange). All built.
9. **Model designs** — LSTM reads days in order; CNN-BiLSTM finds local patterns then weights days with attention; Transformer compares all days at once. Same input/output for fairness.
10. **Evaluation design** — 6 anti-leakage rules; chart shows train/validation/test/fresh.
11. **Data & HMM** — 1,850 duplicates found and removed; HMM labels match COVID/2022/2023; changed to 20-day return because 1-day returns gave nonsense.
12. **Tuning** — tuning improved every model; single-seed winners were lucky (0.71 → 0.63–0.68), so we re-run top 3 on 5 seeds. Transformer selected by the frozen rule.
13. **Classification results** — Transformer 87.9% test, 81.1% fresh, macro-F1 0.84 vs 0.73 baseline; others drop more.
14. **Test detail** — strong recall; but labels lag (June 2024 example) and the test year was mostly "sideways".
15. **Replay** — 5,800 bars one by one, 163 ms, 100% identical to batch; the 15-min model itself only 51.8%.
16. **Trading rules** — ₹10 lakh, realistic costs, cash 6%; Exp 1 regime rules; Exp 2 probability rulebook (post-hoc).
17. **Trading results** — Exp 1 lost; Exp 2 slightly positive but only through interest; no system beat cash; all cut drawdown; best classifier traded worst.
18. **Forward test** — 17 months unseen, everything frozen: rulebook 0/9 profitable; CNN Exp 1 ₹11.24 L; no realistic system profitable in both periods.
19. **Dashboard demo** — open Regimes page (show Transformer forecast), then Trading page (switch test year ↔ fresh).
20. **Plan vs actual** — ahead of the Review 1 plan; weeks 8–14 work already done; report in progress.
21. **Challenges** — data, labels, leakage, seed luck, compute, no API, hindsight — each with a fix.
22. **Contributions** — each member says their own part.
23. **Next steps** — fix labels first (forward-looking), then walk-forward years, revise rules, deliver.
24–25. **References** — "21 references, cited in the report."
26. **Thank you.**

---

## Part 21 — Likely viva questions and answers

**Project and scope**
1. *Why did the project change from Review 1 (hierarchical RL)?* — To make it finishable and properly testable in one semester; the core ideas (regime awareness, honest evaluation) stayed.
2. *What is new in your work?* — Causal HMM labels + fair 3-model comparison with multi-seed tuning + frozen selection and one-time test + rupee trading + an untouched forward test.
3. *Why Nifty 50?* — India's benchmark index; data provided; closest prior work [10] also uses it.

**Data**
4. *How did you handle bad data?* — Audited it: 1,850 duplicate rows from overlapping export chunks (kept the copy continuous with the previous close), special sessions removed, single gaps filled, vendor indicators recomputed.
5. *Why no volume features?* — The index file has no volume, so OBV/VWAP were impossible.
6. *Why daily and not 15-minute as the main model?* — Regimes are multi-week phases; daily data gives stable labels and a meaningful next-day forecast. We still built and replayed a 15-minute model.

**HMM**
7. *What is an HMM?* — A model with hidden states that switch with fixed probabilities and generate observations from state-specific distributions.
8. *Why forward-filtered instead of Viterbi?* — Viterbi/smoothing use future days, which leaks information and cannot be reproduced live.
9. *Why 4 states if BIC prefers 5?* — The project defines four regimes; we reported the BIC result as the spec requires.
10. *Why 20-day return instead of daily return?* — Daily return is noise; with it, 2023's rally was labelled sideways. 20-day return matched known periods.
11. *Are the labels "correct"?* — There is no ground truth for regimes; we validated against known events (COVID, 2022, 2023, 2018) and documented limitations (lag, relative bear).

**Models and training**
12. *Why these three models?* — LSTM is the standard baseline, CNN-BiLSTM-Attention is the strongest hybrid in literature [2], Transformer is the modern attention model [17].
13. *How did you ensure a fair comparison?* — Identical inputs, splits, loss, metrics, early stopping and 5 seeds.
14. *How did you prevent overfitting?* — Dropout, early stopping on validation macro-F1, class weights, multi-seed averaging, and a separate test and forward test.
15. *Why macro-F1?* — Regimes are imbalanced; accuracy can look high while ignoring rare regimes.
16. *What is the persistence baseline and why is it 94%?* — "Tomorrow = today's label". Regimes last weeks, so it is high. Our models don't see today's label, so it is a reference for how sticky labels are.
17. *Why predict t+1?* — Predicting today from today is trivial; a forecast must be about tomorrow.

**Tuning and selection**
18. *What is Optuna TPE?* — Bayesian search that models which settings did well and proposes promising new ones; shown best on Indian data [6].
19. *Why re-run on 5 seeds?* — Single-seed scores were lucky: 0.71 fell to 0.63–0.68. Picking by one seed overstates gains.
20. *Why was the Transformer selected over CNN with higher F1?* — Our pre-registered rule: within 2 F1 points, choose higher Sharpe (0.77 vs 0.67). Decided before seeing the test.
21. *Why an ensemble?* — Averaging 5 seeds cancels random errors; it added ~13 F1 points on test.

**Results**
22. *Is 88% good?* — Yes, versus 0.73 macro-F1 for a logistic baseline and a small val→test drop (−0.05). But note labels are sticky.
23. *Why did trading lose if classification is accurate?* — The labels lag the market; a faithful model acts late, e.g. June-2024 crash then rebound.
24. *Why does the best classifier trade worst?* — It copies the lagging labels most closely; the CNN deviates more, and here that helped.
25. *Your Experiment 2 made money — why say it isn't profitable?* — All its profit was interest on cash; trading P&L was negative in all 9 versions, and on fresh data it lost for every model.
26. *Isn't designing rules after seeing test results cheating?* — Yes, if hidden. We labelled it post-hoc and tested it on 17 months of fresh data where it failed. That's exactly why we ran the forward test.
27. *Which system would you actually use?* — None for profit. For risk control, regime-based exposure reduces drawdown; the CNN with Exp 1 rules was the best realistic system over 2.4 years but still below a liquid fund.

**Validation and engineering**
28. *Why no live Kite validation?* — No broker API account. We replayed the test file bar by bar (identical to batch, 163 ms) and forward-tested on fresh data.
29. *How do you know there's no look-ahead?* — Chronological splits, train-only scaler/HMM, causal indicators and filter, tests that scramble future data, and the replay matching the batch pipeline exactly.
30. *What standards did you follow?* — SRS per IEEE 830-1998; automated testing of requirements; reproducible seeded runs.
31. *Why did the 15-minute model do poorly?* — It overfit within 1–4 epochs using daily-tuned settings; it needs its own tuning.
32. *What are transaction costs in your simulation?* — ETF 0.10% per side + ₹15.93 per sell; futures 0.03% + monthly roll; cash earns 6%.

**Future**
33. *What will you do next?* — Forward-looking regime labels, walk-forward yearly retraining, tune the 15-min model, revise rules on validation only, then the black-book report.
34. *How can this be used in practice?* — As a risk-management signal (reduce exposure in risky regimes), a monitoring dashboard, or a research platform.

---

## Part 22 — Glossary (quick lookup)

| Term | Meaning |
|---|---|
| Adam | optimiser that updates weights using adaptive step sizes |
| Attention | learned weighting of which time steps matter |
| Backtest | simulation of a strategy on past data |
| Baum-Welch (EM) | algorithm that fits HMM parameters |
| BIC | model-selection score; lower is better |
| Buy & hold | buy at the start, hold to the end |
| Class weights | make rare classes count more in the loss |
| Confusion matrix | table of true vs predicted classes |
| Cross-entropy | loss for classification |
| Data leakage | information from the future or test set sneaking into training |
| Drawdown | fall from the portfolio's peak |
| Dropout | randomly disable neurons during training |
| Early stopping | stop training when validation stops improving |
| Ensemble | average of several models' outputs |
| Epoch / batch | full pass over data / samples per update |
| F1 / macro-F1 | balance of precision and recall / averaged over classes equally |
| Filtered posterior | state probability using past and present only |
| Forward test | test on new data after all design decisions |
| Gaussian HMM | HMM whose states emit normally distributed observations |
| Hyperparameter | setting chosen before training |
| Median pruner | stops poor Optuna trials early |
| Overfitting | good on training data, bad on new data |
| Persistence | predicting the next value equals the current one |
| Post-hoc | designed after seeing results |
| Regime | persistent market state |
| Seed | starting random number |
| Sharpe ratio | excess return per unit of volatility |
| Softmax | converts scores into probabilities |
| Stop-loss | automatic exit after a set loss |
| TPE | Bayesian hyperparameter search used by Optuna |
| Transformer | self-attention sequence model |
| Viterbi | most likely state path using the whole sequence (uses the future) |
| Walk-forward replay | feeding data one bar at a time as if live |
| z-score | (value − mean) / standard deviation |
