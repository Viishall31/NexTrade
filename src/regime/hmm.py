"""Step 3: Gaussian HMM regime labelling (FR-R1..R5).

Fitted on the train split only, then frozen. Labels use the filtered posterior
p(state_t | obs_1..t) computed by a forward pass, so labels are causal and the same
code produces live labels.
"""
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy.special import logsumexp
from scipy.stats import multivariate_normal


@dataclass
class RegimeHMM:
    model: GaussianHMM
    emission_mean: np.ndarray       # train-split standardisation of the emissions
    emission_std: np.ndarray
    state_to_label: dict            # hmm state index -> regime name
    emissions: list

    def _obs(self, df: pd.DataFrame) -> np.ndarray:
        return (df[self.emissions].to_numpy() - self.emission_mean) / self.emission_std

    def filtered_posterior(self, df: pd.DataFrame) -> np.ndarray:
        """Forward algorithm in log space: row t = p(state | obs_1..t)."""
        X = self._obs(df)
        m = self.model
        log_b = np.column_stack([
            multivariate_normal(m.means_[k], m.covars_[k]).logpdf(X) for k in range(m.n_components)
        ])
        log_A = np.log(np.maximum(m.transmat_, 1e-300))
        log_alpha = np.empty_like(log_b)
        log_alpha[0] = np.log(np.maximum(m.startprob_, 1e-300)) + log_b[0]
        for t in range(1, len(X)):
            log_alpha[t] = logsumexp(log_alpha[t - 1][:, None] + log_A, axis=0) + log_b[t]
        return np.exp(log_alpha - logsumexp(log_alpha, axis=1, keepdims=True))

    def forward_step(self, log_post_prev: np.ndarray, obs_row: pd.DataFrame) -> np.ndarray:
        """One live update: normalised log p(state_t | obs_1..t) from the previous one and a new observation."""
        m = self.model
        x = self._obs(obs_row)[0]
        log_b = np.array([multivariate_normal(m.means_[k], m.covars_[k]).logpdf(x) for k in range(m.n_components)])
        log_a = logsumexp(log_post_prev[:, None] + np.log(np.maximum(m.transmat_, 1e-300)), axis=0) + log_b
        return log_a - logsumexp(log_a)

    def label(self, df: pd.DataFrame) -> pd.DataFrame:
        post = self.filtered_posterior(df)
        names = [self.state_to_label[k] for k in range(post.shape[1])]
        out = pd.DataFrame(post, index=df.index, columns=[f"p_{n}" for n in names])
        out["state"] = post.argmax(axis=1)
        out["regime"] = out["state"].map(self.state_to_label)
        return out

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: Path) -> "RegimeHMM":
        with open(path, "rb") as f:
            return pickle.load(f)


def fit_best_of(X: np.ndarray, n_states: int, cfg: dict, seed: int) -> GaussianHMM:
    """n_init random restarts, keep the highest train log-likelihood."""
    best, best_ll = None, -np.inf
    for i in range(cfg["n_init"]):
        m = GaussianHMM(n_components=n_states, covariance_type=cfg["covariance_type"],
                        n_iter=cfg["n_iter"], tol=cfg["tol"], random_state=seed + i)
        m.fit(X)
        ll = m.score(X)
        if ll > best_ll:
            best, best_ll = m, ll
    return best


def name_states(train_df: pd.DataFrame, states: np.ndarray, emissions: list) -> tuple[dict, pd.DataFrame]:
    """Map latent states to regime names from the bars assigned to each state.

    high_vol = highest mean volatility; of the rest, bull = highest mean return,
    bear = lowest mean return, sideways = the remaining state.
    """
    ret_col, vol_col = emissions
    stats = train_df.groupby(states)[[ret_col, vol_col]].mean()
    stats["days"] = pd.Series(states).value_counts()
    high_vol = stats[vol_col].idxmax()
    rest = stats.drop(index=high_vol).sort_values(ret_col)
    mapping = {high_vol: "high_vol", rest.index[0]: "bear", rest.index[-1]: "bull"}
    mapping[rest.index[1]] = "sideways"
    stats["regime"] = stats.index.map(mapping)
    return mapping, stats


def fit_regime_hmm(train_df: pd.DataFrame, cfg: dict, seed: int) -> tuple[RegimeHMM, pd.DataFrame]:
    emissions = cfg["emissions"]
    raw = train_df[emissions].to_numpy()
    mean, std = raw.mean(axis=0), raw.std(axis=0)
    model = fit_best_of((raw - mean) / std, cfg["n_states"], cfg, seed)
    hmm = RegimeHMM(model, mean, std, {}, emissions)
    # Name states from filtered assignments, i.e. exactly how labels will be produced.
    states = hmm.filtered_posterior(train_df).argmax(axis=1)
    hmm.state_to_label, stats = name_states(train_df, states, emissions)
    return hmm, stats


def bic_table(train_df: pd.DataFrame, cfg: dict, seed: int) -> pd.DataFrame:
    raw = train_df[cfg["emissions"]].to_numpy()
    X = (raw - raw.mean(axis=0)) / raw.std(axis=0)
    rows = []
    for k in cfg["bic_check_states"]:
        m = fit_best_of(X, k, cfg, seed)
        rows.append({"k": k, "log_likelihood": m.score(X), "bic": m.bic(X)})
    return pd.DataFrame(rows).set_index("k")
