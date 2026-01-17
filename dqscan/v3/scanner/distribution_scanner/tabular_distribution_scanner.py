# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from ..common.base_scanner import BaseScanner

try:
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from scipy import stats  # type: ignore
    from scipy.spatial.distance import cdist  # type: ignore

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler  # type: ignore

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TabularDistributionScanner(BaseScanner):
    def __init__(self, p_val: float = 0.05):
        super().__init__(name="TabularDistributionScanner")
        self.p_val = p_val

    def scan(
        self,
        dataset1: Any,
        dataset2: Any,
        numerical_columns: Optional[list[str]] = None,
        categorical_columns: Optional[list[str]] = None,
        label_column: Optional[str] = None,
    ) -> dict[str, Any]:
        if not (PANDAS_AVAILABLE and SCIPY_AVAILABLE and SKLEARN_AVAILABLE):
            missing = []
            if not PANDAS_AVAILABLE:
                missing.append("pandas")
            if not SCIPY_AVAILABLE:
                missing.append("scipy")
            if not SKLEARN_AVAILABLE:
                missing.append("scikit-learn")
            return self._error_result(f"依赖缺失：{', '.join(missing)}；请安装后重试")

        assert PANDAS_AVAILABLE and SCIPY_AVAILABLE and SKLEARN_AVAILABLE
        self.validate_data(dataset1, pd.DataFrame)
        self.validate_data(dataset2, pd.DataFrame)

        if self.check_empty(dataset1) or self.check_empty(dataset2):
            return {"error": "数据集为空", "dataset1_size": len(dataset1), "dataset2_size": len(dataset2)}

        if numerical_columns is None and categorical_columns is None:
            numerical_columns = dataset1.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = dataset1.select_dtypes(include=["object", "category"]).columns.tolist()
            if label_column:
                if label_column in numerical_columns:
                    numerical_columns.remove(label_column)
                if label_column in categorical_columns:
                    categorical_columns.remove(label_column)

        numerical_columns = numerical_columns or []
        categorical_columns = categorical_columns or []

        results: dict[str, Any] = {
            "algorithm": "MMD + K-S Test + Chi-Square",
            "dataset1_size": len(dataset1),
            "dataset2_size": len(dataset2),
            "numerical_features": len(numerical_columns),
            "categorical_features": len(categorical_columns),
        }

        if numerical_columns:
            results["mmd_result"] = self._detect_mmd(dataset1, dataset2, numerical_columns)
            results["ks_results"] = self._detect_ks(dataset1, dataset2, numerical_columns)
        if categorical_columns:
            results["chi2_results"] = self._detect_chi2(dataset1, dataset2, categorical_columns)
        if label_column and label_column in dataset1.columns and label_column in dataset2.columns:
            results["label_shift"] = self._detect_label_shift(dataset1, dataset2, label_column)

        summary = self._create_summary(results)
        results["summary"] = summary

        results["has_issues"] = bool(summary.get("drift_detected", False))
        results["drift_detected"] = bool(summary.get("drift_detected", False))
        results["p_value"] = float(results.get("mmd_result", {}).get("p_value", 1.0))

        detailed_issues: list[dict[str, Any]] = []
        total_features = 0
        drifted_features = 0

        ks_feature_results = results.get("ks_results", {}).get("feature_results", {}) if isinstance(results.get("ks_results"), dict) else {}
        for name, r in ks_feature_results.items():
            total_features += 1
            if r.get("drift_detected"):
                drifted_features += 1
                detailed_issues.append(
                    {
                        "data_id": name,
                        "issue_type": "分布漂移",
                        "severity": "moderate" if float(r.get("p_value", 1.0)) < 0.01 else "light",
                        "details": {"p_value": float(r.get("p_value", 1.0)), "metric": "ks_statistic"},
                    }
                )

        chi_feature_results = (
            results.get("chi2_results", {}).get("feature_results", {}) if isinstance(results.get("chi2_results"), dict) else {}
        )
        for name, r in chi_feature_results.items():
            total_features += 1
            if r.get("drift_detected"):
                drifted_features += 1
                detailed_issues.append(
                    {
                        "data_id": name,
                        "issue_type": "类别分布漂移",
                        "severity": "moderate" if float(r.get("p_value", 1.0)) < 0.01 else "light",
                        "details": {"p_value": float(r.get("p_value", 1.0)), "metric": "chi2_statistic"},
                    }
                )

        results["total_issues"] = int(drifted_features)
        results["issue_percentage"] = float(drifted_features / total_features) if total_features > 0 else 0.0
        results["detailed_issues"] = detailed_issues
        return results

    def _detect_mmd(self, dataset1: "pd.DataFrame", dataset2: "pd.DataFrame", columns: list[str]) -> dict[str, Any]:
        X = dataset1[columns].dropna().values
        Y = dataset2[columns].dropna().values

        max_samples = 5000
        if len(X) > max_samples:
            X = X[np.random.choice(len(X), max_samples, replace=False)]
        if len(Y) > max_samples:
            Y = Y[np.random.choice(len(Y), max_samples, replace=False)]

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        Y_scaled = scaler.transform(Y)

        mmd_value, p_value = self._compute_mmd_pvalue(X_scaled, Y_scaled)
        return {"method": "MMD (RBF Kernel)", "mmd_value": float(mmd_value), "p_value": float(p_value), "drift_detected": p_value < self.p_val}

    def _compute_mmd_pvalue(self, X: "np.ndarray", Y: "np.ndarray", n_perm: int = 200) -> tuple[float, float]:
        mmd_real = self._compute_mmd(X, Y)
        n, m = len(X), len(Y)
        combined = np.vstack([X, Y])
        mmd_null = []
        for _ in range(n_perm):
            perm = np.random.permutation(n + m)
            mmd_null.append(self._compute_mmd(combined[perm[:n]], combined[perm[n:]]))
        p_value = (np.array(mmd_null) >= mmd_real).sum() / n_perm
        return float(mmd_real), float(p_value)

    def _compute_mmd(self, X: "np.ndarray", Y: "np.ndarray") -> float:
        n, m = X.shape[0], Y.shape[0]
        sample_size = min(1000, n, m)
        X_s = X[np.random.choice(n, sample_size, replace=False)]
        Y_s = Y[np.random.choice(m, sample_size, replace=False)]
        median_dist = np.median(cdist(X_s, Y_s, "euclidean"))
        gamma = 1.0 / (2 * median_dist**2) if median_dist > 0 else 1.0

        def rbf(A, B):
            return np.exp(-gamma * cdist(A, B, "sqeuclidean"))

        K_XX, K_YY, K_XY = rbf(X, X), rbf(Y, Y), rbf(X, Y)
        term1 = (K_XX.sum() - np.diag(K_XX).sum()) / (n * (n - 1))
        term2 = (K_YY.sum() - np.diag(K_YY).sum()) / (m * (m - 1))
        term3 = K_XY.sum() / (n * m)
        return float(np.sqrt(max(0, term1 + term2 - 2 * term3)))

    def _detect_ks(self, dataset1: "pd.DataFrame", dataset2: "pd.DataFrame", columns: list[str]) -> dict[str, Any]:
        drifted: list[str] = []
        results: dict[str, Any] = {}
        for col in columns:
            v1 = dataset1[col].dropna().values
            v2 = dataset2[col].dropna().values
            if len(v1) < 10 or len(v2) < 10:
                continue
            ks_stat, p_value = stats.ks_2samp(v1, v2)
            results[str(col)] = {"ks_statistic": float(ks_stat), "p_value": float(p_value), "drift_detected": p_value < self.p_val}
            if p_value < self.p_val:
                drifted.append(str(col))
        return {"method": "K-S Test", "drifted_features": drifted, "drift_rate": len(drifted) / len(results) if results else 0, "feature_results": results}

    def _detect_chi2(self, dataset1: "pd.DataFrame", dataset2: "pd.DataFrame", columns: list[str]) -> dict[str, Any]:
        drifted: list[str] = []
        results: dict[str, Any] = {}
        for col in columns:
            try:
                d1, d2 = dataset1[col].value_counts(), dataset2[col].value_counts()
                cats = sorted(set(d1.index) | set(d2.index))
                c1, c2 = [d1.get(c, 0) for c in cats], [d2.get(c, 0) for c in cats]
                chi2, p_value, _, _ = stats.chi2_contingency(np.array([c1, c2]))
                results[str(col)] = {"chi2_statistic": float(chi2), "p_value": float(p_value), "drift_detected": p_value < self.p_val}
                if p_value < self.p_val:
                    drifted.append(str(col))
            except Exception as e:
                results[str(col)] = {"error": str(e)}
        return {"method": "Chi-Square Test", "drifted_features": drifted, "drift_rate": len(drifted) / len(results) if results else 0, "feature_results": results}

    def _detect_label_shift(self, dataset1: "pd.DataFrame", dataset2: "pd.DataFrame", label_column: str) -> dict[str, Any]:
        try:
            d1, d2 = dataset1[label_column].value_counts(), dataset2[label_column].value_counts()
            labels = sorted(set(d1.index) | set(d2.index))
            c1, c2 = [d1.get(l, 0) for l in labels], [d2.get(l, 0) for l in labels]
            chi2, p_value, _, _ = stats.chi2_contingency(np.array([c1, c2]))
            return {"method": "Chi-Square", "p_value": float(p_value), "drift_detected": p_value < self.p_val}
        except Exception as e:
            return {"method": "Chi-Square", "error": str(e), "p_value": 1.0, "drift_detected": False}

    def _create_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        drift_flags: list[bool] = []
        for key in ("mmd_result", "ks_results", "chi2_results", "label_shift"):
            r = results.get(key)
            if isinstance(r, dict) and "drift_detected" in r:
                drift_flags.append(bool(r.get("drift_detected")))
            if isinstance(r, dict) and "drift_rate" in r:
                drift_flags.append(bool(r.get("drift_rate", 0) > 0))
        drift_detected = any(drift_flags)
        return {"drift_detected": drift_detected}

