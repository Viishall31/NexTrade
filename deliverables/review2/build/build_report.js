// NexTrade — Review 2 interim report (docx-js), formatted per MPSTME Annexure A.8.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, Header, Footer, PageNumber, NumberFormat, TabStopType, TableOfContents, PageBreak,
  SequentialIdentifier, LevelFormat, SectionType,
} = require("docx");

const FIG = path.join(__dirname, "..", "figures");
const OUT = path.join(__dirname, "..", "NexTrade_Review2_Interim_Report.docx");
const TITLE = "NexTrade: A Regime-Aware AI Trading System for the Nifty 50";
const YEAR = "Academic Year 2026-27";
const TEXT_W = 11906 - 2160 - 1440; // A4 width minus 1.5" left and 1" right margins (DXA)
const FONT = "Times New Roman";

// ------------------------------------------------------------------ helpers
const r = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
const ph = (t) => new TextRun({ text: t, font: FONT, highlight: "yellow" });
function P(children, o = {}) {
  if (typeof children === "string") children = [r(children)];
  return new Paragraph({ children, alignment: o.align || AlignmentType.JUSTIFIED, spacing: { line: 360, after: o.after ?? 120, before: o.before ?? 0 }, ...o.extra });
}
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [r(t)], spacing: { after: 240 } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [r(t)], spacing: { before: 240, after: 120 } });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [r(t)], spacing: { before: 180, after: 80 } });
const B = (t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: typeof t === "string" ? [r(t)] : t, spacing: { line: 360, after: 60 }, alignment: AlignmentType.JUSTIFIED });
const center = (children, o = {}) => new Paragraph({ children, alignment: AlignmentType.CENTER, spacing: { line: 360, after: o.after ?? 120, before: o.before ?? 0 } });

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}
function figure(file, caption, widthIn = 5.75) {
  const { w, h, data } = pngSize(path.join(FIG, file));
  const px = Math.round(widthIn * 96);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
      children: [new ImageRun({ type: "png", data, transformation: { width: px, height: Math.round(px * h / w) } })] }),
    new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [r("Figure ", { size: 20 }), new SequentialIdentifier("Figure"), r(": " + caption, { size: 20 })] }),
  ];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
function table(caption, rows, widthsIn, o = {}) {
  const total = widthsIn.reduce((a, b) => a + b, 0);
  const cols = widthsIn.map((w) => Math.round((w / total) * TEXT_W));
  const fix = TEXT_W - cols.reduce((a, b) => a + b, 0);
  cols[cols.length - 1] += fix;
  const mk = (cells, head) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    width: { size: cols[i], type: WidthType.DXA }, borders: { top: border, bottom: border, left: border, right: border },
    shading: head ? { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: (Array.isArray(c) ? c : [c]).map((line) => new Paragraph({ spacing: { line: 240, after: 0 },
      alignment: typeof line === "string" && /^[−\-+]?(Rs )?[\d,.%−]+( L)?$/.test(line.trim()) ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: typeof line === "string" ? [r(line, { size: o.size || 20, bold: head })] : line })),
  })) });
  return [
    new Paragraph({ style: "Caption", alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 }, keepNext: true,
      children: o.numbered === false ? [r(caption, { size: 20 })] : [r("Table ", { size: 20 }), new SequentialIdentifier("Table"), r(": " + caption, { size: 20 })] }),
    new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: cols, rows: rows.map((row, i) => mk(row, i === 0)) }),
    new Paragraph({ spacing: { after: 160 }, children: [] }),
  ];
}
const summary = (t) => P([r("Summary. ", { bold: true }), r(t)], { before: 120 });

// ------------------------------------------------------------------ content
const titlePage = [
  center([r(TITLE, { bold: true, size: 36 })], { before: 1200, after: 240 }),
  center([r("HMM Regime Detection and a Comparison of LSTM, CNN-BiLSTM-Attention and Transformer Models", { size: 26 })], { after: 480 }),
  center([r("Interim Project Report (Review 2: Midterm)", { bold: true, size: 26 })]),
  center([r("submitted in the partial fulfilment of", { size: 24 })]),
  center([ph("[Name of the Program]")]),
  center([r("in", { size: 24 })]),
  center([ph("[Name of the Stream]")], { after: 360 }),
  center([r("by", { size: 24 })]),
  center([r("Vishal Singh (", { size: 24 }), ph("Roll No."), r(")", { size: 24 })], { after: 360 }),
  center([r("Under the supervision of", { size: 24 })]),
  center([r("Dr. Raj Gaurav Mishra", { bold: true, size: 24 })], { after: 0 }),
  center([r("(", { size: 24 }), ph("Designation, Name of the Department"), r(", MPSTME)", { size: 24 })], { after: 720 }),
  center([r("SVKM's NMIMS University (Deemed-to-be University)", { bold: true })], { after: 0 }),
  center([r("Mukesh Patel School of Technology Management & Engineering (MPSTME)", { bold: true })], { after: 0 }),
  center([r("Vile Parle (W), Mumbai-56")], { after: 0 }),
  center([r(YEAR)]),
];

const certificate = [
  center([r("SVKM's NMIMS University", { bold: true, size: 28 })], { before: 240, after: 0 }),
  center([r("(Deemed-to-be University)")], { after: 0 }),
  center([r("MUKESH PATEL SCHOOL OF TECHNOLOGY MANAGEMENT & ENGINEERING (MPSTME)", { bold: true })], { after: 0 }),
  center([r("Vile Parle (W), Mumbai-56")], { after: 0 }),
  center([r(YEAR)], { after: 480 }),
  center([r("CERTIFICATE", { bold: true, size: 32 })], { after: 360 }),
  P([r("This is to certify that the project entitled “" + TITLE + "” has been done by Mr. Vishal Singh under my guidance and supervision and has been submitted in partial fulfilment of the degree of "),
     ph("[Name of the Program]"), r(" in "), ph("[Name of the Stream]"), r(" of MPSTME, SVKM's NMIMS (Deemed-to-be University), Mumbai, India.")]),
  P([r("")], { after: 720 }),
  new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: TEXT_W }], spacing: { line: 360 },
    children: [r("_______________________"), r("\t_______________________")] }),
  new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: TEXT_W }], spacing: { line: 360 },
    children: [r("Project Mentor: Dr. Raj Gaurav Mishra"), r("\tExaminer: "), ph("[Name and Signature]")] }),
  new Paragraph({ spacing: { line: 360 }, children: [r("(Internal Guide)")] }),
  P([r("Date: "), ph("[DD/MM/YYYY]")], { before: 360, align: AlignmentType.LEFT }),
  P([r("Place: Mumbai")], { align: AlignmentType.LEFT }),
  new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 480 }, children: [r("_______________________")] }),
  new Paragraph({ alignment: AlignmentType.RIGHT, children: [r("HoD: "), ph("[Name and Signature]")] }),
];

