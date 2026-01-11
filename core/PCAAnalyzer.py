import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from core.visualize import apply_global_style, wrap_text, responsive_tight_layout

class PCAAnalyzer:
    def __init__(self, data, feature_cols, n_components=2, scale=True):
        self.data = data.copy()
        self.feature_cols = feature_cols
        self.n_components = n_components
        self.scale = scale
        self.X = self.data[feature_cols].values
        self.scaler = StandardScaler() if scale else None
        self.pca = None
        self.components_ = None
        self.explained_variance_ratio_ = None
        self.scores_ = None

    def fit(self):
        X = self.X
        if self.scaler:
            X = self.scaler.fit_transform(X)
        self.pca = PCA(n_components=self.n_components)
        self.scores_ = self.pca.fit_transform(X)
        self.components_ = self.pca.components_
        self.explained_variance_ratio_ = self.pca.explained_variance_ratio_

    def plot_scree(self, title="PCA Variance Contribution", x_label="Component", y_label="Explained Variance Ratio"):
        apply_global_style()
        fig, ax = plt.subplots(figsize=(8, 6))
        idx = np.arange(1, len(self.explained_variance_ratio_) + 1)
        sns.barplot(x=idx, y=self.explained_variance_ratio_, ax=ax)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        responsive_tight_layout(fig)
        return fig

    def plot_biplot(self, title="PCA Biplot", x_label="PC1", y_label="PC2"):
        if self.scores_ is None or self.components_ is None:
            return None
        apply_global_style()
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(self.scores_[:, 0], self.scores_[:, 1], alpha=0.7)
        scale = np.max(np.abs(self.scores_[:, :2])) if self.scores_.shape[1] >= 2 else 1.0
        for i, col in enumerate(self.feature_cols):
            ax.arrow(0, 0, self.components_[0, i] * scale, self.components_[1, i] * scale, color="r", alpha=0.5)
            ax.text(self.components_[0, i] * scale * 1.05, self.components_[1, i] * scale * 1.05, str(col), fontsize=9)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True)
        responsive_tight_layout(fig)
        return fig
