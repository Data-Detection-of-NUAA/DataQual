# -*- coding: utf-8 -*-

from __future__ import annotations


def test_label_mismatch_cv_consistency_detects_flipped_labels():
    import numpy as np
    import pandas as pd
    from sklearn.datasets import make_classification

    from dqscan.scanner import TabularLabelMismatchScanner

    X, y = make_classification(
        n_samples=500,
        n_features=6,
        n_informative=6,
        n_redundant=0,
        n_classes=2,
        class_sep=2.5,
        flip_y=0.0,
        random_state=42,
    )

    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
    df["id"] = [f"id_{i:04d}" for i in range(len(df))]  # 高基数类别列，应被自动剔除
    df["source"] = np.where(np.arange(len(df)) % 2 == 0, "A", "B")  # 低基数类别列，应保留
    df["label"] = np.where(y == 1, "pos", "neg")

    rng = np.random.default_rng(7)
    flipped_idx = rng.choice(len(df), size=50, replace=False)
    df.loc[flipped_idx, "label"] = np.where(df.loc[flipped_idx, "label"] == "pos", "neg", "pos")

    scanner = TabularLabelMismatchScanner(
        n_splits=5,
        threshold_prob_true=0.2,
        threshold_prob_pred=0.8,
        max_samples=5000,
        max_categorical_cardinality=50,
        seed=42,
    )
    res = scanner.scan(df, label_column="label", max_examples=200)
    assert "error" not in res
    assert res["used_samples"] == 500
    assert res["n_classes"] == 2

    issues = res.get("detailed_issues") or []
    detected = {int(x["data_id"]) for x in issues if isinstance(x, dict) and "data_id" in x}
    overlap = len(detected.intersection({int(i) for i in flipped_idx.tolist()}))
    assert overlap >= 10


def test_label_mismatch_confident_learning_detects_flipped_labels():
    import numpy as np
    import pandas as pd
    from sklearn.datasets import make_classification

    from dqscan.scanner import TabularLabelMismatchScanner

    X, y = make_classification(
        n_samples=500,
        n_features=6,
        n_informative=6,
        n_redundant=0,
        n_classes=2,
        class_sep=2.5,
        flip_y=0.0,
        random_state=42,
    )

    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
    df["id"] = [f"id_{i:04d}" for i in range(len(df))]
    df["label"] = np.where(y == 1, "pos", "neg")

    rng = np.random.default_rng(7)
    flipped_idx = rng.choice(len(df), size=50, replace=False)
    df.loc[flipped_idx, "label"] = np.where(df.loc[flipped_idx, "label"] == "pos", "neg", "pos")

    scanner = TabularLabelMismatchScanner(
        executor_algorithm="confident_learning",
        n_splits=5,
        threshold_prob_true=0.2,
        threshold_prob_pred=0.8,
        score_method="self_confidence",
        filter_by="both",
        fraction_noise=0.02,
        seed=42,
    )
    res = scanner.scan(df, label_column="label", max_examples=200)
    assert "error" not in res
    assert res["used_samples"] == 500
    assert res["n_classes"] == 2

    issues = res.get("detailed_issues") or []
    detected = {int(x["data_id"]) for x in issues if isinstance(x, dict) and "data_id" in x}
    overlap = len(detected.intersection({int(i) for i in flipped_idx.tolist()}))
    assert overlap >= 10
