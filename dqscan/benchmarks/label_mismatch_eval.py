#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reproducible evaluation for dqscan `dirty_data.label_mismatch` (tabular classification).

Why this exists:
- Public datasets typically do not provide "true mislabeled indices".
- We inject synthetic label noise (uniform / class-conditional) and keep the flipped indices
  as ground-truth to compute precision/recall.

Run (recommended with repo venv):
  `./.venv/bin/python dqscan/benchmarks/label_mismatch_eval.py`
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any, Iterable
import warnings


def _require_deps():
    try:
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
        from sklearn import __version__ as _sk_version  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "Missing dependencies. Please run with the project venv:\n"
            "  `./.venv/bin/python dqscan/benchmarks/label_mismatch_eval.py`\n"
            f"Original error: {e}"
        ) from e


_require_deps()

import numpy as np  # type: ignore  # noqa: E402
import pandas as pd  # type: ignore  # noqa: E402
from sklearn.datasets import load_breast_cancer, load_digits, load_wine  # type: ignore  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # type: ignore  # noqa: E402

# Allow running as a script: `python dqscan/benchmarks/label_mismatch_eval.py`
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dqscan.scanner import TabularLabelMismatchScanner  # noqa: E402

# Keep benchmark output readable; convergence warnings do not affect the metric computation here.
warnings.filterwarnings("ignore", category=ConvergenceWarning)


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    label_column: str
    source: str
    license: str


@dataclass(frozen=True)
class RunSpec:
    dataset: str
    noise_mode: str
    noise_fraction: float
    executor_algorithm: str
    n_splits: int
    threshold_prob_true: float
    threshold_prob_pred: float
    score_method: str
    filter_by: str
    fraction_noise: float
    seed: int


@dataclass(frozen=True)
class RunResult:
    spec: RunSpec
    n_samples: int
    n_classes: int
    n_flipped: int
    detected_issues: int
    detected_total_count: int
    tp_at_all: int
    precision_at_all: float
    recall_at_all: float
    precision_at_k: dict[int, float]
    recall_at_k: dict[int, float]
    elapsed_s: float


def _parse_csv_list(s: str) -> list[str]:
    parts = [x.strip() for x in (s or "").split(",")]
    return [p for p in parts if p]


def _parse_csv_floats(s: str) -> list[float]:
    out: list[float] = []
    for x in _parse_csv_list(s):
        out.append(float(x))
    return out


def _load_dataset(name: str) -> tuple[DatasetSpec, pd.DataFrame]:
    ds = str(name or "").strip().lower()
    if ds in {"breast_cancer", "cancer", "bc"}:
        data = load_breast_cancer(as_frame=True)
        df = data.frame.copy()
        df["label"] = df["target"].astype(int)
        df = df.drop(columns=["target"])
        return (
            DatasetSpec(
                name="breast_cancer",
                label_column="label",
                source="UCI Machine Learning Repository: Breast Cancer Wisconsin (Diagnostic) (id=17)",
                license="CC BY 4.0",
            ),
            df,
        )
    if ds in {"digits", "mnist8x8"}:
        data = load_digits()
        X = np.asarray(data.data)
        df = pd.DataFrame(X, columns=[f"pixel_{i}" for i in range(X.shape[1])])
        df["label"] = np.asarray(data.target).astype(int)
        return (
            DatasetSpec(
                name="digits",
                label_column="label",
                source="UCI Machine Learning Repository: Optical Recognition of Handwritten Digits (id=80) (sklearn provides an 8x8 variant/subset)",
                license="CC BY 4.0",
            ),
            df,
        )
    if ds in {"wine"}:
        data = load_wine(as_frame=True)
        df = data.frame.copy()
        df["label"] = df["target"].astype(int)
        df = df.drop(columns=["target"])
        return (
            DatasetSpec(
                name="wine",
                label_column="label",
                source="UCI Machine Learning Repository: Wine (id=109)",
                license="CC BY 4.0",
            ),
            df,
        )
    raise ValueError(f"Unknown dataset: {name} (supported: breast_cancer,digits,wine)")


def _shift_mapping(classes: np.ndarray) -> dict[Any, Any]:
    uniq = classes.tolist()
    if len(uniq) < 2:
        return {}
    return {uniq[i]: uniq[(i + 1) % len(uniq)] for i in range(len(uniq))}


