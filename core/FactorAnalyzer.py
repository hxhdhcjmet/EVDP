import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler

class FactorAnalyzerSimple:
    def __init__(self, data, feature_cols, n_factors=2, scale=True):
        self.data = data.copy()
        self.feature_cols = feature_cols
        self.n_factors = n_factors
        self.scale = scale
        self.X = self.data[feature_cols].values
        self.scaler = StandardScaler() if scale else None
        self.loadings_ = None
        self.scores_ = None

    def fit(self):
        X = self.X
        if self.scaler:
            X = self.scaler.fit_transform(X)
        corr = np.corrcoef(X, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(corr)
        idx = np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
        self.loadings_ = eigvecs[:, : self.n_factors] * np.sqrt(eigvals[: self.n_factors])
        self.scores_ = X @ eigvecs[:, : self.n_factors]

    def plot_loadings_heatmap(self, title="因子载荷热图"):
        if self.loadings_ is None:
            return None
        fig, ax = plt.subplots(figsize=(8, 6))
        df = pd.DataFrame(self.loadings_, index=self.feature_cols, columns=[f"因子{i+1}" for i in range(self.n_factors)])
        sns.heatmap(df, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        ax.set_title(title)
        return fig