const acknowledgement = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("ACKNOWLEDGEMENT")], spacing: { after: 240 } }),
  P("We express our sincere gratitude to our project mentor, Dr. Raj Gaurav Mishra, for his guidance, encouragement and constructive feedback throughout the development of NexTrade. His work on deep reinforcement learning for Nifty 50 trading shaped the direction of this project."),
  P("We thank the faculty members of MPSTME who reviewed our progress, and the Department for providing the resources and schedule that made this work possible. We also thank our families and friends for their constant support."),
  ...table("Student details", [["Name", "Roll No.", "SAP ID"], ["Vishal Singh", [[ph("[Roll No.]")]], [[ph("[SAP ID]")]]]], [2.5, 1.6, 1.6], { numbered: false }),
];

const abstract = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("ABSTRACT")], spacing: { after: 240 } }),
  P("Financial markets move through distinct regimes (rising, falling, range-bound and highly volatile phases), and a trading approach that ignores the prevailing regime tends to generalise poorly. Existing studies either detect regimes without testing their trading value, or compare deep-learning models on price-prediction error without regime information. This project, NexTrade, builds and evaluates a complete regime-aware pipeline for the Nifty 50 index."),
  P("Fifteen-minute Nifty 50 OHLC data (April 2015 to April 2025) were cleaned, including the removal of 1,850 duplicated rows, and resampled to daily bars. Thirteen causal technical indicators were computed. A four-state Gaussian Hidden Markov Model, fitted on 2016 to 2021 data and frozen, labels each trading day as bull, bear, sideways or high-volatility using forward-filtered posteriors so that no label depends on later data. Three architectures (LSTM, CNN-BiLSTM-Attention and a Transformer encoder) were trained to forecast the next day's regime from a 30-day window, tuned with Optuna (50 trials each, with the top trials re-run on five seeds), and the Transformer was selected on validation data before testing."),
  P("On the held-out test year (May 2024 to April 2025) the Transformer ensemble reached 87.9% accuracy and a macro-F1 of 0.84, and 81.1% accuracy on 17 months of fresh data. A bar-by-bar replay of 5,800 fifteen-minute bars reproduced the batch pipeline exactly with a p95 latency of 163 ms. Trading from Rs 10 lakh with rules frozen on validation data did not reliably beat a 6% liquid fund: regime rules lost money in the test year, a probability rulebook ended slightly positive only through interest on idle cash, and that result did not persist on fresh data. Every realistic system did reduce drawdown relative to buy-and-hold. The main finding is that HMM regimes identified after the move are accurately learnable but lag turning points, so better classification did not translate into better trading. Forward-looking regime labels and walk-forward retraining are planned for the remaining weeks."),
  P([r("Keywords: ", { bold: true }), r("market regime detection, Hidden Markov Model, LSTM, CNN-BiLSTM-Attention, Transformer, Optuna, Nifty 50, backtesting")]),
];

const lists = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("TABLE OF CONTENTS")], spacing: { after: 240 } }),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("LIST OF FIGURES")], spacing: { after: 240 } }),
  new TableOfContents("List of Figures", { hyperlink: true, captionLabel: "Figure" }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("LIST OF TABLES")], spacing: { after: 240 } }),
  new TableOfContents("List of Tables", { hyperlink: true, captionLabel: "Table" }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, alignment: AlignmentType.CENTER, children: [r("ABBREVIATIONS")], spacing: { after: 240 } }),
  ...table("Abbreviations", [["Abbreviation", "Meaning"],
    ["ADX", "Average Directional Index"], ["ATR", "Average True Range"], ["BIC", "Bayesian Information Criterion"],
    ["BiLSTM", "Bidirectional Long Short-Term Memory"], ["CNN", "Convolutional Neural Network"], ["DD", "Drawdown"],
    ["EMA", "Exponential Moving Average"], ["ETF", "Exchange-Traded Fund"], ["F1", "Harmonic mean of precision and recall"],
    ["GPU", "Graphics Processing Unit"], ["HMM", "Hidden Markov Model"], ["LSTM", "Long Short-Term Memory"],
    ["MACD", "Moving Average Convergence Divergence"], ["NSE", "National Stock Exchange of India"], ["OHLC", "Open, High, Low, Close"],
    ["P&L", "Profit and Loss"], ["RSI", "Relative Strength Index"], ["SRS", "Software Requirements Specification"],
    ["TPE", "Tree-structured Parzen Estimator"]], [1.6, 4.2], { numbered: false }),
];

// ------------------------------------------------------------------ Chapter 1
const ch1 = [
  H1("Chapter 1: Introduction"),
  P("This chapter introduces the market-regime problem that NexTrade addresses, the motivation and scope of the work, the problem statement and objectives, the salient contributions made up to Review 2, and the organisation of the rest of the report."),
  H2("1.1 Background of the Project Topic"),
  P("Equity indices do not behave uniformly over time. Periods of steady appreciation, sharp declines, range-bound drift and volatility clusters alternate, and the statistical properties of returns change between them. Regime-switching models formalise this idea: Hamilton's Markov-switching framework [13] treats the observed series as generated by a small number of hidden states with their own dynamics, and the Hidden Markov Model (HMM) tutorial by Rabiner [14] describes the inference machinery used to estimate those states. In finance, regime models have been used for asset allocation [1] and, more recently, for equity-market regime analysis with Gaussian HMMs [12]."),
  P("In parallel, deep sequence models have become standard tools for learning from market time series. Long Short-Term Memory networks [15], hybrid convolutional and recurrent architectures with attention [2], [16] and Transformer encoders [17] have all been applied to stock prediction [4], [5], [7], [8]. The Nifty 50, India's benchmark index of fifty large companies, has been studied with LSTMs [7] and with deep reinforcement learning on 15-minute data [10]."),
  H2("1.2 Motivation and Scope of the Report"),
  P("A regime label is only useful to an investor if it can be forecast before the market moves and if acting on it improves outcomes after costs. Most regime studies stop at labelling the past [1], [12], while most deep-learning studies measure price-prediction error on historical data [4], [5], [8]. There is little evidence on whether modern architectures can forecast Nifty 50 regimes out of sample, which architecture does so best, and whether the forecasts are worth trading."),
  P("This interim report covers the work completed up to Review 2 (Week 7): data preparation, HMM regime labelling, training and tuning of three architectures, model selection, a one-time test, a bar-by-bar 15-minute replay, rule-based trading in rupees, a forward test on fresh data and an interactive dashboard. Real-money trading, derivatives execution and broker integration are outside the scope."),
  H2("1.3 Problem Statement"),
  P([r("Problem statement. ", { bold: true }), r("Given only past Nifty 50 price data and technical indicators, forecast the market regime (bull, bear, sideways or high-volatility) of the next trading day; compare LSTM, CNN-BiLSTM-Attention and Transformer models fairly on this task; and determine whether trading decisions based on the forecasts are profitable on data never used for any design decision.")]),
  P("The project objectives, as approved after Review 1, are:"),
  B([r("Regime labelling and model training: ", { bold: true }), r("generate regime labels with a Gaussian HMM and train deep-learning models on time-ordered historical data.")]),
  B([r("Model development and comparison: ", { bold: true }), r("implement and compare CNN-BiLSTM-Attention, LSTM and Transformer models under identical splits and metrics.")]),
  B([r("Hyperparameter optimisation: ", { bold: true }), r("tune the models with Optuna to improve regime accuracy and trading performance, selecting on validation data only.")]),
  B([r("Validation: ", { bold: true }), r("validate the best model on unseen and 15-minute data using classification and trading-performance metrics.")]),
  H2("1.4 Salient Contributions"),
  B("A leakage-controlled pipeline: time-ordered splits, a scaler and HMM fitted on training data only, forward-filtered (causal) regime labels, and 52 automated tests that verify these properties."),
  B("A fair three-way comparison of LSTM, CNN-BiLSTM-Attention and Transformer classifiers on identical data, tuned with 50 Optuna trials each and re-run on five seeds to remove seed luck."),
  B("A one-time evaluation on the held-out test year, a bar-by-bar replay proven identical to the batch pipeline, and a forward test on 17 months of fresh data with every model and rule frozen."),
  B("A rupee-denominated trading study (Rs 10 lakh, costs and cash interest) that separates trading profit from interest income, showing that accurate regime classification did not produce reliable trading profit."),
  B("A Streamlit dashboard that presents regimes, model comparisons, replay logs and trading results to non-technical reviewers."),
  H2("1.5 Organization of the Report"),
  P("Chapter 2 reviews the literature and identifies the research gap. Chapter 3 describes the methodology and implementation. Chapter 4 presents the results and their analysis. Chapter 5 discusses advantages, limitations and applications. Chapter 6 concludes the report with progress against the plan and the future scope. Appendices contain flowcharts, data sheets and the list of software components."),
  summary("Market regimes change the behaviour of the Nifty 50. NexTrade tests whether deep models can forecast those regimes and whether the forecasts are tradable, using a strictly leakage-controlled evaluation."),
];

