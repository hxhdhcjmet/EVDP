import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN

class ClusterAnalyzer:
    def __init__(self, data, feature_cols, scale=True):
        self.data = data.copy()
        self.feature_cols = feature_cols
        self.scale = scale
        self.X = self.data[feature_cols].values
        self.scaler = StandardScaler() if scale else None
        self.labels_ = None

    def _prepare_X(self):
        X = self.X
        if self.scaler:
            X = self.scaler.fit_transform(X)
        return X

    def fit_kmeans(self, n_clusters=3, random_state=42):
        X = self._prepare_X()
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=random_state)
        self.labels_ = km.fit_predict(X)
        return self.labels_

    def fit_agglomerative(self, n_clusters=3, linkage="ward"):
        X = self._prepare_X()
        agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        self.labels_ = agg.fit_predict(X)
        return self.labels_

    def fit_dbscan(self, eps=0.5, min_samples=5):
        X = self._prepare_X()
        db = DBSCAN(eps=eps, min_samples=min_samples)
        self.labels_ = db.fit_predict(X)
        return self.labels_

    def plot_clusters(self, x_index=0, y_index=1, title="聚类结果", x_label=None, y_label=None):
        if self.labels_ is None:
            return None
        X = self._prepare_X()
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x=X[:, x_index], y=X[:, y_index], hue=self.labels_, palette="tab10", ax=ax, legend=True)
        ax.set_xlabel(x_label or self.feature_cols[x_index])
        ax.set_ylabel(y_label or self.feature_cols[y_index])
        ax.set_title(title)
        return fig
