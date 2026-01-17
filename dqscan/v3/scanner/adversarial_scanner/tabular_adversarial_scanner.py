# -*- coding: utf-8 -*-

"""
对抗性检测（Tabular）。

本模块的目标是给出一个“模型是否容易被小扰动攻击翻车”的粗粒度信号。

- 优先使用 IBM ART（如已安装）执行 ZOO 黑盒攻击
- 未安装 ART 时，使用随机扰动搜索的降级攻击，保证整体流程可运行
"""

from __future__ import annotations

from typing import Any, Optional

from ..common.base_scanner import BaseScanner

try:
    import numpy as np  # type: ignore

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.base import BaseEstimator  # type: ignore

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# IBM ART (optional)
try:
    from art.attacks.evasion import ZooAttack  # type: ignore
    from art.estimators.classification import SklearnClassifier  # type: ignore

    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False


class TabularAdversarialScanner(BaseScanner):
    """
    表格对抗性扫描器（V3）

    - 优先使用 IBM ART 的 ZOO 攻击（如已安装）
    - 否则使用随机搜索扰动的降级攻击，保证可运行与可评分
    """

    def __init__(
        self,
        max_iter: int = 100,
        learning_rate: float = 0.01,
        confidence: float = 0.0,
        batch_size: int = 1,
        epsilon: float = 0.05,
        random_trials: int = 40,
        random_features: int = 3,
        seed: int = 42,
    ):
        super().__init__(name="TabularAdversarialScanner")
        self.max_iter = max_iter
        self.learning_rate = learning_rate
        self.confidence = confidence
        self.batch_size = batch_size
        self.epsilon = epsilon
        self.random_trials = random_trials
        self.random_features = random_features
        self.seed = seed

    def scan(
        self,
        model: Any,
        data: Any,
        labels: Any,
        feature_names: Optional[list[str]] = None,
        num_classes: Optional[int] = None,
        clip_values: Optional[tuple[float, float]] = None,
        model_type: str = "sklearn",
        max_samples: int = 100,
    ) -> dict[str, Any]:
        if not (NUMPY_AVAILABLE and SKLEARN_AVAILABLE):
            missing = []
            if not NUMPY_AVAILABLE:
                missing.append("numpy")
            if not SKLEARN_AVAILABLE:
                missing.append("scikit-learn")
            return self._error_result(f"依赖缺失：{', '.join(missing)}；请安装后重试")

        assert NUMPY_AVAILABLE and SKLEARN_AVAILABLE
        if model_type != "sklearn":
            return self._error_result("当前系统MVP仅支持 sklearn 模型类型的对抗性扫描")

        if not isinstance(model, BaseEstimator):
            return self._error_result("sklearn 模型不合法（不是 BaseEstimator）")

        X = np.asarray(data, dtype=np.float32)
        y = np.asarray(labels, dtype=np.int64)
        if X.ndim != 2 or len(X) == 0:
            return self._error_result("data 为空或维度不正确，期望二维数组")
        if len(y) != len(X):
            return self._error_result("labels 长度与 data 不一致")

        if len(X) > max_samples:
            rng = np.random.default_rng(self.seed)
            idx = rng.choice(len(X), size=max_samples, replace=False)
            X = X[idx]
            y = y[idx]

        if clip_values is None:
            clip_values = (float(np.min(X)), float(np.max(X)))

        results: dict[str, Any] = {
            "algorithm": "ZOO (IBM ART)" if ART_AVAILABLE else "Random Search Attack (Fallback)",
            "total_samples": int(len(X)),
            "num_features": int(X.shape[1]),
            "max_iter": self.max_iter,
            "learning_rate": self.learning_rate,
        }

        # 原始预测
        try:
            original_preds = model.predict(X)
            original_accuracy = float(np.mean(original_preds == y))
        except Exception as e:
            return self._error_result(f"原始预测失败: {e}")

        results["original_accuracy"] = original_accuracy

        if ART_AVAILABLE:
            try:
                classifier = SklearnClassifier(model=model, clip_values=clip_values)
                attack = ZooAttack(
                    classifier=classifier,
                    confidence=self.confidence,
                    learning_rate=self.learning_rate,
                    max_iter=self.max_iter,
                    batch_size=self.batch_size,
                    verbose=False,
                )
                adv_X = attack.generate(x=X)
                adv_preds = model.predict(adv_X)
                adv_accuracy = float(np.mean(adv_preds == y))

                correctly = original_preds == y
                attacked = (adv_preds != y) & correctly
                denom = int(np.sum(correctly))
                attack_success_rate = float(np.sum(attacked) / denom) if denom > 0 else 0.0
                results["adversarial_accuracy"] = adv_accuracy
                results["attack_success_rate"] = attack_success_rate
                results["robustness_score"] = float(1.0 - attack_success_rate)
                return self._finalize(results, X, y, original_preds, adv_preds, attacked, feature_names)
            except Exception as e:
                results["warning"] = f"ZOO不可用，使用降级攻击：{e}"

        # 降级随机攻击：在原本预测正确的样本上尝试有限次扰动翻转预测
        rng = np.random.default_rng(self.seed)
        correctly = original_preds == y
        success = np.zeros(len(X), dtype=bool)
        adv_preds = np.array(original_preds, copy=True)

        feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        lo, hi = clip_values
        scale = (hi - lo) if hi > lo else 1.0
        eps = float(self.epsilon) * scale

        for i in range(len(X)):
            if not correctly[i]:
                continue
            x0 = X[i].copy()
            for _ in range(self.random_trials):
                x = x0.copy()
                k = min(self.random_features, x.shape[0])
                feat_idx = rng.choice(x.shape[0], size=k, replace=False)
                noise = rng.normal(loc=0.0, scale=eps, size=k).astype(np.float32)
                x[feat_idx] = np.clip(x[feat_idx] + noise, lo, hi)
                try:
                    p = model.predict(x.reshape(1, -1))[0]
                except Exception:
                    continue
                if p != y[i]:
                    success[i] = True
                    adv_preds[i] = p
                    break

        denom = int(np.sum(correctly))
        attack_success_rate = float(np.sum(success) / denom) if denom > 0 else 0.0
        results["attack_success_rate"] = float(attack_success_rate)
        results["robustness_score"] = float(1.0 - attack_success_rate)
        results["adversarial_accuracy"] = float(np.mean(adv_preds == y))
        return self._finalize(results, X, y, original_preds, adv_preds, success, feature_names)

    def _finalize(
        self,
        results: dict[str, Any],
        X: "np.ndarray",
        y: "np.ndarray",
        original_preds: "np.ndarray",
        adversarial_preds: "np.ndarray",
        successful_attacks: "np.ndarray",
        feature_names: list[str] | None,
    ) -> dict[str, Any]:
        attack_success_rate = float(results.get("attack_success_rate", 0.0))
        results["has_issues"] = attack_success_rate > 0.1
        results["total_issues"] = int(np.sum(successful_attacks))
        results["issue_percentage"] = float(attack_success_rate)

        detailed_issues: list[dict[str, Any]] = []
        attack_indices = np.where(successful_attacks)[0]
        for idx in attack_indices[:50]:
            detailed_issues.append(
                {
                    "data_id": int(idx),
                    "issue_type": "对抗样本攻击成功",
                    "severity": self._get_severity(attack_success_rate),
                    "details": {
                        "original_label": int(y[idx]),
                        "original_pred": int(original_preds[idx]),
                        "adversarial_pred": int(adversarial_preds[idx]),
                    },
                }
            )
        results["detailed_issues"] = detailed_issues
        return results

    def _get_severity(self, attack_success_rate: float) -> str:
        if attack_success_rate > 0.5:
            return "severe"
        if attack_success_rate > 0.3:
            return "moderate"
        return "light"