// ------------------------------------------------------------------ Chapter 2
const lit = [["Ref.", "Study", "Method and key points", "Gap relevant to NexTrade"],
  ["[1]", "Yuan and Mitra, SSRN, 2016", "Gaussian HMM on FTSE 100 and Euro Stoxx 50 returns; captures fat tails and volatility clustering", "Detection only; no classifier, trading test or Indian data"],
  ["[2]", "Lu et al., Neural Comput. Appl., 2020", "CNN-BiLSTM with attention outperforms LSTM, MLP and SVM", "Price regression; no regimes; no Transformer"],
  ["[3]", "Al Ridhawi et al., arXiv, 2026", "Autoencoder-gated dual-node Transformers with RL control for regime shifts", "Very heavy; US only; not a labelled classification task"],
  ["[4]", "Xiao, Bi and Deng, arXiv, 2024", "LSTM vs GRU vs Transformer on Tesla prices", "Single US stock; regression; no regimes or tuning"],
  ["[5]", "ScienceDirect, 2025", "LSTM and Transformers vs econometric models", "No CNN-BiLSTM-Attention; no regimes; no Indian data"],
  ["[6]", "Research Square, 2025", "Grid, Bayesian and Optuna TPE tuning on Nifty BeES; TPE best", "Tunes only LSTM and 1D-CNN for price prediction"],
  ["[7]", "IEEE Xplore, 2022", "LSTM on Nifty 50 daily prices", "Single model; no regimes, tuning or intraday data"],
  ["[8]", "MDPI, 2024", "RNN, LSTM, CNN, GRU, Attention-LSTM on Indian stocks", "Error metrics only; no Transformer; no trading"],
  ["[9]", "Evolving Systems, 2022", "Incremental learning with streaming data", "Not regime classification; not Nifty 15-min"],
  ["[10]", "Mishra et al., AI, 2025", "DQN, DDQN and Dueling DDQN on 15-min Nifty 50 data", "Single fixed policy; no regime classifier"],
  ["[11]", "Pagliaro, Electronics, 2026", "Regime-aware LightGBM with walk-forward validation", "Classifier only; no deep sequence comparison"],
  ["[12]", "Gaussian HMM regime analysis, 2025", "Multivariate HMM with PCA identifies equity regimes", "Detection only; no forecasting or trading"],
];
const ch2 = [
  H1("Chapter 2: Literature Survey"),
  P("This chapter reviews the research on market regimes, deep sequence models for markets, hyperparameter optimisation and evaluation practice, and ends by identifying the gap that defines the NexTrade problem statement."),
  H2("2.1 Introduction to the Overall Topic"),
  P("Regime-switching models originate with Hamilton [13], who modelled macroeconomic series as switching between latent states governed by a Markov chain. HMM estimation relies on the forward-backward and Viterbi algorithms described by Rabiner [14]. The forward pass alone yields filtered state probabilities that use only past observations, which is the property needed for any real-time use. Regime ideas have since been applied to asset allocation and equity indices [1], [12], and combined with machine-learning classifiers under walk-forward validation [11]."),
  P("Deep learning supplies the forecasting component. LSTMs [15] address vanishing gradients in recurrent networks; attention mechanisms [16] let a model weight informative time steps; and Transformers [17] replace recurrence with multi-head self-attention. Hybrid CNN-BiLSTM-attention models have shown strong results on stock data [2], and comparisons of LSTM, GRU and Transformer models exist for individual US stocks [4] and against econometric baselines [5]. Model quality depends heavily on hyperparameters: the Tree-structured Parzen Estimator [18], implemented in Optuna [19], performed best among tuning methods on Indian ETF data [6]. Finally, backtest overfitting [20] is a well-documented risk: selecting among many strategies on the same history inflates apparent performance, which motivates strict out-of-sample testing."),
  H2("2.2 Survey of Related Work"),
  P("Regime detection. Yuan and Mitra [1] fitted Gaussian HMMs to European index returns and showed that the states capture fat tails and volatility clustering better than a geometric Brownian motion, supporting factor-switching strategies. A 2025 study [12] applied multivariate Gaussian HMMs with PCA to equity markets and identified interpretable regimes. Both stop at describing the past and do not forecast regimes or test trading decisions. Pagliaro [11] conditioned a LightGBM forecaster on rolling HMM regimes with walk-forward validation, but did not compare deep sequence architectures."),
  P("Deep models for markets. Lu et al. [2] combined convolutional feature extraction, a bidirectional LSTM and attention, outperforming LSTM, MLP and SVM baselines for price prediction. Al Ridhawi et al. [3] proposed autoencoder-gated dual-node Transformers with reinforcement-learning control to adapt to regime shifts; the design is powerful but heavy and evaluated on US data. Xiao, Bi and Deng [4] compared LSTM, GRU and Transformer models on a single US stock, and a 2025 study [5] compared LSTM and Transformer models with econometric baselines. For Indian markets, an LSTM was applied to Nifty 50 prices [7], and several deep architectures were compared on Indian equities using error metrics [8]. None of these frames the task as regime classification or evaluates trading outcomes on unseen data."),
  P("Tuning, real-time use and Indian trading. The Research Square study [6] compared grid search, Bayesian optimisation and Optuna samplers on Nifty BeES and found TPE best, but tuned only LSTM and 1D-CNN models. An incremental-learning framework [9] updated models with streaming data for real-time prediction, without regime classification. Mishra et al. [10] benchmarked DQN, DDQN and Dueling DDQN agents on a decade of 15-minute Nifty 50 data with technical indicators; the agents are single fixed policies with no explicit regime classifier, which NexTrade complements with a regime layer and a supervised three-model comparison. Table 1 summarises the reviewed studies."),
  ...table("Comparison of reviewed literature", lit, [0.45, 1.35, 2.15, 1.85], { size: 18 }),
  H2("2.3 Research Gap and Problem Definition"),
  P("Four gaps emerge. First, regime studies [1], [11], [12] label or condition on regimes but do not forecast them with deep sequence models or test the trading value of those forecasts. Second, deep-learning comparisons [2], [4], [5], [8] include at most two of LSTM, CNN-BiLSTM-Attention and Transformer, and use price error rather than out-of-sample trading results. Third, tuning studies [6] cover only simpler architectures. Fourth, Indian intraday work [10] relies on single fixed policies without a regime classifier. Given the risk of backtest overfitting [20], any claim of trading value also needs a test on data untouched by design decisions."),
  P("These gaps define the NexTrade problem: forecast Nifty 50 regimes with causal HMM labels, compare the three architectures fairly with tuning, select on validation only, and test classification and trading value on held-out and fresh data."),
  summary("Existing work either labels regimes or predicts prices, but does not forecast regimes with a fair three-architecture comparison and test the trading value out of sample. NexTrade is designed to fill that gap."),
];

