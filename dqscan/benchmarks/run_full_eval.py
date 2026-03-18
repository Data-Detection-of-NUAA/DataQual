"""
图片分类错标检测 - 完整双算法评估脚本。

同时评估 SimiFeat KNN (CLIP) 和 pHash Outlier 两种算法，
在不同噪声比例下的 precision / recall / F1 表现。
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.datasets import load_digits

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def export_digits(output_dir: str) -> tuple[str, str]:
    """导出 sklearn digits → 64x64 RGB PNG + CSV。"""
    digits = load_digits()
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    rows = []
    for i in range(len(digits.images)):
        label = str(digits.target[i])
        os.makedirs(os.path.join(image_dir, label), exist_ok=True)
        arr = (digits.images[i] / 16.0 * 255).astype(np.uint8)
        img = Image.fromarray(arr, "L").resize((64, 64), Image.NEAREST).convert("RGB")
        rel = f"{label}/{i:05d}.png"
        img.save(os.path.join(image_dir, rel))
        rows.append({"image_path": rel, "label": label})
    csv_path = os.path.join(output_dir, "labels.csv")
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    logger.info("导出 %d 张图片", len(rows))
    return image_dir, csv_path


def inject_noise(csv_path: str, fraction: float, seed: int = 42) -> tuple[str, set[int]]:
    df = pd.read_csv(csv_path)
    rng = np.random.RandomState(seed)
    n = len(df)
    n_flip = int(n * fraction)
    flip_idx = set(rng.choice(n, n_flip, replace=False).tolist())
    labels = df["label"].tolist()
    uniq = sorted(set(labels))
    for i in flip_idx:
        labels[i] = rng.choice([l for l in uniq if l != labels[i]])
    df["label"] = labels
    out = csv_path.replace(".csv", f"_noisy_{fraction}.csv")
    df.to_csv(out, index=False)
    return out, flip_idx


def calc_metrics(detected: set[int], truth: set[int], total: int) -> dict:
    tp = len(detected & truth)
    p = tp / len(detected) if detected else 0
    r = tp / len(truth) if truth else 0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
    return {
        "detected": len(detected), "true_noisy": len(truth),
        "tp": tp, "fp": len(detected) - tp, "fn": len(truth) - tp,
        "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4),
    }


def run_eval(image_dir, csv_path, algorithm, fraction, **scanner_kwargs) -> dict[str, Any]:
    from dqscan.scanner.image_scanner import ImageLabelMismatchScanner

    noisy_csv, truth = inject_noise(csv_path, fraction)
    noisy_df = pd.read_csv(noisy_csv)

    scanner = ImageLabelMismatchScanner(
        algorithm=algorithm,
        k=10, threshold=0.5,
        max_samples=5000, max_examples=500,
        **scanner_kwargs,
    )
    t0 = time.time()
    result = scanner.scan(
        image_dir=image_dir, label_df=noisy_df,
        image_column="image_path", label_column="label",
        output_dir=tempfile.mkdtemp(), emit=lambda e: None,
    )
    elapsed = round(time.time() - t0, 2)

    paths = {iss.get("data_id", "") for iss in result.get("detailed_issues", [])}
    idx_map = {row["image_path"]: i for i, row in noisy_df.iterrows()}
    det_idx = {idx_map[p] for p in paths if p in idx_map}

    m = calc_metrics(det_idx, truth, len(noisy_df))
    m.update({
        "algorithm": algorithm,
        "algorithm_display": result.get("algorithm", algorithm),
        "noise_fraction": fraction,
        "elapsed_seconds": elapsed,
        "total_images": len(noisy_df),
        "confusion_pairs_top_5": result.get("confusion_pairs_top", [])[:5],
        "per_class_issue_rate": result.get("per_class_issue_rate", {}),
    })
    logger.info(
        "%s noise=%.2f  P=%.4f R=%.4f F1=%.4f  det=%d tp=%d  %.1fs",
        algorithm, fraction, m["precision"], m["recall"], m["f1"],
        m["detected"], m["tp"], elapsed,
    )
    return m


def main():
    tmpdir = tempfile.mkdtemp(prefix="dqscan_full_eval_")
    logger.info("工作目录: %s", tmpdir)

    image_dir, csv_path = export_digits(tmpdir)

    fractions = [0.05, 0.10, 0.15, 0.20]
    algorithms = ["simifeat_knn", "phash_outlier"]
    all_results = []

    for algo in algorithms:
        for nf in fractions:
            logger.info("=" * 60)
            try:
                kwargs = {"device": "cpu"} if algo == "simifeat_knn" else {"hash_size": 16}
                m = run_eval(image_dir, csv_path, algo, nf, **kwargs)
                all_results.append(m)
            except Exception as exc:
                logger.error("FAIL %s nf=%.2f: %s", algo, nf, exc, exc_info=True)
                all_results.append({"algorithm": algo, "noise_fraction": nf, "error": str(exc)})

    out_path = os.path.join(
        str(Path(__file__).resolve().parents[2]),
        "dqscan", "benchmarks", "eval_results_full.json",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 汇总表
    print("\n" + "=" * 100)
    print("图片分类错标检测 — 双算法评估报告")
    print("数据集: sklearn digits (1797 张 64x64 手写数字, 10 类)")
    print("=" * 100)
    print(f"{'算法':<20} {'噪声':>6} {'检测':>6} {'真阳':>5} {'假阳':>5} {'假阴':>5} {'P':>7} {'R':>7} {'F1':>7} {'耗时':>6}")
    print("-" * 100)
    for r in all_results:
        if "error" in r:
            print(f"  {r['algorithm']:<18} {r['noise_fraction']:>5.2f}   ERROR: {r['error'][:60]}")
        else:
            print(
                f"  {r['algorithm_display'][:18]:<18}"
                f" {r['noise_fraction']:>5.2f}"
                f" {r['detected']:>5}"
                f" {r['tp']:>5}"
                f" {r['fp']:>5}"
                f" {r['fn']:>5}"
                f" {r['precision']:>6.4f}"
                f" {r['recall']:>6.4f}"
                f" {r['f1']:>6.4f}"
                f" {r['elapsed_seconds']:>5.1f}s"
            )
    print("=" * 100)
    print(f"\n详细 JSON: {out_path}")


if __name__ == "__main__":
    main()
