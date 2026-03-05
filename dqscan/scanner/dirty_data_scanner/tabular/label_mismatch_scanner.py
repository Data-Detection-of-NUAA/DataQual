# -*- coding: utf-8 -*-

"""
疑似错标（Label Mismatch）检测（Tabular / Classification）。

目标：识别“特征与标签明显不一致”的样本，输出可解释的疑似错标列表，便于人工复核。

MVP 算法：交叉验证一致性（cv_consistency）
- 对每条样本做 out-of-fold 预测概率
- 若模型对“真实标签”的置信度很低且预测类别与真实类别冲突，则判为疑似错标

注意：
- 该方法本质是“模型一致性启发式”，不是最终真值；输出应作为人工复核线索。
- 为避免数据泄漏，必须使用交叉验证的 out-of-fold 概率；否则结果会偏乐观。
"""

from __future__ import annotations

from typing import Any, Optional

from ...common.base_scanner import BaseScanner

try:
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from sklearn.compose import ColumnTransformer  # type: ignore
    from sklearn.impute import SimpleImputer  # type: ignore
    from sklearn.linear_model import LogisticRegression  # type: ignore
    from sklearn.model_selection import StratifiedKFold  # type: ignore
    from sklearn.pipeline import Pipeline  # type: ignore
    from sklearn.preprocessing import LabelEncoder, OneHotEncoder  # type: ignore

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class TabularLabelMismatchScanner(BaseScanner):
    """分类任务的疑似错标扫描器（需要 pandas/numpy/scikit-learn）。"""

    def __init__(
        self,
        *,
        executor_algorithm: str = "cv_consistency",
        n_splits: int = 5,
        threshold_prob_true: float = 0.2,
        threshold_prob_pred: float = 0.6,
        # confident_learning / confident_pruning_lite
        score_method: str = "self_confidence",
        filter_by: str = "both",
        fraction_noise: float = 0.05,
        max_samples: int = 5000,
        max_categorical_cardinality: int = 50,
        model: str = "logreg",
        seed: int = 42,
    ):
        super().__init__(name="TabularLabelMismatchScanner")
        self.executor_algorithm = str(executor_algorithm or "cv_consistency")
        self.n_splits = int(n_splits)
        self.threshold_prob_true = float(threshold_prob_true)
        self.threshold_prob_pred = float(threshold_prob_pred)
        self.score_method = str(score_method or "self_confidence")
        self.filter_by = str(filter_by or "both")
        self.fraction_noise = float(fraction_noise)
        self.max_samples = int(max_samples)
        self.max_categorical_cardinality = int(max_categorical_cardinality)
        self.model = str(model or "logreg")
        self.seed = int(seed)

    def scan(
        self,
        data: Any,
        *,
        label_column: str,
        exclude_columns: Optional[list[str]] = None,
        max_examples: int = 500,
    ) -> dict[str, Any]:
        if not (PANDAS_AVAILABLE and SKLEARN_AVAILABLE):
            missing = []
            if not PANDAS_AVAILABLE:
                missing.append("pandas/numpy")
            if not SKLEARN_AVAILABLE:
                missing.append("scikit-learn")
            return self._error_result(f"依赖缺失：{', '.join(missing)}；请安装后重试")

        assert PANDAS_AVAILABLE
        self.validate_data(data, pd.DataFrame)

        if self.check_empty(data):
            return self._error_result("数据为空")

        if not isinstance(label_column, str) or not label_column.strip():
            return self._error_result("label_column 不能为空")
        label_column = label_column.strip()
        if label_column not in data.columns:
            return self._error_result(f"label_column 不存在：{label_column}")

        exclude_set = set()
        if isinstance(exclude_columns, list):
            for x in exclude_columns:
                if isinstance(x, str) and x.strip():
                    exclude_set.add(x.strip())
        exclude_set.discard(label_column)

        # 仅保留 label 非空的样本
        df = data.copy()
        label_series = df[label_column]
        notnull_mask = ~label_series.isna()
        dropped_missing_label = int((~notnull_mask).sum())
        df = df.loc[notnull_mask].copy()
        if df.empty:
            return self._error_result("label 全为空，无法检测疑似错标")

        # label 编码（分类）
        y_raw = df[label_column].astype(str).values
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
        n_classes = int(len(le.classes_))
        if n_classes < 2:
            return self._error_result("类别数不足（<2），无法做分类错标检测")

        # 特征列：去掉 label 与 exclude_columns，并过滤高基数类别列
        feature_df = df.drop(columns=[label_column], errors="ignore")
        if exclude_set:
            feature_df = feature_df.drop(columns=[c for c in exclude_set if c in feature_df.columns], errors="ignore")

        if feature_df.shape[1] == 0:
            return self._error_result("无可用特征列（排除后为空）")

        # 自动剔除高基数类别列（常见：id/uuid/时间戳字符串等）
        categorical_cols = feature_df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        dropped_high_cardinality: list[str] = []
        if categorical_cols and self.max_categorical_cardinality > 0:
            keep_cats: list[str] = []
            for c in categorical_cols:
                try:
                    nunique = int(feature_df[c].nunique(dropna=True))
                except Exception:
                    nunique = 0
                if nunique > self.max_categorical_cardinality:
                    dropped_high_cardinality.append(str(c))
                else:
                    keep_cats.append(str(c))
            categorical_cols = keep_cats

        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()

        # 采样护栏：使用分层采样，尽量保留各类别
        n_total = int(len(feature_df))
        used_idx = np.arange(n_total)
        sampled = False
        if self.max_samples and n_total > self.max_samples:
            rng = np.random.default_rng(self.seed)
            sampled = True
            max_samples = int(self.max_samples)

            classes, counts = np.unique(y, return_counts=True)
            base_quota = max(1, max_samples // max(1, len(classes)))
            extra = max_samples % max(1, len(classes))
            selected: list[int] = []

            for cls in classes.tolist():
                cls_idx = np.where(y == cls)[0]
                quota = base_quota + (1 if extra > 0 else 0)
                if extra > 0:
                    extra -= 1
                k = min(int(len(cls_idx)), int(quota))
                if k <= 0:
                    continue
                selected.extend(rng.choice(cls_idx, size=k, replace=False).tolist())

            if len(selected) < max_samples:
                remaining = np.setdiff1d(used_idx, np.asarray(selected, dtype=int), assume_unique=False)
                need = max_samples - len(selected)
                if len(remaining) > 0 and need > 0:
                    selected.extend(
                        rng.choice(remaining, size=min(int(need), int(len(remaining))), replace=False).tolist()
                    )

            used_idx = np.asarray(sorted(set(selected)), dtype=int)
            feature_df = feature_df.iloc[used_idx].copy()
            y = y[used_idx]
            df = df.iloc[used_idx].copy()
            n_total = int(len(feature_df))

        # 交叉验证折数自适应：必须保证每类样本数 >= n_splits
        _, class_counts = np.unique(y, return_counts=True)
        min_class_count = int(class_counts.min())
        n_splits = int(min(self.n_splits, min_class_count))
        if n_splits < 2:
            return self._error_result("每个类别样本数过少，无法进行交叉验证一致性检测")

        # 预处理：数值列/类别列分别处理（含缺失值）
        transformers: list[tuple[str, Any, list[str]]] = []
        if numeric_cols:
            num_pipe = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
            transformers.append(("num", num_pipe, [str(c) for c in numeric_cols]))
        if categorical_cols:
            cat_pipe = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", self._one_hot_encoder()),
                ]
            )
            transformers.append(("cat", cat_pipe, [str(c) for c in categorical_cols]))

        if not transformers:
            return self._error_result("没有可用特征列（数值/类别均为空）")

        preprocess = ColumnTransformer(transformers=transformers, remainder="drop")

        clf = self._build_classifier()
        pipe = Pipeline(steps=[("preprocess", preprocess), ("clf", clf)])

        try:
            oof_proba = self._compute_oof_pred_proba(
                feature_df=feature_df,
                y=y,
                n_classes=n_classes,
                n_splits=n_splits,
                pipe=pipe,
            )
        except Exception as e:
            return self._error_result(f"训练/预测失败：{e}")

        if np.isnan(oof_proba).any():
            return self._error_result("out-of-fold 概率存在缺失（可能是分层失败或数据异常）")

        executor = str(self.executor_algorithm or "").strip().lower()
        if not executor:
            executor = "cv_consistency"

        if executor in {"confident_learning", "confident_pruning_lite", "cl"}:
            method_res = self._detect_confident_learning(
                df=df,
                y=y,
                le=le,
                oof_proba=oof_proba,
                label_column=label_column,
                max_examples=max_examples,
            )
        else:
            method_res = self._detect_cv_consistency(
                df=df,
                y=y,
                le=le,
                oof_proba=oof_proba,
                label_column=label_column,
                max_examples=max_examples,
            )

        results: dict[str, Any] = {
            "algorithm": method_res.get("algorithm") or ("CV Consistency (Classification)" if executor == "cv_consistency" else "Label Mismatch"),
            "executor_algorithm": executor,
            "label_column": label_column,
            "total_samples": int(len(data)),
            "used_samples": int(n_total),
            "dropped_missing_label": int(dropped_missing_label),
            "n_classes": int(n_classes),
            "classes": [str(x) for x in le.classes_.tolist()][:50],
            "n_splits": int(n_splits),
            "threshold_prob_true": float(self.threshold_prob_true),
            "threshold_prob_pred": float(self.threshold_prob_pred),
            "score_method": str(self.score_method),
            "filter_by": str(self.filter_by),
            "fraction_noise": float(self.fraction_noise),
            "max_samples": int(self.max_samples),
            "max_categorical_cardinality": int(self.max_categorical_cardinality),
            "excluded_columns": sorted(exclude_set),
            "dropped_high_cardinality_columns": dropped_high_cardinality[:50],
            "sampled": bool(sampled),
            "label_mismatch_count": int(method_res.get("label_mismatch_count", 0) or 0),
            "label_mismatch_rate": float(method_res.get("label_mismatch_rate", 0.0) or 0.0),
            "has_issues": bool(method_res.get("label_mismatch_count", 0) or 0),
            "total_issues": int(method_res.get("label_mismatch_count", 0) or 0),
            "issue_percentage": float(method_res.get("label_mismatch_rate", 0.0) or 0.0),
            "detailed_issues": method_res.get("detailed_issues") if isinstance(method_res.get("detailed_issues"), list) else [],
        }
        # 结构化解释（可选）
        if isinstance(method_res.get("per_class_issue_rate"), dict):
            results["per_class_issue_rate"] = method_res.get("per_class_issue_rate")
        if isinstance(method_res.get("confusion_pairs_top"), list):
            results["confusion_pairs_top"] = method_res.get("confusion_pairs_top")
        if self.model:
            results["model"] = self.model
        return results

    def _compute_oof_pred_proba(
        self,
        *,
        feature_df: "pd.DataFrame",
        y: "np.ndarray",
        n_classes: int,
        n_splits: int,
        pipe: Any,
    ) -> "np.ndarray":
        """生成 out-of-fold 的 `predict_proba`（n×K）。"""
        n_total = int(len(feature_df))
        oof_proba = np.full((n_total, int(n_classes)), np.nan, dtype=float)
        skf = StratifiedKFold(n_splits=int(n_splits), shuffle=True, random_state=self.seed)
        for train_idx, test_idx in skf.split(feature_df, y):
            X_train = feature_df.iloc[train_idx]
            y_train = y[train_idx]
            X_test = feature_df.iloc[test_idx]
            pipe.fit(X_train, y_train)
            proba = pipe.predict_proba(X_test)
            if proba.shape[1] != int(n_classes):
                raise ValueError("交叉验证中类别维度不一致（类别过少或分布异常）")
            oof_proba[test_idx, :] = proba
        return oof_proba

    def _detect_cv_consistency(
        self,
        *,
        df: "pd.DataFrame",
        y: "np.ndarray",
        le: Any,
        oof_proba: "np.ndarray",
        label_column: str,
        max_examples: int,
    ) -> dict[str, Any]:
        n_total = int(len(df))
        prob_true = oof_proba[np.arange(n_total), y]
        pred = oof_proba.argmax(axis=1)
        prob_pred = oof_proba.max(axis=1)
        margin = prob_pred - prob_true

        suspicious = (pred != y) & (prob_true <= self.threshold_prob_true) & (prob_pred >= self.threshold_prob_pred)
        suspicious_idx = np.where(suspicious)[0]

        suspected_count = int(len(suspicious_idx))
        suspected_rate = float(suspected_count / max(n_total, 1))

        max_examples = int(max(10, min(int(max_examples or 50), 500)))
        order = suspicious_idx[np.argsort(-margin[suspicious_idx])] if suspected_count > 0 else np.array([], dtype=int)

        issues: list[dict[str, Any]] = []
        for rank, i in enumerate(order[:max_examples].tolist(), start=1):
            row_id = self._row_id(df, i)
            given_label = le.inverse_transform([int(y[i])])[0]
            suggested_label = le.inverse_transform([int(pred[i])])[0]
            pt = float(prob_true[i])
            pp = float(prob_pred[i])
            sev = "severe" if (pt < 0.05 and pp > 0.9) else "moderate" if (pt < 0.1 and pp > 0.8) else "light"
            issues.append(
                {
                    "data_id": row_id,
                    "issue_type": "疑似错标",
                    "severity": sev,
                    "details": {
                        "label_column": label_column,
                        "given_label": given_label,
                        "suggested_label": suggested_label,
                        "prob_given": round(pt, 6),
                        "prob_suggested": round(pp, 6),
                        "margin": round(float(margin[i]), 6),
                        "rank": int(rank),
                        "reason": "cv_consistency_low_prob_given_and_confident_other",
                        "row_preview": self._row_preview(df, int(i)),
                    },
                }
            )

        return {
            "algorithm": "CV Consistency (Classification)",
            "label_mismatch_count": suspected_count,
            "label_mismatch_rate": suspected_rate,
            "detailed_issues": issues,
        }

    def _detect_confident_learning(
        self,
        *,
        df: "pd.DataFrame",
        y: "np.ndarray",
        le: Any,
        oof_proba: "np.ndarray",
        label_column: str,
        max_examples: int,
    ) -> dict[str, Any]:
        """
        Confident Learning（lite）：基于 out-of-fold 概率的打分 + pruning 策略（按类配额）。
        说明：这是 cleanlab 风格的“可疑样本排序/剪枝”近似实现，用于候选集生成与解释。
        """
        n_total = int(len(df))
        n_classes = int(oof_proba.shape[1])

        given_prob = oof_proba[np.arange(n_total), y]
        pred = oof_proba.argmax(axis=1)
        pred_prob = oof_proba.max(axis=1)

        # max other prob
        tmp = oof_proba.copy()
        tmp[np.arange(n_total), y] = -1.0
        other_prob = tmp.max(axis=1)

        eps = 1e-12
        normalized_margin = (given_prob - other_prob) / (given_prob + other_prob + eps)

        # normalized entropy in [0,1]
        safe = np.clip(oof_proba, eps, 1.0)
        entropy = -np.sum(safe * np.log(safe), axis=1) / max(np.log(max(n_classes, 2)), eps)

        score_method = str(self.score_method or "self_confidence").strip().lower()
        if score_method in {"self_confidence", "confidence", "prob_given"}:
            quality = given_prob
        elif score_method in {"normalized_margin", "margin"}:
            quality = normalized_margin
        elif score_method in {"confidence_weighted_entropy", "cwe"}:
            quality = given_prob * (1.0 - entropy)
        else:
            # 默认：self_confidence
            score_method = "self_confidence"
            quality = given_prob

        filter_by = str(self.filter_by or "both").strip().lower()
        fraction_noise = float(self.fraction_noise)
        if not np.isfinite(fraction_noise) or fraction_noise < 0:
            fraction_noise = 0.0
        if fraction_noise > 1:
            fraction_noise = 1.0

        # 1) confident flips（高置信替代标签 & 低给定标签置信度）
        confident_flip = (pred != y) & (given_prob <= self.threshold_prob_true) & (pred_prob >= self.threshold_prob_pred)

        selected: set[int] = set()

        def _select_bottom_by_class(quota_by_class: dict[int, int]) -> set[int]:
            out: set[int] = set()
            for cls, quota in quota_by_class.items():
                if quota <= 0:
                    continue
                # 仅从“模型预测 != 给定标签”的样本里选（避免把纯边界/不确定样本全部当成错标）
                cls_idx = np.where((y == int(cls)) & (pred != y))[0]
                if cls_idx.size == 0:
                    continue
                # 按质量从低到高
                order = cls_idx[np.argsort(quality[cls_idx])]
                out.update(order[: int(min(int(quota), int(order.size)))].tolist())
            return out

        # 2) pruning 策略
        classes, counts = np.unique(y, return_counts=True)
        counts_by_class = {int(c): int(n) for c, n in zip(classes.tolist(), counts.tolist())}

        if filter_by in {"confident_learning"}:
            selected = set(np.where(confident_flip)[0].tolist())
        else:
            if filter_by in {"prune_by_class", "both"}:
                quota = {c: int(np.ceil(fraction_noise * cnt)) for c, cnt in counts_by_class.items()}
                selected |= _select_bottom_by_class(quota)
            if filter_by in {"prune_by_noise_rate", "both"}:
                noise_rate = {}
                for c, cnt in counts_by_class.items():
                    if cnt <= 0:
                        noise_rate[c] = 0.0
                        continue
                    idx = np.where(y == int(c))[0]
                    noise_rate[c] = float(confident_flip[idx].mean()) if idx.size else 0.0
                quota = {c: int(np.ceil(noise_rate[c] * counts_by_class[c])) for c in counts_by_class}
                selected |= _select_bottom_by_class(quota)
            # 无论策略如何，confident_flip 都应强制纳入（强信号）
            selected |= set(np.where(confident_flip)[0].tolist())

        selected_idx = np.asarray(sorted(selected), dtype=int)

        suspected_count = int(selected_idx.size)
        suspected_rate = float(suspected_count / max(n_total, 1))

        # 排序：优先展示“质量最低”的
        max_examples = int(max(10, min(int(max_examples or 50), 500)))
        if suspected_count > 0:
            order = selected_idx[np.argsort(quality[selected_idx])]
        else:
            order = np.array([], dtype=int)

        # per-class issue rate（按给定标签统计）
        per_class_issue_rate: dict[str, float] = {}
        if n_total > 0:
            for c, cnt in counts_by_class.items():
                if cnt <= 0:
                    continue
                cls_name = str(le.inverse_transform([int(c)])[0])
                in_cls = np.where(y == int(c))[0]
                if in_cls.size == 0:
                    continue
                cls_selected = np.intersect1d(in_cls, selected_idx, assume_unique=False)
                per_class_issue_rate[cls_name] = float(len(cls_selected) / max(int(cnt), 1))

        # confusion pairs（Top）
        confusion_counts: dict[tuple[str, str], int] = {}
        for i in selected_idx.tolist():
            g = str(le.inverse_transform([int(y[i])])[0])
            s = str(le.inverse_transform([int(pred[i])])[0])
            if g == s:
                continue
            key = (g, s)
            confusion_counts[key] = confusion_counts.get(key, 0) + 1
        confusion_pairs_top = [
            {"given_label": k[0], "suggested_label": k[1], "count": int(v)}
            for k, v in sorted(confusion_counts.items(), key=lambda kv: -kv[1])[:20]
        ]

        issues: list[dict[str, Any]] = []
        for rank, i in enumerate(order[:max_examples].tolist(), start=1):
            row_id = self._row_id(df, i)
            given_label = le.inverse_transform([int(y[i])])[0]
            suggested_label = le.inverse_transform([int(pred[i])])[0]
            gprob = float(given_prob[i])
            sprob = float(pred_prob[i])
            m = float(sprob - gprob)
            ent = float(entropy[i])
            sev = (
                "severe"
                if (pred[i] != y[i] and gprob <= self.threshold_prob_true and sprob >= self.threshold_prob_pred)
                else "moderate"
                if (pred[i] != y[i] and m >= 0.3 and gprob <= 0.5)
                else "light"
            )
            reason = (
                "confident_learning_confident_flip"
                if (pred[i] != y[i] and gprob <= self.threshold_prob_true and sprob >= self.threshold_prob_pred)
                else "confident_learning_low_quality"
            )
            issues.append(
                {
                    "data_id": row_id,
                    "issue_type": "疑似错标",
                    "severity": sev,
                    "details": {
                        "label_column": label_column,
                        "given_label": given_label,
                        "suggested_label": suggested_label,
                        "score": round(float(quality[i]), 6),
                        "score_method": score_method,
                        "prob_given": round(gprob, 6),
                        "prob_suggested": round(sprob, 6),
                        "normalized_margin": round(float(normalized_margin[i]), 6),
                        "entropy": round(ent, 6),
                        "margin": round(m, 6),
                        "rank": int(rank),
                        "reason": reason,
                        "row_preview": self._row_preview(df, int(i)),
                    },
                }
            )

        return {
            "algorithm": "Confident Learning (Lite)",
            "label_mismatch_count": suspected_count,
            "label_mismatch_rate": suspected_rate,
            "detailed_issues": issues,
            "per_class_issue_rate": per_class_issue_rate,
            "confusion_pairs_top": confusion_pairs_top,
        }

    def _row_id(self, df: "pd.DataFrame", i: int) -> Any:
        try:
            idx = df.index[i]
            return int(idx) if str(idx).isdigit() else idx
        except Exception:
            return int(i)

    def _row_preview(self, df: "pd.DataFrame", i: int, *, max_fields: int = 30) -> dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return {}
        try:
            row = df.iloc[int(i)]
        except Exception:
            return {}

        cols = list(df.columns)[: int(max_fields)]
        preview: dict[str, Any] = {}
        for c in cols:
            try:
                v = row.get(c)
            except Exception:
                v = None
            try:
                if pd.isna(v):
                    v = None
            except Exception:
                pass
            if isinstance(v, str) and len(v) > 200:
                v = v[:200] + "…"
            preview[str(c)] = v
        return preview

    def _one_hot_encoder(self):
        try:
            return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
        except TypeError:
            # sklearn<1.2 兼容
            return OneHotEncoder(handle_unknown="ignore", sparse=True)

    def _build_classifier(self):
        if self.model.lower() not in {"logreg", "logistic_regression"}:
            # MVP 先支持 logreg；未来可扩展 rf/xgb 等
            self.model = "logreg"
        return LogisticRegression(
            max_iter=300,
            solver="saga",
            random_state=self.seed,
            n_jobs=1,
        )