// ------------------------------------------------------------------ Chapter 3
const ch3 = [
  H1("Chapter 3: Methodology and Implementation"),
  P("This chapter describes the NexTrade system: its block diagram, hardware and software, and each stage from data cleaning to the dashboard. All parameters are stored in a single configuration file, every run is seeded and logged, and selections are frozen in timestamped files before any test evaluation."),
  H2("3.1 Block Diagram"),
  P("Figure 1 shows the twelve stages of the pipeline. Stages 1 to 4 prepare data and regime labels, stages 5 to 8 build, tune and select the classifiers, and stages 9 to 12 validate, trade and present the results."),
  ...figure("fig_architecture.png", "NexTrade system block diagram"),
  H2("3.2 Hardware Description"),
  P("NexTrade is a software system; no custom hardware is involved. Development and all daily-model experiments ran on a laptop CPU, and the 15-minute model was trained on a cloud GPU (Table 2)."),
  ...table("Hardware used", [["Component", "Specification", "Used for"],
    ["Laptop CPU", "12 logical cores, Intel Iris Xe graphics", "Data pipeline, HMM, daily models, Optuna tuning, replay, dashboard"],
    ["Memory", "8 GB RAM", "All local processing"],
    ["Cloud GPU", "Google Colab NVIDIA T4", "Training the 15-minute Transformer (about 1 to 2 minutes per seed)"],
    ["Operating system", "Windows 11", "Development environment"]], [1.3, 2.2, 2.6]),
  H2("3.3 Software Description"),
  ...table("Software tools and libraries", [["Category", "Tools"],
    ["Language", "Python 3.13"], ["Data handling", "pandas, NumPy, PyArrow; yfinance for fresh daily data"],
    ["Regime labelling", "hmmlearn (Gaussian HMM); SciPy for the forward filter"],
    ["Deep learning", "PyTorch 2.14 (CPU locally, CUDA on Colab)"], ["Tuning and metrics", "Optuna 4.9 (TPE sampler, median pruner); scikit-learn"],
    ["Visualisation", "Matplotlib; Streamlit and Plotly dashboard"], ["Storage and logging", "Parquet files, SQLite prediction log, JSONL experiment log"],
    ["Quality", "pytest (52 tests), configuration-driven and seeded scripts"]], [1.6, 4.4]),
  H2("3.4 Data Pipeline and Cleaning"),
  P("The training file contains 57,478 fifteen-minute Nifty 50 bars from April 2015 to April 2024; the test file contains 6,014 bars from May 2024 to April 2025. An audit found that the vendor export overlapped at chunk boundaries: 74 trading days appeared twice, and the later copy's 09:15 bar had a corrupted open (about 55 points from the prior close versus under 1 point for the first copy). The vendor's EMA and Supertrend columns restarted at each chunk and were discarded. The cleaning rules and outcomes are listed in Table 4. Clean bars were resampled to daily OHLC bars for the daily models and the HMM."),
  ...table("Data cleaning rules and results (training file)", [["Rule", "Result"],
    ["Remove duplicate timestamps (keep first copy)", "1,850 rows removed across 74 days"],
    ["Keep only regular session bars (09:15 to 15:15)", "42 out-of-session rows removed (Muhurat and extended sessions)"],
    ["Forward-fill single missing bars; drop days with longer gaps", "1 bar filled; 3 partial days dropped"],
    ["Validate OHLC consistency and positive prices", "0 violations"],
    ["Final dataset", "55,575 bars; 2,223 trading days with 25 bars each"]], [3.2, 2.8]),
  H2("3.5 Feature Engineering"),
  P("Thirteen causal indicators were computed from OHLC only, because the index data carry no volume (Table 5). MACD values are divided by price so that 2016 and 2024 levels are comparable, and the first 200 bars are discarded until the 200-period EMA has settled. Features are z-scored with means and standard deviations from the training split only."),
  ...table("Model input features", [["Indicator", "Parameters", "Features"],
    ["RSI", "14 periods (Wilder)", "RSI"], ["MACD", "12, 26, 9", "MACD line, signal, histogram (divided by price)"],
    ["EMA ratio", "20, 50, 200", "close / EMA (3 features)"], ["ATR", "14 periods", "ATR / close"],
    ["ADX", "14 periods", "ADX"], ["Bollinger Bands", "20 periods, 2 std", "%B, bandwidth"], ["Stochastic RSI", "14, 3, 3", "%K, %D"]], [1.6, 1.6, 2.8]),
  H2("3.6 HMM Regime Labelling"),
  P("A four-state Gaussian HMM with full covariance is fitted to two daily observations: the trailing 20-day log return and the 20-day annualised realised volatility, both standardised with training statistics. The model is fitted on February 2016 to December 2021 with ten random restarts, and the highest-likelihood fit is frozen. Labels use the forward (filtered) posterior, computed recursively as"),
  center([r("αₜ(j) = [ Σᵢ αₜ₋₁(i) aᵢⱼ ] bⱼ(oₜ),   p(sₜ = j | o₁..oₜ) = αₜ(j) / Σₖ αₜ(k)", { italics: true })]),
  P("where a are transition probabilities and b are Gaussian emission densities [14]. Unlike smoothed posteriors, these probabilities never use later days, so historical and live labels are produced identically; a unit test verifies that altering future data leaves past labels unchanged. States are named from training statistics: the highest-volatility state is high-volatility; of the remaining three, the highest mean return is bull, the lowest is bear, and the other is sideways."),
  H2("3.7 Sequence Construction and Model Architectures"),
  P("Each sample is a window of the last 30 trading days of the 13 scaled features; the target is the HMM regime of the following day. All three models share this input, a four-class softmax output, class-weighted cross-entropy, the Adam optimiser and early stopping on validation macro-F1 with patience 10. Figure 2 shows the tuned architectures."),
  ...figure("fig_models.png", "Tuned model architectures"),
  B([r("LSTM [15]: ", { bold: true }), r("stacked LSTM layers read the window step by step; the final hidden state feeds a dense layer.")]),
  B([r("CNN-BiLSTM-Attention [2], [16]: ", { bold: true }), r("causal 1-D convolutions extract local patterns, a bidirectional LSTM models the sequence, and additive attention weights the time steps.")]),
  B([r("Transformer encoder [17]: ", { bold: true }), r("a linear projection and sinusoidal positions feed self-attention encoder layers, followed by mean pooling.")]),
  H2("3.8 Hyperparameter Tuning and Model Selection"),
  P("Each architecture was tuned independently with Optuna [19] using the TPE sampler [18] and a median pruner, for 50 trials. The objective, computed on validation data only, is 0.6 times macro-F1 plus 0.4 times the normalised Sharpe ratio of a regime-conditioned strategy. Because seed variation alone moved macro-F1 by about 0.05, the top three trials of every search were re-run with five seeds and the configuration with the best mean objective was kept (Table 6)."),
  ...table("Optuna search space", [["Hyperparameter", "Range", "Applies to"],
    ["Learning rate", "log-uniform 1e-4 to 1e-2", "All"], ["Batch size", "16, 32, 64, 128", "All"], ["Dropout", "0.1 to 0.5", "All"],
    ["Layers", "1 to 3", "LSTM layers; CNN convolution layers"], ["Hidden units / d_model", "32, 64, 128, 256", "All"],
    ["Attention heads", "2, 4, 8", "Transformer"], ["Feed-forward size", "64, 128, 256", "Transformer"]], [1.8, 2.0, 2.2]),
  P("The selection rule was fixed and written to a timestamped file before the test file was opened: keep architectures whose macro-F1 is within two percentage points of the best, then choose the highest Sharpe ratio. The deployed model averages the softmax outputs of the five seeds."),
  H2("3.9 Evaluation Protocol"),
  P("Figure 3 shows the four evaluation periods. Training covers February 2016 to December 2021; validation (used for early stopping, tuning, selection and trading-rule design) covers January 2022 to April 2024; the test file (May 2024 to April 2025) was evaluated once; and fresh data from 8 April 2025 to 15 September 2026, downloaded from yfinance after all design decisions, provides a forward test with every model and rule frozen."),
  ...figure("fig_split_timeline.png", "Chronological data splits"),
  H2("3.10 Walk-Forward Replay"),
  P("Because a broker API was not available, live validation was replaced by a replay of the 15-minute test file. A 15-minute Transformer (48-bar window, tuned daily hyperparameters, trained on a Colab GPU) receives bars one at a time. For every bar the pipeline recomputes indicators on a 2,000-bar buffer, predicts with the five-seed ensemble and logs the prediction, probabilities, confidence and latency to SQLite; at each day's close the frozen HMM advances one forward step to produce the ground-truth label. Predictions below 0.5 confidence are flagged. No component can place orders."),
  H2("3.11 Trading Simulation and Rules"),
  P("Trading is simulated in rupees from Rs 10,00,000. A decision is taken at each day's close from that day's forecast and executed at the same close. The realistic instrument is a Nifty 50 ETF with an all-in cost of 0.10% per side plus Rs 15.93 per sell; uninvested cash earns 6% a year. An idealised futures variant (spot prices, fractional contracts) is reported for comparison."),
  P("Experiment 1 maps confirmed regimes to exposure (for example, invested in bull and sideways, cash in bear and high-volatility) with confirmation days, a confidence filter and an optional 5% stop-loss; 72 combinations per model were searched on validation and the one with the highest final capital and a drawdown no worse than buy-and-hold was frozen. Experiment 2, designed after the Experiment 1 test results and therefore reported as post-hoc, is a probability rulebook (Figure 4): buy when P(bull) exceeds a threshold for a number of days, sell when P(bear) + P(high-volatility) exceeds a threshold, never trade on a sideways forecast, and apply a trailing stop, a cooldown and a fresh-signal requirement. A default parameter set was fixed in advance, and 324 combinations were searched on validation."),
  ...figure("fig_rulebook_flow.png", "Experiment 2 probability rulebook (default parameters)"),
  H2("3.12 Dashboard"),
  P("A read-only Streamlit dashboard presents the work to reviewers on six pages: overview, regimes (HMM labels against model forecasts with date and regime filters), models, replay, trading (equity curves, trade logs with reasons and a scorecard) and method and limitations. Figures 5 and 6 show two pages."),
  ...figure("dash_regimes.png", "Dashboard: regime timeline with the Transformer forecast", 5.6),
  ...figure("dash_trading.png", "Dashboard: trading results page", 5.6),
  summary("NexTrade is implemented end to end as a leakage-controlled Python pipeline, from cleaned data and causal HMM labels through tuned deep classifiers to replay, rupee trading and a dashboard."),
];

