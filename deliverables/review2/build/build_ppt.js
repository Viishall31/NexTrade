// NexTrade — Review 2 deck (pptxgenjs). Style follows the team's Review 1/2 decks: soft blue background,
// large bold uppercase titles, white cards, wave logo top-right.
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const FIG = path.join(__dirname, "..", "figures");
const ASSET = path.join(__dirname, "assets");
const OUT = path.join(__dirname, "..", "NexTrade_Review2_Midterm.pptx");
const REP = path.join(__dirname, "..", "..", "..", "reports");
const rj = (f) => JSON.parse(fs.readFileSync(path.join(REP, f), "utf8"));

const INK = "121518", INK2 = "3F4854", MUTED = "6B7684", LINE = "C9D2DE";
const BLUE = "2A78D6", ORANGE = "EB6834", GREEN = "1A9C6D", NAVY = "1D4F91";
const FONT = "Arial";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "NexTrade — Review 2";

function base(title, opts = {}) {
  const s = pres.addSlide();
  s.background = { path: path.join(ASSET, "background.jpeg") };
  s.addImage({ path: path.join(ASSET, "logo.jpeg"), x: 12.25, y: 0.3, w: 0.6, h: 0.6 });
  if (title) {
    s.addText(title, { x: 0.55, y: 0.3, w: 11.5, h: 0.95, fontFace: FONT, fontSize: opts.size || 36, bold: true, color: INK,
      margin: 0, valign: "middle", isTextBox: true });
  }
  return s;
}
function card(s, x, y, w, h, fill = "FFFFFF", transparency = 10) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill, transparency }, line: { color: LINE, width: 0.75 } });
}
function text(s, t, x, y, w, h, o = {}) {
  s.addText(t, Object.assign({ x, y, w, h, fontFace: FONT, fontSize: 14, color: INK2, margin: 0, valign: "top", isTextBox: true }, o));
}
function img(s, file, x, y, w, h) {
  s.addImage({ path: path.join(FIG, file), x, y, w, h, sizing: { type: "contain", w, h } });
}
function chip(s, label, x, y, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.25, h: 0.32, rectRadius: 0.16, fill: { color }, line: { color } });
  text(s, label, x, y, 1.25, 0.32, { fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
}
function table(s, rows, x, y, w, colW, o = {}) {
  const header = rows[0].map((c) => ({ text: c, options: { bold: true, color: INK, fill: { color: "FFFFFF" }, fontSize: o.headSize || 12 } }));
  const body = rows.slice(1).map((r) => r.map((c) => ({ text: String(c), options: { color: INK2, fill: { color: "F4F7FB" }, fontSize: o.size || 11 } })));
  s.addTable([header, ...body], { x, y, w, colW, fontFace: FONT, border: { type: "solid", pt: 0.75, color: "FFFFFF" }, margin: 0.06, valign: "middle", autoPage: false, rowH: o.rowH });
}

// ------------------------------------------------------------------ 1 title
{
  const s = base(null);
  text(s, "NEXTRADE", 0.5, 1.45, 12.3, 1.5, { fontSize: 88, bold: true, color: INK, align: "center", valign: "middle" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 2.4, y: 3.35, w: 8.5, h: 0.75, rectRadius: 0.37, fill: { color: "F1EFEA" }, line: { color: "F1EFEA" } });
  text(s, "A REGIME-AWARE AI TRADING SYSTEM FOR THE NIFTY 50", 2.4, 3.35, 8.5, 0.75, { fontSize: 18, bold: true, color: INK, align: "center", valign: "middle" });
  text(s, "REVIEW 2  ·  MIDTERM PROGRESS", 3.2, 4.3, 6.9, 0.5, { fontSize: 18, color: INK, align: "center", valign: "middle" });
  text(s, "Mentor: Dr. Raj Gaurav Mishra  ·  MPSTME, SVKM's NMIMS  ·  Academic Year 2026-27", 2.2, 4.85, 8.9, 0.4, { fontSize: 13, color: INK2, align: "center" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.4, y: 6.05, w: 4.5, h: 0.65, rectRadius: 0.32, fill: { color: "FFFFFF", transparency: 45 }, line: { color: "FFFFFF", transparency: 45 } });
  text(s, [{ text: "Presented by:  ", options: { fontSize: 11, color: INK2 } }, { text: "Group 17", options: { fontSize: 20, color: INK } }], 4.4, 6.05, 4.5, 0.65, { align: "center", valign: "middle" });
  text(s, "VISHAL SINGH", 9.8, 5.95, 2.9, 1.0, { fontSize: 14, bold: true, color: INK, align: "right" });
  s.addNotes("Good morning. We are Group 17. Our project is NexTrade, a regime-aware AI trading system for the Nifty 50. Today we present our midterm progress: what we built, the results so far, and the plan to Review 3.");
}

// ------------------------------------------------------------------ 2 overview
{
  const s = base("OVERVIEW");
  card(s, 0.55, 1.55, 5.95, 5.4);
  text(s, "PROBLEM STATEMENT", 0.85, 1.8, 5.4, 0.4, { fontSize: 16, bold: true, color: INK });
  text(s, [
    { text: "The Nifty 50 keeps switching between bull, bear, sideways and high-volatility phases; one fixed strategy cannot work in all of them.", options: { bullet: true, breakLine: true } },
    { text: "Regime-detection studies only label the market; they never test whether the labels help trading.", options: { bullet: true, breakLine: true } },
    { text: "Deep-learning studies compare at most two of LSTM, CNN-BiLSTM-Attention and Transformer, on price error, not on unseen trading.", options: { bullet: true, breakLine: true } },
    { text: "Can a model trained on HMM regimes classify the next day's regime on unseen Nifty 50 data, and does trading on it make money?", options: { bullet: true, bold: true, color: INK } },
  ], 0.85, 2.3, 5.4, 4.4, { fontSize: 14, paraSpaceAfter: 8 });
  card(s, 6.85, 1.55, 5.95, 5.4);
  text(s, "PROPOSED SOLUTION", 7.15, 1.8, 5.4, 0.4, { fontSize: 16, bold: true, color: INK });
  text(s, [
    { text: "Label every trading day with a Gaussian HMM (bull / bear / sideways / high-vol) using past data only.", options: { bullet: true, breakLine: true } },
    { text: "Train LSTM, CNN-BiLSTM-Attention and Transformer on identical splits to forecast the next day's regime from 30 days of 13 indicators.", options: { bullet: true, breakLine: true } },
    { text: "Tune with Optuna, select on validation, test once on May 2024 – Apr 2025.", options: { bullet: true, breakLine: true } },
    { text: "Validate bar-by-bar on 15-min data, trade from Rs 10 lakh with frozen rules, and forward-test on 17 months of unseen data.", options: { bullet: true } },
  ], 7.15, 2.3, 5.4, 4.4, { fontSize: 14, paraSpaceAfter: 8 });
  s.addNotes("Markets change regime. Regime papers stop at labelling, and model papers ignore regimes and trading. NexTrade labels regimes with an HMM, compares three deep models on the same data, tunes and selects them properly, and then tests whether trading on the forecasts makes money.");
}

// ------------------------------------------------------------------ 3 objectives
{
  const s = base("OBJECTIVE");
  text(s, "Develop an AI-based market regime detection system for the Nifty 50 using historical OHLC and technical-indicator data.", 0.6, 1.4, 12.0, 0.7, { fontSize: 18, bold: true, color: INK });
  const objs = [
    ["Regime labelling & model training", "Generate regime labels with a Gaussian HMM and train deep-learning models on time-ordered data.", "DONE", GREEN],
    ["Model development & comparison", "Implement and compare CNN-BiLSTM-Attention, LSTM and Transformer on identical splits and metrics.", "DONE", GREEN],
    ["Hyperparameter optimisation", "Tune every model with Optuna (TPE) for regime accuracy and trading performance, selecting on validation only.", "DONE", GREEN],
    ["Validation", "Validate the best model on unseen and 15-minute data with classification and trading metrics.", "ADAPTED", NAVY],
  ];
  objs.forEach((o, i) => {
    const y = 2.3 + i * 1.18;
    card(s, 0.6, y, 12.1, 1.0);
    text(s, String(i + 1), 0.8, y + 0.15, 0.5, 0.7, { fontSize: 26, bold: true, color: BLUE, valign: "middle" });
    text(s, o[0], 1.4, y + 0.12, 8.7, 0.35, { fontSize: 15, bold: true, color: INK });
    text(s, o[1], 1.4, y + 0.48, 9.6, 0.45, { fontSize: 13 });
    chip(s, o[2], 11.2, y + 0.34, o[3]);
  });
  text(s, "Adapted: no broker API account, so live Kite validation was replaced by a bar-by-bar replay of the 15-min test file and a forward test on fresh data (Apr 2025 – Sep 2026).", 0.6, 7.0, 12.1, 0.4, { fontSize: 11, color: MUTED });
  s.addNotes("All four objectives are addressed. The fourth is adapted: without a broker API we replayed the test file bar by bar and forward-tested on 17 months of fresh data instead of a live Kite feed.");
}

// ------------------------------------------------------------------ 4-5 literature
const lit = [
  ["PAPER", "TITLE", "KEY POINTS", "GAP"],
  ["[1] SSRN, 2016", "Market Regime Identification Using Hidden Markov Models (Yuan & Mitra)", "Gaussian HMM on FTSE 100 / Euro Stoxx 50; captures fat tails and volatility clustering", "Detection only; no classifier, no Indian data, no trading test"],
  ["[2] Neural Comput. & Appl., 2020", "A CNN-BiLSTM-AM Method for Stock Price Prediction (Lu et al.)", "CNN + BiLSTM + attention beats LSTM, MLP, SVM", "Price regression; no regimes, no Transformer"],
  ["[3] arXiv, 2026", "Regime-Aware Prediction with Autoencoder-Gated Dual-Node Transformers and RL (Al Ridhawi et al.)", "Autoencoder flags regime shifts; dual Transformers; RL control", "Very heavy; US only; not a labelled classification task"],
  ["[4] arXiv, 2024", "LSTM, GRU and Transformer for Stock Price Prediction (Xiao, Bi & Deng)", "Head-to-head of three sequence models on Tesla", "One US stock; regression; no regimes or tuning"],
  ["[5] ScienceDirect, 2025", "Integrating Deep Learning and Econometrics for Stock Price Prediction", "LSTM / Transformer vs ARIMA-style models", "No CNN-BiLSTM-Attention; no regimes; no Indian data"],
  ["[6] Research Square, 2025", "Hyperparameter Optimisation in DL Investment Predictions: Indian ETF Analysis", "Grid, Bayesian, Optuna TPE on Nifty BeES; TPE best", "Tunes only LSTM / 1D-CNN; price prediction"],
  ["[7] IEEE Xplore, 2022", "Stock Market Analysis and Prediction for Nifty50 using LSTM", "LSTM on Nifty 50 daily prices", "Single model; no regimes, no tuning, no intraday"],
  ["[8] MDPI, 2024", "Comparative Analysis of Deep Learning Models in the Indian Market", "RNN, LSTM, CNN, GRU, Attention-LSTM on Indian stocks", "Error metrics only; no Transformer; no trading test"],
  ["[9] Evolving Systems, 2022", "Real-Time Stock Prediction with Incremental and Deep Learning", "Online learning updated with streaming data", "Not regime classification; not Nifty 15-min"],
  ["[10] AI (MDPI), 2025", "A Deep RL Framework for Strategic Indian NIFTY 50 Index Trading (Mishra et al.)", "DQN / DDQN / Dueling DDQN on 15-min Nifty 50 with indicators", "Single fixed policy; no regime classifier"],
];
[[1, 6, "LITERATURE REVIEW"], [6, 11, "LITERATURE REVIEW (CONTD.)"]].forEach(([a, b, t]) => {
  const s = base(t);
  table(s, [lit[0], ...lit.slice(a, b)], 0.55, 1.55, 12.25, [2.0, 3.6, 3.4, 3.25], { size: 11.5, headSize: 13, rowH: [0.45, 1.0, 1.0, 1.0, 1.0, 1.0] });
  s.addNotes(a === 1 ? "Regime papers stop at detection; model papers compare at most two of our architectures and measure price error." :
    "Paper 6 showed Optuna TPE works best on Indian data, so we adopted it. Paper 10, by Mishra et al., is the closest Indian study on 15-minute Nifty 50 data; NexTrade extends that line with a regime layer and a three-model comparison.");
});

// ------------------------------------------------------------------ 6 research gap
{
  const s = base("RESEARCH GAP");
  card(s, 0.55, 1.55, 5.95, 5.3);
  text(s, "What existing work misses", 0.85, 1.8, 5.4, 0.4, { fontSize: 17, bold: true, color: INK });
  text(s, [
    { text: "Regime papers [1], [12] stop at labelling; they never test trading.", options: { bullet: true, breakLine: true } },
    { text: "Model papers [2], [4], [5], [8] compare at most two of our three architectures.", options: { bullet: true, breakLine: true } },
    { text: "Evaluation is price error on past data, not money after costs on unseen data.", options: { bullet: true, breakLine: true } },
    { text: "Closest Indian study [10] uses 15-min Nifty 50 but one fixed policy with no regime classifier.", options: { bullet: true } },
  ], 0.85, 2.35, 5.4, 4.3, { fontSize: 15, paraSpaceAfter: 10 });
  card(s, 6.85, 1.55, 5.95, 5.3, "EEF6F1", 5);
  text(s, "What NexTrade adds", 7.15, 1.8, 5.4, 0.4, { fontSize: 17, bold: true, color: GREEN });
  text(s, [
    { text: "Causal HMM regime labels (forward-filtered), frozen after training.", options: { bullet: true, breakLine: true } },
    { text: "All three architectures on identical splits, tuned with Optuna and re-run on 5 seeds.", options: { bullet: true, breakLine: true } },
    { text: "Selection frozen on validation; test file used once.", options: { bullet: true, breakLine: true } },
    { text: "Trading in rupees with costs, frozen rules, and an untouched forward test on 17 months of new data.", options: { bullet: true } },
  ], 7.15, 2.35, 5.4, 4.3, { fontSize: 15, paraSpaceAfter: 10 });
  s.addNotes("Nobody combines causal HMM regime labels with a fair three-way comparison of LSTM, CNN-BiLSTM-Attention and Transformer on Nifty 50, evaluated by trading money on unseen data. That is our contribution.");
}

// ------------------------------------------------------------------ 7 tools
{
  const s = base("TOOLS AND TECHNIQUES");
  table(s, [
    ["CATEGORY", "TOOLS / TECHNIQUES"],
    ["Language & data", "Python 3.13, pandas, NumPy, PyArrow · Nifty 50 15-min OHLC (vendor file) · yfinance ^NSEI daily (fresh data)"],
    ["Features", "13 causal indicators computed from OHLC: RSI, MACD ×3, close/EMA 20·50·200, ATR, ADX, Bollinger %B & width, Stoch RSI %K/%D"],
    ["Regime labelling", "hmmlearn Gaussian HMM, 4 states, full covariance, forward-filtered posterior"],
    ["Deep learning", "PyTorch 2.14: LSTM, CNN-BiLSTM-Attention (additive attention), Transformer encoder · Google Colab T4 GPU for 15-min"],
    ["Tuning & metrics", "Optuna 4.9 (TPE sampler, median pruner) · scikit-learn (accuracy, macro-F1, confusion matrix)"],
    ["Trading evaluation", "Custom backtester and rupee simulator: costs, cash interest, stop-loss, cooldown, Sharpe, drawdown"],
    ["Replay & logging", "Bar-by-bar live pipeline, SQLite prediction log, JSONL experiment log"],
    ["Dashboard & quality", "Streamlit + Plotly · pytest (52 tests: leakage, causality, backtest maths) · config-driven, seeded runs"],
  ], 0.55, 1.55, 12.25, [2.6, 9.65], { size: 13, headSize: 13, rowH: 0.6 });
  s.addNotes("Everything is Python. PyTorch for the models, hmmlearn for regimes, Optuna for tuning, a custom backtester for trading, Streamlit for the dashboard, and 52 automated tests that check for leakage and correct maths.");
}

// ------------------------------------------------------------------ 8 architecture
{
  const s = base("SYSTEM ARCHITECTURE");
  img(s, "fig_architecture.png", 0.9, 1.35, 11.5, 6.0);
  s.addNotes("Twelve stages, all implemented. Data, cleaning, features and HMM labels; windows, three classifiers, tuning and selection; then the one-time test, 15-minute replay, rupee trading, and the forward test with the dashboard.");
}

// ------------------------------------------------------------------ 9 model designs
{
  const s = base("MODEL DESIGNS");
  img(s, "fig_models.png", 1.0, 1.3, 11.3, 5.9);
  text(s, "All three: same input, 4-class softmax, class-weighted cross-entropy, Adam, early stopping on validation macro-F1, 5 seeds. Tuned settings shown.", 0.6, 7.0, 12.1, 0.4, { fontSize: 11, color: MUTED });
  s.addNotes("Same input and output for all three so the comparison is fair. The LSTM reads the window step by step, the CNN-BiLSTM finds local patterns then weights time steps with attention, and the Transformer uses self-attention over the whole window.");
}

// ------------------------------------------------------------------ 10 evaluation design
{
  const s = base("EVALUATION DESIGN");
  const steps = [
    ["Chronological split", "Train Feb 2016 – Dec 2021 · Validation Jan 2022 – Apr 2024 · Test = test file · never shuffled"],
    ["Fit on train only", "Scaler and HMM fitted on training rows, then frozen"],
    ["Causal labels", "Forward-filtered HMM: a day's label never uses later days (unit-tested)"],
    ["Tuning on validation", "Optuna TPE, 50 trials; top 3 re-run on 5 seeds"],
    ["Frozen selection", "Rule fixed before testing: F1 within 2 pts, then best Sharpe"],
    ["One-time test + forward test", "Test file scored once; then fresh Apr 2025 – Sep 2026 data, everything frozen"],
  ];
  steps.forEach((st, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.55 + col * 6.2, y = 1.5 + row * 1.12;
    card(s, x, y, 6.0, 0.98);
    text(s, String(i + 1), x + 0.2, y + 0.14, 0.45, 0.7, { fontSize: 24, bold: true, color: BLUE, valign: "middle" });
    text(s, st[0], x + 0.75, y + 0.1, 4.0, 0.35, { fontSize: 14, bold: true, color: INK });
    text(s, st[1], x + 0.75, y + 0.46, 5.1, 0.5, { fontSize: 11.5 });
    chip(s, "DONE", x + 4.6, y + 0.1, GREEN);
  });
  img(s, "fig_split_timeline.png", 0.9, 4.95, 11.5, 2.45);
  s.addNotes("Six rules keep the test honest, and all are implemented and tested. The chart shows the four periods: training, validation, the one-time test year and the untouched fresh data.");
}

// ------------------------------------------------------------------ 11 HMM regimes
{
  const s = base("DATA & HMM REGIMES");
  img(s, "fig_regimes_full.png", 0.45, 1.35, 7.9, 3.75);
  card(s, 8.6, 1.4, 4.2, 5.6);
  text(s, "Data (training file)", 8.85, 1.6, 3.8, 0.35, { fontSize: 14, bold: true, color: INK });
  text(s, "57,478 raw bars → 55,575 clean\n1,850 duplicate rows removed\n2,223 trading days, 25 bars each", 8.85, 1.95, 3.8, 0.9, { fontSize: 12 });
  text(s, "Validated against known periods", 8.85, 2.95, 3.8, 0.35, { fontSize: 14, bold: true, color: INK });
  table(s, [["Period", "HMM said"], ["Feb–Apr 2020 crash", "69% high-vol + 21% bear"], ["H1 2022 correction", "65% bear"], ["2023 rally", "72% bull"], ["Sep–Oct 2018 selloff", "46% bear"]],
    8.85, 3.35, 3.75, [1.75, 2.0], { size: 11, headSize: 11, rowH: 0.36 });
  text(s, "Emission change: the spec's 1-day return gave volatility-only states (2023 rally labelled 80% sideways), so the HMM uses the 20-day return + 20-day volatility.", 8.85, 5.35, 3.75, 1.5, { fontSize: 11, color: INK2 });
  text(s, "4 states, full covariance, fitted on 2016–2021 only and frozen. BIC prefers 5 states; 4 kept to match the project's regimes.", 0.6, 5.3, 7.6, 0.8, { fontSize: 12, color: INK2 });
  s.addNotes("The HMM labels line up with real events: the COVID crash is high-volatility, the 2022 correction is bear, the 2023 rally is bull. Using daily returns failed, so we switched to 20-day returns.");
}

// ------------------------------------------------------------------ 12 tuning (native chart)
{
  const s = base("HYPERPARAMETER TUNING");
  const models = ["LSTM", "CNN-BiLSTM-Attention", "Transformer"];
  const arch = ["lstm", "cnn_bilstm_attn", "transformer"];
  const dflt = rj("05_backtest_daily.json").models;
  const tuned = arch.map((a) => rj(`06_tuning_daily_${a}.json`).chosen.mean.macro_f1);
  s.addChart(pres.charts.BAR, [
    { name: "Default (spec)", labels: models, values: arch.map((a) => dflt[a].macro_f1_mean) },
    { name: "Tuned (Optuna)", labels: models, values: tuned },
  ], { x: 0.55, y: 1.45, w: 7.2, h: 5.4, barDir: "col", barGrouping: "clustered", chartColors: ["B7C2CF", NAVY],
    showTitle: true, title: "Validation macro-F1 (5-seed mean)", titleFontSize: 14, titleColor: INK, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontSize: 11, dataLabelColor: INK2,
    valAxisMinVal: 0, valAxisMaxVal: 0.9, valAxisLabelFormatCode: "0.0", valAxisLabelColor: MUTED, catAxisLabelColor: INK2,
    catAxisLabelFontSize: 12, valGridLine: { color: "DDE3EA", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 12, fontFace: FONT });
  card(s, 8.1, 1.5, 4.7, 5.35);
  text(s, "Optuna TPE · 50 trials per model", 8.35, 1.7, 4.3, 0.35, { fontSize: 14, bold: true, color: INK });
  text(s, "Objective = 0.6 × macro-F1 + 0.4 × normalised Sharpe, on validation only", 8.35, 2.05, 4.3, 0.6, { fontSize: 12 });
  text(s, "0.71 → 0.63–0.68", 8.35, 2.8, 4.3, 0.6, { fontSize: 28, bold: true, color: ORANGE });
  text(s, "Best single-seed trials fell this much when re-run on 5 seeds, so the top 3 of every search are re-run and the best mean wins.", 8.35, 3.4, 4.3, 1.0, { fontSize: 12 });
  text(s, "Objective, default → tuned", 8.35, 4.5, 4.3, 0.35, { fontSize: 13, bold: true, color: INK });
  text(s, "LSTM 0.619 → 0.637\nCNN-BiLSTM-Attention 0.647 → 0.680\nTransformer 0.654 → 0.691", 8.35, 4.85, 4.3, 1.0, { fontSize: 12.5 });
  text(s, "Most important: learning rate and dropout. Selected: Transformer.", 8.35, 6.0, 4.3, 0.7, { fontSize: 12, color: GREEN, bold: true });
  s.addNotes("Tuning improved every model. The key methodological point: single-seed winners were lucky; re-running the top three on five seeds gave honest numbers. By our frozen rule, the Transformer was selected.");
}

// ------------------------------------------------------------------ 13 classification (native chart)
{
  const s = base("RESULTS: REGIME CLASSIFICATION");
  const periods = ["Validation*", "Test year", "Fresh data"];
  const f1 = { lstm: [0.687, 0.621, 0.495], cnn: [0.818, 0.580, 0.419], tr: [0.809, 0.836, 0.652] };
  s.addChart(pres.charts.BAR, [
    { name: "LSTM", labels: periods, values: f1.lstm },
    { name: "CNN-BiLSTM-Attention", labels: periods, values: f1.cnn },
    { name: "Transformer", labels: periods, values: f1.tr },
  ], { x: 0.55, y: 1.45, w: 7.6, h: 5.3, barDir: "col", barGrouping: "clustered", chartColors: [BLUE, ORANGE, "1BAF7A"],
    showTitle: true, title: "Macro-F1, 5-seed ensembles", titleFontSize: 14, titleColor: INK, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 10, dataLabelColor: INK2,
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0", valAxisLabelColor: MUTED, catAxisLabelColor: INK2,
    catAxisLabelFontSize: 12, valGridLine: { color: "DDE3EA", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 12, fontFace: FONT });
  text(s, "*Validation also used for early stopping and tuning, so it reads high.", 0.6, 6.85, 7.5, 0.3, { fontSize: 10, color: MUTED });
  const stats = [["87.9%", "Transformer accuracy, test year (May 2024 – Apr 2025)"], ["81.1%", "Same frozen model on 17 months of fresh data"], ["0.84", "Test macro-F1 vs 0.73 for a logistic-regression baseline"]];
  stats.forEach((st, i) => {
    const y = 1.5 + i * 1.78;
    card(s, 8.45, y, 4.35, 1.6);
    text(s, st[0], 8.7, y + 0.15, 3.9, 0.8, { fontSize: 40, bold: true, color: i < 2 ? "1BAF7A" : NAVY, valign: "middle" });
    text(s, st[1], 8.7, y + 0.95, 3.9, 0.6, { fontSize: 12.5 });
  });
  s.addNotes("The Transformer generalises best: 0.84 macro-F1 and 88% accuracy on the test year, 81% on fresh data. The LSTM and CNN drop more on new data.");
}

// ------------------------------------------------------------------ 14 test detail
{
  const s = base("TEST YEAR IN DETAIL");
  img(s, "fig_confusion_test.png", 0.5, 1.45, 4.3, 3.7);
  img(s, "fig_test_timeline.png", 4.95, 1.4, 7.9, 3.9);
  card(s, 0.55, 5.45, 12.25, 1.6);
  text(s, [
    { text: "Recall: bull 0.87 · bear 0.85 · sideways 0.89; only 0.4% of forecasts below 0.5 confidence.", options: { bullet: true, breakLine: true } },
    { text: "The frozen HMM labelled 65% of the test year sideways, including the slow Oct 2024 – Mar 2025 decline, and no high-volatility days.", options: { bullet: true, breakLine: true } },
    { text: "Labels change after the market moves (e.g. 4 June 2024 election crash), so a model that copies them faithfully signals late.", options: { bullet: true } },
  ], 0.85, 5.6, 11.7, 1.4, { fontSize: 13, paraSpaceAfter: 4 });
  s.addNotes("The confusion matrix shows strong recall for all three regimes present. But the labels themselves lag: the crash day is labelled bear only after it happens, which matters for trading.");
}

// ------------------------------------------------------------------ 15 replay
{
  const s = base("WALK-FORWARD REPLAY (15-MIN)");
  const r = rj("09_replay_test.json");
  const k = [["5,800 / 5,800", "bars processed one at a time (uptime 100%)"], [`${Math.round(r.latency_ms.p95)} ms`, "p95 latency per bar (requirement < 2,000 ms)"],
    ["100%", "match with the batch pipeline: no look-ahead"], [`${(100 * r.classification.accuracy).toFixed(1)}%`, "15-min accuracy vs 70.2% on validation"]];
  k.forEach((q, i) => {
    const x = 0.55 + i * 3.1;
    card(s, x, 1.45, 2.9, 1.55);
    text(s, q[0], x + 0.2, 1.55, 2.6, 0.7, { fontSize: 26, bold: true, color: i === 3 ? ORANGE : GREEN, valign: "middle" });
    text(s, q[1], x + 0.2, 2.25, 2.6, 0.7, { fontSize: 11.5 });
  });
  img(s, "fig_replay.png", 0.8, 3.2, 11.7, 3.75);
  text(s, "15-min Transformer trained on a Colab T4 GPU. Every prediction logged to SQLite with confidence; forecasts below 0.5 flagged (16.6%).", 0.6, 7.0, 12.1, 0.4, { fontSize: 11, color: MUTED });
  s.addNotes("Instead of a live Kite feed we replayed the test file bar by bar. The pipeline is fast and exactly matches the batch results. The 15-minute model itself is weaker: 52% accuracy on the test year.");
}

// ------------------------------------------------------------------ 16 trading rules
{
  const s = base("TRADING RULES");
  card(s, 0.55, 1.45, 4.3, 5.5);
  text(s, "Setup (all systems)", 0.8, 1.65, 3.9, 0.35, { fontSize: 15, bold: true, color: INK });
  text(s, [
    { text: "Start Rs 10,00,000; decide at each day's close", options: { bullet: true, breakLine: true } },
    { text: "Nifty 50 ETF: 0.10% per side + Rs 15.93 per sell", options: { bullet: true, breakLine: true } },
    { text: "Idle cash earns 6% a year", options: { bullet: true, breakLine: true } },
    { text: "Rules chosen on validation only, then frozen", options: { bullet: true } },
  ], 0.8, 2.05, 3.9, 2.0, { fontSize: 12.5, paraSpaceAfter: 5 });
  text(s, "Experiment 1: regime rules", 0.8, 4.05, 3.9, 0.35, { fontSize: 15, bold: true, color: INK });
  text(s, "72 combinations per model: which regimes to hold, confirmation days, confidence filter, 5% stop. Best by validation profit with drawdown ≤ buy & hold.", 0.8, 4.45, 3.9, 1.5, { fontSize: 12 });
  text(s, "Experiment 2: probability rulebook (right)", 0.8, 5.95, 3.9, 0.35, { fontSize: 13, bold: true, color: NAVY });
  text(s, "324 settings searched; designed after Exp 1 results, so post-hoc.", 0.8, 6.3, 3.9, 0.55, { fontSize: 11.5 });
  img(s, "fig_rulebook_flow.png", 5.05, 1.6, 7.8, 3.2);
  card(s, 5.1, 5.0, 7.7, 1.95);
  text(s, "Default rulebook", 5.35, 5.15, 7.2, 0.35, { fontSize: 14, bold: true, color: INK });
  text(s, "BUY when P(bull) ≥ 0.60 for 2 days (100% if ≥ 0.75, else 50%) · SELL when P(bear)+P(high-vol) ≥ 0.50 for 2 days · 8% trailing stop · 5-day cooldown · sideways never trades.", 5.35, 5.5, 7.2, 1.3, { fontSize: 13 });
  s.addNotes("Both experiments trade from ten lakh rupees with costs. Experiment 1 maps regimes to positions; Experiment 2 uses the probabilities directly with buy, sell, stop-loss and cooldown rules.");
}

// ------------------------------------------------------------------ 17 trading results test
{
  const s = base("RESULTS: TRADING THE TEST YEAR");
  img(s, "fig_trading_test.png", 0.45, 1.35, 8.1, 3.45);
  table(s, [
    ["Rs 10 lakh became", "Exp 1 rules", "Exp 2 tuned"],
    ["LSTM", "Rs 9,70,051", "Rs 10,21,018"],
    ["CNN-BiLSTM-Attn", "Rs 9,62,903", "Rs 10,06,074"],
    ["Transformer", "Rs 9,29,569", "Rs 10,19,525"],
    ["Buy & hold ETF", "Rs 9,81,776", ""],
    ["Cash at 6%", "Rs 10,55,109", ""],
  ], 8.75, 1.5, 4.05, [1.55, 1.25, 1.25], { size: 11, headSize: 11, rowH: 0.42 });
  img(s, "fig_profit_split.png", 0.45, 4.95, 6.05, 2.4);
  card(s, 6.7, 4.95, 6.1, 2.4);
  text(s, [
    { text: "Exp 1 lost money for every model.", options: { bullet: true, breakLine: true } },
    { text: "Exp 2 ended slightly positive, but trading P&L excluding interest was negative in all 9 versions: the profit was interest on idle cash.", options: { bullet: true, breakLine: true } },
    { text: "No system beat cash at 6%; all had smaller drawdowns than buy & hold (−15.7%).", options: { bullet: true, breakLine: true } },
    { text: "Best classifier (Transformer) traded worst: it copies the lagging labels most faithfully.", options: { bullet: true, bold: true, color: INK } },
  ], 6.95, 5.05, 5.65, 2.25, { fontSize: 12, paraSpaceAfter: 4 });
  s.addNotes("On the test year, regime rules lost money. The probability rulebook ended slightly positive, but the chart below shows every rupee of profit came from interest on cash; the buy and sell decisions themselves lost money.");
}

// ------------------------------------------------------------------ 18 forward test
{
  const s = base("FORWARD TEST ON FRESH DATA");
  img(s, "fig_chained.png", 0.45, 1.35, 8.3, 3.6);
  img(s, "fig_trading_fresh.png", 0.45, 5.0, 8.3, 2.4);
  card(s, 8.95, 1.45, 3.85, 5.55);
  text(s, "8 Apr 2025 – 15 Sep 2026", 9.2, 1.6, 3.4, 0.35, { fontSize: 13, bold: true, color: INK });
  text(s, "354 trading days no model or rule had seen; everything frozen", 9.2, 1.95, 3.4, 0.6, { fontSize: 11.5 });
  text(s, "Rs 11,24,388", 9.2, 2.65, 3.4, 0.6, { fontSize: 26, bold: true, color: BLUE });
  text(s, "CNN-BiLSTM-Attention with Exp 1 rules: beat buy & hold (Rs 10,40,165) and cash (Rs 10,85,297)", 9.2, 3.25, 3.4, 0.95, { fontSize: 11.5 });
  text(s, "0 of 9", 9.2, 4.3, 3.4, 0.6, { fontSize: 26, bold: true, color: ORANGE });
  text(s, "Exp 2 rulebook versions made a profit: the test-year gain did not persist", 9.2, 4.9, 3.4, 0.8, { fontSize: 11.5 });
  text(s, "No realistic system was profitable in both unseen periods.", 9.2, 5.9, 3.4, 0.9, { fontSize: 12.5, bold: true, color: INK });
  s.addNotes("This is the most honest test we have. On data after the test file, the rulebook lost money for every model, while the CNN with Experiment 1 rules did well. Across both periods no realistic system was consistently profitable.");
}

// ------------------------------------------------------------------ 19 working modules
{
  const s = base("WORKING MODULES: DASHBOARD");
  img(s, "dash_regimes.png", 0.5, 1.4, 6.05, 3.78);
  img(s, "dash_trading.png", 6.78, 1.4, 6.05, 3.78);
  card(s, 0.55, 5.4, 12.25, 1.6);
  text(s, [
    { text: "Six pages: Overview · Regimes (HMM vs model forecast, date and regime filters) · Models (tuning, accuracy by period, confusion matrices) · Replay (15-min log) · Trading (equity curves, trade logs with reasons, scorecard) · Method & limitations", options: { bullet: true, breakLine: true } },
    { text: "Read-only: reads saved results and re-simulates frozen rules; nothing is retrained. Run with streamlit run dashboard/app.py", options: { bullet: true } },
  ], 0.85, 5.55, 11.7, 1.4, { fontSize: 13, paraSpaceAfter: 5 });
  s.addNotes("Live demo: open the dashboard, show the Regimes page with the Transformer forecast, then the Trading page switching between the test year and fresh data.");
}

// ------------------------------------------------------------------ 20 plan vs actual
{
  const s = base("PLAN VS ACTUAL");
  img(s, "fig_gantt.png", 0.55, 1.35, 12.2, 5.6);
  text(s, "First pipeline in Weeks 1–5; final regime-classification pipeline, testing, trading, replay, forward test and dashboard completed by Week 7, ahead of the Review 1 plan.", 0.6, 6.95, 12.1, 0.45, { fontSize: 11.5, color: MUTED });
  s.addNotes("We are ahead of the Review 1 plan. Everything planned for weeks 8 to 14 is already done; the black-book report is in progress for Review 3.");
}

// ------------------------------------------------------------------ 21 challenges
{
  const s = base("CHALLENGES & SOLUTIONS");
  table(s, [
    ["CHALLENGE", "WHAT WE FOUND", "HOW WE SOLVED IT"],
    ["Messy vendor data", "1,850 duplicate rows; vendor EMA/Supertrend restart at export chunks; no volume", "Kept the copy continuous with the prior close; recomputed all indicators from OHLC"],
    ["HMM regimes looked wrong", "1-day returns gave volatility-only states (2023 rally = sideways)", "20-day return emission; validated on COVID crash, 2022, 2023"],
    ["Look-ahead in HMM labels", "Smoothed posteriors use future days", "Forward-filtered labels; unit tests prove causality"],
    ["Lucky tuning trials", "Best single seed 0.71 fell to 0.63 on 5 seeds", "Top-3 trials re-run on 5 seeds; best mean wins"],
    ["15-min training too slow on CPU", "~5 hours for 5 seeds", "Colab T4 GPU bundle: ~1–2 min per seed"],
    ["No broker API for live data", "Kite Connect unavailable", "Bar-by-bar replay (identical to batch) + forward test on fresh yfinance data"],
    ["Hindsight in trading rules", "Rulebook designed after seeing test results", "Frozen rules + untouched forward test; reported as post-hoc"],
  ], 0.55, 1.5, 12.25, [2.6, 4.7, 4.95], { size: 11.5, headSize: 12, rowH: 0.66 });
  s.addNotes("The main challenges were data quality, label quality, leakage, seed luck, compute and the missing broker API. Each has a documented fix.");
}

// ------------------------------------------------------------------ 22 contributions
{
  const s = base("INDIVIDUAL CONTRIBUTIONS");
  ["VISHAL SINGH"].forEach((n) => {
    const x = 4.7;
    card(s, x, 1.6, 3.95, 5.2);
    text(s, n, x + 0.25, 1.85, 3.5, 0.45, { fontSize: 16, bold: true, color: INK });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.25, y: 2.45, w: 3.45, h: 4.1, fill: { color: "FFF4C2" }, line: { color: "E5C75A", width: 0.75, dashType: "dash" } });
    text(s, "[To be filled by the team]\n\nModules owned\nKey tasks completed\nTools used", x + 0.45, 2.65, 3.1, 3.7, { fontSize: 13, color: "7A6200" });
  });
  s.addNotes("Fill in each member's modules before presenting (for example: data and features, HMM and models, tuning, trading and dashboard).");
}

// ------------------------------------------------------------------ 23 next steps
{
  const s = base("NEXT STEPS & FUTURE SCOPE");
  const steps = [["Weeks 8–9", "Forward-looking labels", "Label regimes by the next 20 days' return and volatility to remove label lag; evaluate on validation only"],
    ["Weeks 9–11", "Walk-forward retraining", "Yearly retrain and trade the following year for several out-of-sample years; tune the 15-min model"],
    ["Weeks 11–13", "Rulebook revision", "Trend overlay and re-entry rules chosen on validation; re-run the frozen forward test"],
    ["Weeks 14–15", "Delivery", "Black-book report, dashboard polish, final presentation and viva"]];
  steps.forEach((st, i) => {
    const x = 0.55 + i * 3.1;
    card(s, x, 1.5, 2.95, 3.0);
    text(s, st[0], x + 0.2, 1.65, 2.6, 0.35, { fontSize: 13, bold: true, color: BLUE });
    text(s, st[1], x + 0.2, 2.0, 2.6, 0.7, { fontSize: 15, bold: true, color: INK });
    text(s, st[2], x + 0.2, 2.7, 2.6, 1.7, { fontSize: 12 });
  });
  card(s, 0.55, 4.75, 12.25, 2.25, "EEF6F1", 5);
  text(s, "Future scope", 0.85, 4.9, 11.7, 0.4, { fontSize: 15, bold: true, color: GREEN });
  text(s, [
    { text: "Live paper trading on a broker API feed once access is available", options: { bullet: true, breakLine: true } },
    { text: "Add futures volume and India VIX features; probability calibration and confidence-based position sizing", options: { bullet: true, breakLine: true } },
    { text: "Extend to Bank Nifty and other indices; compare with a regime-aware LightGBM baseline [11]", options: { bullet: true } },
  ], 0.85, 5.3, 11.7, 1.6, { fontSize: 13, paraSpaceAfter: 5 });
  s.addNotes("The biggest lesson is that lagging labels limit trading value, so the next phase fixes the labels first, then tests across many years instead of two.");
}

// ------------------------------------------------------------------ 24-25 references
const refs = [
  "[1] Y. Yuan and G. Mitra, \"Market Regime Identification Using Hidden Markov Models,\" SSRN, 2016.",
  "[2] W. Lu, J. Li, Y. Li, A. Sun and J. Wang, \"A CNN-BiLSTM-AM method for stock price prediction,\" Neural Computing and Applications, Springer, 2020.",
  "[3] M. Al Ridhawi, M. Haj Ali and H. Al Osman, \"Adaptive Regime-Aware Stock Price Prediction Using Autoencoder-Gated Dual Node Transformers with Reinforcement Learning Control,\" arXiv:2603.19136, 2026.",
  "[4] J. Xiao, S. Bi and T. Deng, \"Comparative Analysis of LSTM, GRU, and Transformer Models for Stock Price Prediction,\" arXiv:2411.05790, 2024.",
  "[5] \"Integrating deep learning and econometrics for stock price prediction: A comprehensive comparison of LSTM, transformers, and traditional time series models,\" ScienceDirect, 2025.",
  "[6] \"Impact of Hyperparameter Optimisation Techniques in Deep Learning-based Investment Predictions: An Indian ETF-based analysis,\" Research Square (preprint), 2025.",
  "[7] \"Stock Market Analysis and Prediction for Nifty50 using LSTM Deep Learning Approach,\" IEEE Xplore, 2022.",
  "[8] \"Comparative Analysis of Deep Learning Models for Stock Price Prediction in the Indian Market,\" MDPI, 2024.",
  "[9] \"An efficient real-time stock prediction exploiting incremental learning and deep learning,\" Evolving Systems, Springer, 2022.",
  "[10] R. G. Mishra, D. Sharma, M. Gadhavi, S. Pant and A. Kumar, \"A Deep Reinforcement Learning Framework for Strategic Indian NIFTY 50 Index Trading,\" AI, vol. 6, no. 8, p. 183, 2025.",
  "[11] A. Pagliaro, \"Regime-Aware LightGBM for Stock Market Forecasting: A Validated Walk-Forward Framework with Statistical Rigor and Explainable AI Analysis,\" Electronics, vol. 15, no. 6, p. 1334, 2026.",
  "[12] \"Machine Learning-Driven Market Regime Analysis in Equity Markets: A Gaussian Hidden Markov Model Approach,\" ResearchGate, 2025.",
  "[13] J. D. Hamilton, \"A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle,\" Econometrica, vol. 57, no. 2, pp. 357–384, 1989.",
  "[14] L. R. Rabiner, \"A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition,\" Proc. IEEE, vol. 77, no. 2, pp. 257–286, 1989.",
  "[15] S. Hochreiter and J. Schmidhuber, \"Long Short-Term Memory,\" Neural Computation, vol. 9, no. 8, pp. 1735–1780, 1997.",
  "[16] D. Bahdanau, K. Cho and Y. Bengio, \"Neural Machine Translation by Jointly Learning to Align and Translate,\" ICLR, 2015.",
  "[17] A. Vaswani et al., \"Attention Is All You Need,\" Advances in Neural Information Processing Systems 30, pp. 5998–6008, 2017.",
  "[18] J. Bergstra, R. Bardenet, Y. Bengio and B. Kégl, \"Algorithms for Hyper-Parameter Optimization,\" Advances in Neural Information Processing Systems 24, pp. 2546–2554, 2011.",
  "[19] T. Akiba, S. Sano, T. Yanase, T. Ohta and M. Koyama, \"Optuna: A Next-generation Hyperparameter Optimization Framework,\" Proc. ACM SIGKDD, pp. 2623–2631, 2019.",
  "[20] D. H. Bailey, J. M. Borwein, M. López de Prado and Q. J. Zhu, \"Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance,\" Notices of the AMS, vol. 61, no. 5, pp. 458–471, 2014.",
  "[21] IEEE Std 830-1998, \"IEEE Recommended Practice for Software Requirements Specifications,\" IEEE, 1998.",
];
[[0, 11, "REFERENCES"], [11, 21, "REFERENCES (CONTD.)"]].forEach(([a, b, t]) => {
  const s = base(t);
  card(s, 0.55, 1.45, 12.25, 5.6);
  text(s, refs.slice(a, b).map((r, i, arr) => ({ text: r, options: { breakLine: i < arr.length - 1 } })), 0.85, 1.65, 11.7, 5.3, { fontSize: 12, paraSpaceAfter: 6, color: INK2 });
});

// ------------------------------------------------------------------ 26 thank you
{
  const s = base(null);
  text(s, "THANK YOU", 0.5, 2.3, 12.3, 1.6, { fontSize: 80, bold: true, color: INK, align: "center", valign: "middle" });
  text(s, "Questions welcome", 0.5, 3.9, 12.3, 0.6, { fontSize: 22, color: INK2, align: "center" });
  text(s, "Group 17  ·  Vishal Singh  ·  Mentor: Dr. Raj Gaurav Mishra", 0.5, 6.4, 12.3, 0.5, { fontSize: 14, color: INK2, align: "center" });
}

pres.writeFile({ fileName: OUT }).then((f) => console.log("wrote", f));