def _inject_noise(
    *,
    y: np.ndarray,
    noise_fraction: float,
    noise_mode: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (y_noisy, flipped_indices)."""
    y = np.asarray(y)
    n = int(y.shape[0])
    if n <= 0:
        return y.copy(), np.asarray([], dtype=int)

    frac = float(noise_fraction)
    if not np.isfinite(frac) or frac <= 0:
        return y.copy(), np.asarray([], dtype=int)
    if frac >= 1:
        frac = 1.0

    rng = np.random.default_rng(int(seed))
    n_flip = int(np.floor(frac * n))
    if n_flip <= 0:
        return y.copy(), np.asarray([], dtype=int)

    flipped = rng.choice(n, size=n_flip, replace=False)
    y_noisy = y.copy()
    classes = np.unique(y_noisy)
    if classes.size < 2:
        return y.copy(), np.asarray([], dtype=int)

    mode = str(noise_mode or "uniform").strip().lower()
    if mode in {"class_conditional", "class-conditional", "cc"}:
        mapping = _shift_mapping(classes)
        for i in flipped.tolist():
            y_noisy[i] = mapping.get(y_noisy[i], y_noisy[i])
    else:
        # uniform: random other class
        for i in flipped.tolist():
            cur = y_noisy[i]
            other = classes[classes != cur]
            y_noisy[i] = rng.choice(other, size=1)[0]

    return y_noisy, np.asarray(flipped, dtype=int)


def _to_int_id(x: Any) -> int | None:
    try:
        if isinstance(x, (int, np.integer)):
            return int(x)
        s = str(x)
        return int(s) if s.isdigit() else None
    except Exception:
        return None


def _precision_recall_at_k(
    *,
    ranked_ids: list[int],
    flipped_set: set[int],
    k: int,
) -> tuple[float, float, int]:
    k = int(k)
    if k <= 0:
        return 0.0, 0.0, 0
    topk = ranked_ids[: min(k, len(ranked_ids))]
    tp = len(set(topk).intersection(flipped_set))
    precision = float(tp / max(len(topk), 1))
    recall = float(tp / max(len(flipped_set), 1))
    return precision, recall, tp


def _run_once(
    *,
    dataset_name: str,
    noise_mode: str,
    noise_fraction: float,
    executor_algorithm: str,
    n_splits: int,
    threshold_prob_true: float,
    threshold_prob_pred: float,
    score_method: str,
    filter_by: str,
    fraction_noise: float | None,
    seed: int,
    max_examples: int,
) -> RunResult:
    ds_spec, df = _load_dataset(dataset_name)
    label_column = ds_spec.label_column

    y_clean = df[label_column].to_numpy()
    y_noisy, flipped_idx = _inject_noise(y=y_clean, noise_fraction=noise_fraction, noise_mode=noise_mode, seed=seed)
    df_noisy = df.copy()
    df_noisy[label_column] = y_noisy
    flipped_set = {int(i) for i in flipped_idx.tolist()}

    frac_noise = float(noise_fraction if fraction_noise is None else fraction_noise)
    frac_noise = float(np.clip(frac_noise, 0.0, 1.0))

    scanner = TabularLabelMismatchScanner(
        executor_algorithm=executor_algorithm,
        n_splits=int(n_splits),
        threshold_prob_true=float(threshold_prob_true),
        threshold_prob_pred=float(threshold_prob_pred),
        score_method=str(score_method),
        filter_by=str(filter_by),
        fraction_noise=float(frac_noise),
        max_samples=1000000,
        seed=int(seed),
    )

    t0 = time.perf_counter()
    res = scanner.scan(df_noisy, label_column=label_column, max_examples=int(max_examples))
    elapsed = float(time.perf_counter() - t0)
    if "error" in res:
        raise RuntimeError(f"scanner error: {res.get('error')}")

    issues = res.get("detailed_issues") or []
    ranked_ids: list[int] = []
    for it in issues:
        if not isinstance(it, dict):
            continue
        raw_id = it.get("data_id")
        iid = _to_int_id(raw_id)
        if iid is not None:
            ranked_ids.append(int(iid))

    # deduplicate while preserving order
    ranked_ids = list(dict.fromkeys(ranked_ids))

    tp_all = len(set(ranked_ids).intersection(flipped_set))
    precision_all = float(tp_all / max(len(ranked_ids), 1))
    recall_all = float(tp_all / max(len(flipped_set), 1))

    # k suggestions:
    ks: list[int] = []
    for k in [10, 20, 50, 100, len(flipped_set)]:
        if k and k > 0:
            ks.append(int(k))
    ks = sorted(set(ks))

    precision_at_k: dict[int, float] = {}
    recall_at_k: dict[int, float] = {}
    for k in ks:
        p, r, _ = _precision_recall_at_k(ranked_ids=ranked_ids, flipped_set=flipped_set, k=k)
        precision_at_k[int(k)] = float(p)
        recall_at_k[int(k)] = float(r)

    return RunResult(
        spec=RunSpec(
            dataset=str(ds_spec.name),
            noise_mode=str(noise_mode),
            noise_fraction=float(noise_fraction),
            executor_algorithm=str(executor_algorithm),
            n_splits=int(res.get("n_splits") or n_splits),
            threshold_prob_true=float(threshold_prob_true),
            threshold_prob_pred=float(threshold_prob_pred),
            score_method=str(score_method),
            filter_by=str(filter_by),
            fraction_noise=float(frac_noise),
            seed=int(seed),
        ),
        n_samples=int(len(df_noisy)),
        n_classes=int(res.get("n_classes") or 0),
        n_flipped=int(len(flipped_set)),
        detected_issues=int(len(ranked_ids)),
        detected_total_count=int(res.get("label_mismatch_count") or 0),
        tp_at_all=int(tp_all),
        precision_at_all=float(precision_all),
        recall_at_all=float(recall_all),
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        elapsed_s=float(elapsed),
    )


def _format_percent(x: float) -> str:
    try:
        return f"{100.0 * float(x):.1f}%"
    except Exception:
        return "NA"


def _print_results(results: Iterable[RunResult]) -> None:
    results = list(results)
    if not results:
        print("No results.")
        return

    # grouped output; keep it human-readable without extra deps.
    for rr in results:
        s = rr.spec
        print(
            f"[{s.dataset}] mode={s.noise_mode} noise={s.noise_fraction:.3f} "
            f"algo={s.executor_algorithm} n_flipped={rr.n_flipped} "
            f"detected={rr.detected_issues} tp={rr.tp_at_all} "
            f"P={_format_percent(rr.precision_at_all)} R={_format_percent(rr.recall_at_all)} "
            f"time={rr.elapsed_s:.2f}s"
        )
        if rr.precision_at_k:
            ks = sorted(rr.precision_at_k.keys())
            row = []
            for k in ks:
                row.append(f"k={k}: P={_format_percent(rr.precision_at_k[k])}, R={_format_percent(rr.recall_at_k[k])}")
            print("  " + " | ".join(row))
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate dqscan label_mismatch on open datasets with injected label noise.")
    parser.add_argument("--datasets", default="breast_cancer,digits", help="Comma-separated: breast_cancer,digits,wine")
    parser.add_argument("--noise-modes", default="uniform,class_conditional", help="Comma-separated: uniform,class_conditional")
    parser.add_argument("--noise-fractions", default="0.05,0.10", help="Comma-separated floats, e.g. 0.05,0.10")
    parser.add_argument("--executors", default="cv_consistency,confident_learning", help="Comma-separated: cv_consistency,confident_learning")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--threshold-prob-true", type=float, default=0.2)
    parser.add_argument("--threshold-prob-pred", type=float, default=0.8)
    parser.add_argument("--score-method", default="self_confidence")
    parser.add_argument("--filter-by", default="both")
    parser.add_argument(
        "--fraction-noise",
        type=float,
        default=None,
        help="Override fraction_noise for confident_learning. If omitted, it matches injected noise_fraction.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-examples", type=int, default=500)
    parser.add_argument("--json-out", default="", help="Optional: write results JSON to this path.")
    args = parser.parse_args(argv)

    datasets = _parse_csv_list(args.datasets)
    noise_modes = _parse_csv_list(args.noise_modes)
    noise_fractions = _parse_csv_floats(args.noise_fractions)
    executors = _parse_csv_list(args.executors)

    results: list[RunResult] = []
    for ds in datasets:
        for nm in noise_modes:
            for nf in noise_fractions:
                for ex in executors:
                    rr = _run_once(
                        dataset_name=ds,
                        noise_mode=nm,
                        noise_fraction=float(nf),
                        executor_algorithm=ex,
                        n_splits=int(args.n_splits),
                        threshold_prob_true=float(args.threshold_prob_true),
                        threshold_prob_pred=float(args.threshold_prob_pred),
                        score_method=str(args.score_method),
                        filter_by=str(args.filter_by),
                        fraction_noise=args.fraction_noise,
                        seed=int(args.seed),
                        max_examples=int(args.max_examples),
                    )
                    results.append(rr)

    _print_results(results)

    if args.json_out:
        payload = {"results": [asdict(r) for r in results]}
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Wrote JSON: {args.json_out}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