// ------------------------------------------------------------------ Chapter 4
const ch4 = [
  H1("Chapter 4: Results and Analysis"),
  P("This chapter reports the results of each stage: regime labels, tuning, classification on validation, test and fresh data, the 15-minute replay, and trading. All figures are produced from saved results by scripts, and test data were used only after the selection had been frozen."),
  H2("4.1 HMM Regime Labels"),
  P("With the one-day return originally specified, the HMM separated days by volatility alone: the 2023 rally was labelled 80% sideways and the first half of 2022 70% bull. Using the 20-day return produced states that match known market periods (Table 7 and Figure 7). The Bayesian information criterion favoured five states (BIC 2,012) over four (2,542); four were kept to match the project definition. Regimes switch about nine times a year."),
  ...table("HMM labels in known market periods (20-day return emission)", [["Period", "What happened", "HMM label share"],
    ["Feb to Apr 2020", "COVID crash", "69% high-volatility, 21% bear"], ["Jan to Jun 2022", "Correction", "65% bear"],
    ["2023", "Rally", "72% bull"], ["Sep to Oct 2018", "IL&FS selloff", "46% bear"]], [1.6, 1.6, 2.8]),
  ...figure("fig_regimes_full.png", "Nifty 50 close and frozen HMM regimes, 2016 to 2026"),
  H2("4.2 Hyperparameter Tuning"),
  P("Tuning improved the validation objective of every architecture (Table 8, Figure 8). The largest gains in macro-F1 came from the learning rate and dropout; model size mattered little with about 1,400 training windows. Re-running the top trials on five seeds was essential: single-seed best scores of about 0.71 fell to 0.63 to 0.68, and the trial with the best single-seed score was never the final choice. By the frozen rule, the CNN-BiLSTM-Attention (macro-F1 0.762) and Transformer (0.758) were eligible, and the Transformer was selected for its higher Sharpe ratio (0.77 against 0.67)."),
  ...table("Validation results, default and tuned (5-seed means)", [["Model", "Default macro-F1", "Tuned macro-F1", "Default objective", "Tuned objective", "Tuned params"],
    ["LSTM", "0.631", "0.685", "0.619", "0.637", "341,668"], ["CNN-BiLSTM-Attention", "0.689", "0.762", "0.647", "0.680", "365,604"],
    ["Transformer", "0.709", "0.758", "0.654", "0.691", "271,012"]], [1.7, 0.9, 0.9, 0.9, 0.9, 0.9]),
  ...figure("fig_tuning.png", "Default versus tuned macro-F1 and the Optuna search history"),
  H2("4.3 Regime Classification"),
  P("Table 9 and Figure 9 compare the five-seed ensembles across the three periods. The Transformer generalised best: on the test year it reached 87.9% accuracy and a macro-F1 of 0.836 over the regimes present, against 0.730 for a logistic-regression baseline using only the last day's features, and 81.1% accuracy on fresh data. The LSTM and CNN-BiLSTM-Attention lost more accuracy on new data. Validation scores are optimistic because the same period drove early stopping and tuning."),
  ...table("Classification by period (5-seed ensembles, accuracy / macro-F1)", [["Model", "Validation", "Test year", "Fresh data"],
    ["LSTM", "0.803 / 0.687", "0.793 / 0.621", "0.703 / 0.495"], ["CNN-BiLSTM-Attention", "0.822 / 0.818", "0.841 / 0.580", "0.630 / 0.419"],
    ["Transformer", "0.787 / 0.809", "0.879 / 0.836", "0.811 / 0.652"]], [1.9, 1.35, 1.35, 1.35]),
  ...figure("fig_classification_periods.png", "Accuracy and macro-F1 by evaluation period"),
  P("The confusion matrix (Figure 10) shows balanced recall for the regimes present in the test year: 0.87 for bull, 0.85 for bear and 0.89 for sideways, with only 0.4% of forecasts below 0.5 confidence. The frozen HMM labelled 65% of the test year sideways, including the slow October 2024 to March 2025 decline, and no high-volatility days. Figure 11 shows that labels change only after the market moves: the 4 June 2024 election-result fall was labelled bear from that day, after the loss had occurred."),
  ...figure("fig_confusion_test.png", "Confusion matrix of the Transformer ensemble, test year", 3.8),
  ...figure("fig_test_timeline.png", "Test year: HMM regimes and Transformer forecasts"),
  H2("4.4 Walk-Forward Replay"),
  P("The replay processed all 5,800 test bars (100% uptime) with a p95 latency of 163 ms per bar against a requirement of 2 seconds, and matched the batch pipeline exactly: 100% prediction agreement, a maximum probability difference of 3.0e-07 and identical daily labels. The 15-minute model itself was weaker than the daily model: accuracy fell from 70.2% on validation to 51.8% on the test year, and 16.6% of forecasts were flagged as low confidence (Figure 12). Its best epochs were 1 to 4, indicating early overfitting with the daily-tuned learning rate."),
  ...figure("fig_replay.png", "Replay confidence and rolling accuracy, 15-minute Transformer"),
  H2("4.5 Trading on the Test Year"),
  P("Table 10 and Figure 13 show the value of Rs 10 lakh after the test year. Experiment 1 lost money for every model. The Experiment 2 rulebook ended slightly positive for most versions, but Figure 14 shows that the trading P&L excluding interest was negative for all nine versions: the positive balances were interest on idle cash. No system beat a 6% liquid fund, although every realistic system had a smaller maximum drawdown than buy-and-hold (between 6.6% and 13.0% against 15.7%)."),
  ...table("Test-year trading results from Rs 10,00,000 (ETF)", [["Model", "Exp 1 rules", "Exp 2 default", "Exp 2 tuned"],
    ["LSTM", "Rs 9,70,051", "Rs 9,92,193", "Rs 10,21,018"], ["CNN-BiLSTM-Attention", "Rs 9,62,903", "Rs 10,04,727", "Rs 10,06,074"],
    ["Transformer", "Rs 9,29,569", "Rs 9,90,485", "Rs 10,19,525"], ["Buy-and-hold ETF", "Rs 9,81,776", "", ""], ["Cash at 6%", "Rs 10,55,109", "", ""]],
    [1.9, 1.35, 1.35, 1.35]),
  ...figure("fig_trading_test.png", "Test-year equity curves, Experiment 1 and Experiment 2"),
  ...figure("fig_profit_split.png", "Experiment 2: interest income versus trading P&L, test year"),
  H2("4.6 Forward Test on Fresh Data"),
  P("On 354 trading days after the test file ended, with every model and rule frozen, the ranking reversed (Figure 15). The Experiment 2 rulebook lost money for every model, while Experiment 1 was profitable in five of six versions. The CNN-BiLSTM-Attention with Experiment 1 rules ended at Rs 11,24,388, beating buy-and-hold (Rs 10,40,165) and cash (Rs 10,85,297) with positive trading P&L of Rs 1,06,102. Chaining both unseen periods (Figure 16, Table 11), no realistic system was profitable in both, and the best (CNN-BiLSTM-Attention, Experiment 1, Rs 10,82,677) beat buy-and-hold but not cash."),
  ...figure("fig_trading_fresh.png", "Fresh-data equity curves by model"),
  ...figure("fig_chained.png", "Value of Rs 10 lakh across both unseen periods"),
  ...table("Both unseen periods chained (May 2024 to September 2026)", [["System", "Test year", "Fresh data", "Chained"],
    ["CNN-BiLSTM-Attention, Exp 1", "Rs 9,62,903", "Rs 11,24,388", "Rs 10,82,677"], ["LSTM, Exp 1", "Rs 9,70,051", "Rs 10,32,009", "Rs 10,01,101"],
    ["Transformer, Exp 2 tuned", "Rs 10,19,525", "Rs 9,80,449", "Rs 9,99,592"], ["Transformer, Exp 1", "Rs 9,29,569", "Rs 10,07,329", "Rs 9,36,382"],
    ["Buy-and-hold ETF", "Rs 9,81,776", "Rs 10,40,165", "Rs 10,21,208"], ["Cash at 6%", "Rs 10,55,109", "Rs 10,85,297", "Rs 11,45,107"]], [2.1, 1.3, 1.3, 1.3]),
  H2("4.7 Discussion"),
  P("Two findings stand out. First, classification quality and trading value are not aligned. The Transformer reproduces the HMM labels most faithfully and trades worst, while the CNN-BiLSTM-Attention, the weakest classifier on unseen data, trades best. HMM regimes are identified after a move, so a faithful copy of the labels inherits their delay. Second, validation-based rule selection over many combinations did not carry over reliably, consistent with the backtest-overfitting risk described by Bailey et al. [20]; the untouched forward test was necessary to expose this."),
  H2("4.8 Standards and Validation of Results"),
  P("The requirements were documented as a Software Requirements Specification structured according to IEEE Std 830-1998 [21]. Verification follows a test-driven approach: 52 automated tests check data validity, the causality of every indicator and the HMM filter, train-only scaling, window alignment, model output shapes, backtest arithmetic, trading-rule behaviour and search-space construction. Results are reproducible from a single configuration file with fixed seeds, and every training run, tuning trial and evaluation is logged."),
  summary("The system classifies regimes well on unseen data and its replay is exact and fast, but trading on the regimes was not reliably profitable across the test year and the fresh period; risk reduction was the consistent benefit."),
];

// ------------------------------------------------------------------ Chapter 5
const ch5 = [
  H1("Chapter 5: Advantages, Limitations and Applications"),
  P("This chapter summarises what NexTrade does well, where it falls short, and where it can be applied."),
  H2("5.1 Advantages"),
  B("Leakage-controlled by construction and by test: causal features and labels, train-only fitting, frozen selections and a one-time test."),
  B("Fair comparison of three architectures on identical data, with multi-seed re-runs that remove seed luck from tuning results."),
  B("Evaluation beyond accuracy: rupee trading with costs and cash interest, decomposition of profit into trading and interest, and a forward test on fresh data."),
  B("Operationally ready: a replay proven identical to the batch pipeline, sub-second latency and a logged prediction trail."),
  B("Transparent reporting through a dashboard and documented deviations, suitable for review by non-specialists."),
  H2("5.2 Limitations"),
  B("HMM labels lag turning points and classify slow, calm declines as sideways, which limits trading value."),
  B("Few regime episodes per period (about nine switches a year) and rare high-volatility days (2% to 4%) make per-class scores noisy."),
  B("The 15-minute model overfits within a few epochs and was not tuned for 15-minute data."),
  B("Experiment 2 is post-hoc; the futures results are idealised; transaction costs are approximate."),
  B("No volume or India VIX features, and fresh data come from a different source (median close difference 0.02%)."),
  H2("5.3 Applications"),
  B("Risk management: scaling equity exposure by regime reduced drawdowns relative to buy-and-hold in both unseen periods."),
  B("Market monitoring: a daily regime dashboard for analysts and portfolio managers."),
  B("Research platform: a reusable, tested pipeline for comparing sequence models and label definitions on Indian indices."),
  B("Education: a worked example of honest out-of-sample evaluation and backtest-overfitting risk."),
  summary("NexTrade's strengths are rigour, fairness and transparency; its main limitation is the lag in HMM-based labels, and its most dependable application is risk reduction rather than profit generation."),
];

// ------------------------------------------------------------------ Chapter 6
const ch6 = [
  H1("Chapter 6: Conclusion and Future Scope"),
  P("This chapter summarises the work carried out up to Review 2, draws conclusions, compares progress with the plan from Review 1, and sets out the future scope."),
  H2("6.1 Work Carried Out"),
  P("All stages of the approved scope have been implemented: data cleaning and feature engineering, causal HMM regime labelling, training and tuning of LSTM, CNN-BiLSTM-Attention and Transformer models, frozen model selection, a one-time test, a 15-minute walk-forward replay in place of live broker validation, rupee-denominated trading with two rule experiments, a forward test on 17 months of fresh data, and a Streamlit dashboard."),
  H2("6.2 Conclusions"),
  B("Deep models can forecast HMM-defined Nifty 50 regimes out of sample: the selected Transformer ensemble reached 87.9% accuracy on the test year and 81.1% on fresh data."),
  B("Trading on those forecasts was not reliably profitable. No realistic system was profitable in both unseen periods, and none beat a 6% liquid fund over the combined 2.4 years."),
  B("The best classifier was the worst trader, because the HMM labels lag the market. Improving the label definition matters more than improving the classifier."),
  B("Regime-based exposure consistently reduced drawdown, which is its most dependable value."),
  H2("6.3 Progress Against the Plan"),
  P("Figure 17 compares the Review 1 plan with actual progress. A first pipeline was completed in Weeks 1 to 5, and the final regime-classification pipeline, testing, tuning, trading, replay, forward test and dashboard were completed by Week 7, ahead of the plan, which scheduled these tasks for Weeks 8 to 14. The black-book report is in progress for Review 3."),
  ...figure("fig_gantt.png", "Plan versus actual progress (Week 1 = 3 August 2026)"),
  ...table("Challenges faced and solutions", [["Challenge", "Solution"],
    ["Duplicated and inconsistent vendor data", "Kept the copy continuous with the prior close; recomputed all indicators"],
    ["HMM states driven by volatility only", "20-day return emission, validated on known market periods"],
    ["Look-ahead in smoothed HMM posteriors", "Forward-filtered labels with causality tests"],
    ["Lucky single-seed tuning results", "Top-3 trials re-run on five seeds"],
    ["15-minute training too slow on CPU", "Colab T4 GPU bundle"],
    ["No broker API for live data", "Bar-by-bar replay and forward test on fresh data"],
    ["Hindsight in trading-rule design", "Frozen rules and an untouched forward test"]], [2.6, 3.4]),
  H2("6.4 Individual Contributions"),
  ...table("Individual contributions", [["Member", "Modules and tasks"],
    ["Vishal Singh", [[ph("[To be filled by the team]")]]]], [1.8, 4.2]),
  H2("6.5 Future Scope"),
  B([r("Weeks 8 to 9: ", { bold: true }), r("define regimes from forward-looking 20-day returns and volatility to remove label lag, evaluated on validation only.")]),
  B([r("Weeks 9 to 11: ", { bold: true }), r("walk-forward retraining each year to obtain several out-of-sample years; tune the 15-minute model.")]),
  B([r("Weeks 11 to 13: ", { bold: true }), r("revise the rulebook with trend and re-entry rules chosen on validation, and repeat the frozen forward test.")]),
  B([r("Weeks 14 to 15: ", { bold: true }), r("black-book report, dashboard refinement, final presentation and viva.")]),
  B("Beyond the course: live paper trading through a broker API, futures volume and India VIX features, probability calibration and confidence-based sizing, and extension to Bank Nifty and other indices, including a regime-aware LightGBM baseline [11]."),
];

// ------------------------------------------------------------------ references & appendices
const refs = [
  "Y. Yuan and G. Mitra, \"Market Regime Identification Using Hidden Markov Models,\" SSRN Working Paper 3406068, 2016.",
  "W. Lu, J. Li, Y. Li, A. Sun and J. Wang, \"A CNN-BiLSTM-AM method for stock price prediction,\" Neural Computing and Applications, Springer, 2020.",
  "M. Al Ridhawi, M. Haj Ali and H. Al Osman, \"Adaptive Regime-Aware Stock Price Prediction Using Autoencoder-Gated Dual Node Transformers with Reinforcement Learning Control,\" arXiv:2603.19136, 2026.",
  "J. Xiao, S. Bi and T. Deng, \"Comparative Analysis of LSTM, GRU, and Transformer Models for Stock Price Prediction,\" arXiv:2411.05790, 2024.",
  "\"Integrating deep learning and econometrics for stock price prediction: A comprehensive comparison of LSTM, transformers, and traditional time series models,\" ScienceDirect, 2025.",
  "\"Impact of Hyperparameter Optimisation Techniques in Deep Learning-based Investment Predictions: An Indian ETF-based analysis,\" Research Square (preprint), 2025.",
  "\"Stock Market Analysis and Prediction for Nifty50 using LSTM Deep Learning Approach,\" IEEE Xplore, 2022.",
  "\"Comparative Analysis of Deep Learning Models for Stock Price Prediction in the Indian Market,\" MDPI, 2024.",
  "\"An efficient real-time stock prediction exploiting incremental learning and deep learning,\" Evolving Systems, Springer, 2022.",
  "R. G. Mishra, D. Sharma, M. Gadhavi, S. Pant and A. Kumar, \"A Deep Reinforcement Learning Framework for Strategic Indian NIFTY 50 Index Trading,\" AI, vol. 6, no. 8, p. 183, 2025.",
  "A. Pagliaro, \"Regime-Aware LightGBM for Stock Market Forecasting: A Validated Walk-Forward Framework with Statistical Rigor and Explainable AI Analysis,\" Electronics, vol. 15, no. 6, p. 1334, 2026.",
  "\"Machine Learning-Driven Market Regime Analysis in Equity Markets: A Gaussian Hidden Markov Model Approach,\" ResearchGate, 2025.",
  "J. D. Hamilton, \"A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle,\" Econometrica, vol. 57, no. 2, pp. 357-384, 1989.",
  "L. R. Rabiner, \"A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition,\" Proceedings of the IEEE, vol. 77, no. 2, pp. 257-286, 1989.",
  "S. Hochreiter and J. Schmidhuber, \"Long Short-Term Memory,\" Neural Computation, vol. 9, no. 8, pp. 1735-1780, 1997.",
  "D. Bahdanau, K. Cho and Y. Bengio, \"Neural Machine Translation by Jointly Learning to Align and Translate,\" in Proc. International Conference on Learning Representations (ICLR), 2015.",
  "A. Vaswani et al., \"Attention Is All You Need,\" in Advances in Neural Information Processing Systems 30, pp. 5998-6008, 2017.",
  "J. Bergstra, R. Bardenet, Y. Bengio and B. Kegl, \"Algorithms for Hyper-Parameter Optimization,\" in Advances in Neural Information Processing Systems 24, pp. 2546-2554, 2011.",
  "T. Akiba, S. Sano, T. Yanase, T. Ohta and M. Koyama, \"Optuna: A Next-generation Hyperparameter Optimization Framework,\" in Proc. ACM SIGKDD, pp. 2623-2631, 2019.",
  "D. H. Bailey, J. M. Borwein, M. Lopez de Prado and Q. J. Zhu, \"Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance,\" Notices of the American Mathematical Society, vol. 61, no. 5, pp. 458-471, 2014.",
  "IEEE Std 830-1998, \"IEEE Recommended Practice for Software Requirements Specifications,\" IEEE, 1998.",
];
const references = [
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [r("References")], spacing: { after: 240 } }),
  ...refs.map((t, i) => new Paragraph({ spacing: { line: 300, after: 100 }, indent: { left: 540, hanging: 540 }, alignment: AlignmentType.LEFT,
    children: [r(`[${i + 1}]\t${t}`)], tabStops: [{ type: TabStopType.LEFT, position: 540 }] })),
];
const appendices = [
  H1("Appendix A: Soft Code Flowcharts"),
  P("The execution order of the implementation scripts is shown below; each stage reads the outputs of the previous one and writes timestamped results."),
  ...table("Script execution order", [["Stage", "Script", "Output"],
    ["1-2", "01_clean_data.py, 02_build_features.py", "Clean bars, features, train-only scaler"],
    ["3", "03_label_regimes.py", "Frozen HMM and regime labels"],
    ["4-5", "04_train_default_models.py, 05_backtest_default_models.py", "Default models and backtests"],
    ["6", "06_tune.py, 06_summarize_tuning.py", "Optuna studies and tuned models"],
    ["7", "07_select_model.py, 07_prepare_test_data.py, 07_evaluate_test.py", "Frozen selection and test results"],
    ["8-9", "08_train_15min.py (Colab), 09_replay.py", "15-minute model and replay log"],
    ["10-11", "10_*.py, 11_*.py", "Trading rules, rulebook and results"],
    ["12", "12_prepare_fresh.py, 12_evaluate_fresh.py", "Forward-test results"],
    ["Dashboard", "dashboard/app.py", "Streamlit dashboard"]], [0.8, 3.0, 2.2], { size: 18 }),
  P("The decision flow of the trading rulebook is shown in Figure 4 (Section 3.11)."),
  H1("Appendix B: Data Sheets"),
  ...table("Dataset and configuration summary", [["Item", "Value"],
    ["Instrument", "Nifty 50 index (^NSEI)"], ["Training file", "57,478 fifteen-minute bars, Apr 2015 to Apr 2024"],
    ["Test file", "6,014 fifteen-minute bars, May 2024 to Apr 2025"], ["Fresh data", "354 daily bars, 8 Apr 2025 to 15 Sep 2026 (yfinance)"],
    ["Session", "09:15 to 15:15 bar starts, 25 bars per day"], ["Window", "30 days (daily model); 48 bars (15-minute model)"],
    ["Classes", "bull, bear, sideways, high-volatility"], ["Seeds", "5 per configuration (42 to 46)"],
    ["Capital and costs", "Rs 10,00,000; ETF 0.10% per side + Rs 15.93 per sell; cash at 6% a year"]], [1.8, 4.2]),
  H1("Appendix C: List of Components"),
  ...table("Software components and versions", [["Component", "Version", "Role"],
    ["Python", "3.13", "Language"], ["PyTorch", "2.14", "Deep-learning models"], ["Optuna", "4.9", "Hyperparameter tuning"],
    ["hmmlearn", "0.3.3", "Gaussian HMM"], ["scikit-learn", "1.6.1", "Metrics and baseline"], ["pandas / NumPy", "2.3.1 / 2.2.3", "Data handling"],
    ["Matplotlib", "3.10.5", "Figures"], ["Streamlit / Plotly", "1.64 / 7.1", "Dashboard"], ["pytest", "latest", "Automated tests"]], [1.8, 1.4, 2.8]),
  H1("Appendix D: List of Papers Presented and Published"),
  P("No papers have been presented or published at the time of this interim report."),
];

// ------------------------------------------------------------------ document
const header = new Header({ children: [new Paragraph({ tabStops: [{ type: TabStopType.RIGHT, position: TEXT_W }], border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999", space: 2 } },
  children: [r("NexTrade: Regime-Aware AI Trading System", { size: 18 }), r("\t" + YEAR, { size: 18 })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] });
const page = (fmt, start) => ({ size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 2160, right: 1440, header: 708, footer: 708 },
  pageNumbers: start ? { start, formatType: fmt } : { formatType: fmt } });

const doc = new Document({
  creator: "Group 17", title: TITLE, description: "Review 2 interim report",
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 360 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 36, bold: true, color: "000000" }, paragraph: { outlineLevel: 0, spacing: { before: 0, after: 240 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true, color: "000000" }, paragraph: { outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: "000000" }, paragraph: { outlineLevel: 2 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 20, color: "000000" } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] }] },
  sections: [
    { properties: { page: page(NumberFormat.LOWER_ROMAN, 1) }, children: titlePage },
    { properties: { type: SectionType.NEXT_PAGE, page: page(NumberFormat.LOWER_ROMAN, 2) }, headers: { default: header }, footers: { default: footer },
      children: [...certificate, ...acknowledgement, ...abstract, ...lists] },
    { properties: { type: SectionType.NEXT_PAGE, page: page(NumberFormat.DECIMAL, 1) }, headers: { default: header }, footers: { default: footer },
      children: [...ch1, ...ch2, ...ch3, ...ch4, ...ch5, ...ch6, ...references, ...appendices] },
  ],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT); });
