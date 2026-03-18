"""
图片分类错标检测 - 真实数据评估脚本。

使用方式：
1. 从 sklearn.datasets 导出手写数字图片（放大到 64x64 提升 pHash 效果）
2. 注入合成错标（多种噪声比例）
3. 运行 ImageLabelMismatchScanner（pHash Outlier）
4. 计算 precision@k / recall@k / F1
5. 输出 JSON 报告

依赖：Pillow, imagehash, pandas, numpy, sklearn
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

# 确保 dqscan 包可导入
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def export_digits_as_images(output_dir: str, max_samples: int = 1797) -> tuple[str, str]:
    """
    将 sklearn digits 数据集导出为 64x64 灰度 PNG 图片 + CSV 标签文件。
    """
    digits = load_digits()
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    rows = []
    n = min(max_samples, len(digits.images))
    for i in range(n):
        img_array = digits.images[i]  # (8, 8) float64 in [0, 16]
        label = str(digits.target[i])
        class_dir = os.path.join(image_dir, label)
        os.makedirs(class_dir, exist_ok=True)

        # 归一化到 [0, 255]，放大到 64x64
        img_uint8 = (img_array / 16.0 * 255).astype(np.uint8)
        img = Image.fromarray(img_uint8, mode="L").resize((64, 64), Image.NEAREST)
        # 转为 RGB（pHash 需要）
        img_rgb = img.convert("RGB")

        rel_path = f"{label}/{i:05d}.png"
        img_rgb.save(os.path.join(image_dir, rel_path))
        rows.append({"image_path": rel_path, "label": label})

    csv_path = os.path.join(output_dir, "labels.csv")
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    logger.info("Digits 数据集导出完成: %d 张图片, 10 个类别 (0-9)", len(rows))
    return image_dir, csv_path


def inject_noise(
    csv_path: str,
    noise_fraction: float,
    seed: int = 42,
) -> tuple[str, set[int]]:
    """向标签文件注入合成错标。"""
    df = pd.read_csv(csv_path)
    rng = np.random.RandomState(seed)

    n = len(df)
    n_flip = int(n * noise_fraction)
    flip_indices = set(rng.choice(n, n_flip, replace=False).tolist())

    labels = df["label"].tolist()
    unique_labels = sorted(set(labels))

    for idx in flip_indices:
        original = labels[idx]
        candidates = [l for l in unique_labels if l != original]
        labels[idx] = rng.choice(candidates)

    df["label"] = labels
    noisy_csv_path = csv_path.replace(".csv", f"_noisy_{noise_fraction}.csv")
    df.to_csv(noisy_csv_path, index=False)

    logger.info("注入噪声: fraction=%.2f, 翻转 %d/%d 条", noise_fraction, len(flip_indices), n)
    return noisy_csv_path, flip_indices


def evaluate(
    detected_indices: set[int],
    true_noisy_indices: set[int],
    total: int,
    k: int | None = None,
) -> dict[str, float]:
    """计算 precision@k / recall@k / F1。"""
    if k is None:
        k = len(true_noisy_indices)

    tp = len(detected_indices & true_noisy_indices)
    precision = tp / len(detected_indices) if detected_indices else 0.0
    recall = tp / len(true_noisy_indices) if true_noisy_indices else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "k": k,
        "detected": len(detected_indices),
        "true_noisy": len(true_noisy_indices),
        "tp": tp,
        "fp": len(detected_indices) - tp,
        "fn": len(true_noisy_indices) - tp,
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "f1": round(f1, 4),
    }


def run_single_eval(
    image_dir: str,
    csv_path: str,
    noise_fraction: float,
    max_examples: int = 500,
    hash_size: int = 16,
    threshold: float = 0.5,
    k: int = 10,
) -> dict[str, Any]:
    """运行一次评估（pHash Outlier 算法）。"""
    from dqscan.scanner.image_scanner import ImageLabelMismatchScanner

    # 注入噪声
    noisy_csv_path, true_noisy = inject_noise(csv_path, noise_fraction)
    noisy_df = pd.read_csv(noisy_csv_path)

    scanner = ImageLabelMismatchScanner(
        algorithm="phash_outlier",
        k=k,
        threshold=threshold,
        max_samples=5000,
        max_examples=max_examples,
        hash_size=hash_size,
    )

    start = time.time()
    scan_result = scanner.scan(
        image_dir=image_dir,
        label_df=noisy_df,
        image_column="image_path",
        label_column="label",
        output_dir=tempfile.mkdtemp(),
        emit=lambda e: None,
    )
    elapsed = round(time.time() - start, 2)

    # 提取检测到的索引
    detected_paths = set()
    for issue in scan_result.get("detailed_issues", []):
        detected_paths.add(issue.get("data_id", ""))

    path_to_idx = {row["image_path"]: i for i, row in noisy_df.iterrows()}
    detected_indices = {path_to_idx[p] for p in detected_paths if p in path_to_idx}

    metrics = evaluate(detected_indices, true_noisy, len(noisy_df))
    metrics["algorithm"] = "phash_outlier"
    metrics["algorithm_display"] = scan_result.get("algorithm", "pHash 类内离群")
    metrics["noise_fraction"] = noise_fraction
    metrics["elapsed_seconds"] = elapsed
    metrics["total_images"] = len(noisy_df)
    metrics["hash_size"] = hash_size

    # 保留扫描结果中的附加信息
    metrics["confusion_pairs_top_5"] = scan_result.get("confusion_pairs_top", [])[:5]
    metrics["per_class_issue_rate"] = scan_result.get("per_class_issue_rate", {})
    metrics["total_detected_issues"] = scan_result.get("total_issues", 0)
    metrics["image_label_mismatch_rate"] = scan_result.get("image_label_mismatch_rate", 0)

    # 抽样 5 个检测到的 issue 做展示
    sample_issues = []
    for issue in scan_result.get("detailed_issues", [])[:5]:
        sample_issues.append({
            "image_path": issue.get("data_id", ""),
            "given_label": issue.get("details", {}).get("given_label", ""),
            "suggested_label": issue.get("details", {}).get("suggested_label", ""),
            "confidence_score": issue.get("details", {}).get("confidence_score", 0),
            "severity": issue.get("severity", ""),
        })
    metrics["sample_issues"] = sample_issues

    logger.info(
        "noise=%.2f | P@k=%.4f R@k=%.4f F1=%.4f | detected=%d true=%d tp=%d | %.1fs",
        noise_fraction,
        metrics["precision_at_k"],
        metrics["recall_at_k"],
        metrics["f1"],
        metrics["detected"],
        metrics["true_noisy"],
        metrics["tp"],
        elapsed,
    )

    return metrics


def main():
    output_dir = tempfile.mkdtemp(prefix="dqscan_eval_")
    logger.info("工作目录: %s", output_dir)

    # 1. 准备数据集
    logger.info("=" * 60)
    logger.info("Phase 1: 导出 sklearn digits 数据集")
    image_dir, csv_path = export_digits_as_images(output_dir, max_samples=1797)

    # 2. 运行评估
    noise_fractions = [0.02, 0.05, 0.10, 0.15, 0.20]
    all_results = []

    for nf in noise_fractions:
        logger.info("=" * 60)
        logger.info("Phase 2: 评估 noise_fraction=%.2f", nf)
        try:
            metrics = run_single_eval(
                image_dir=image_dir,
                csv_path=csv_path,
                noise_fraction=nf,
                max_examples=500,
                hash_size=16,
            )
            all_results.append(metrics)
        except Exception as exc:
            logger.error("评估失败: %s", exc, exc_info=True)
            all_results.append({
                "algorithm": "phash_outlier",
                "noise_fraction": nf,
                "error": str(exc),
            })

    # 3. 输出结果
    json_out = os.path.join(
        str(Path(__file__).resolve().parents[2]),
        "dqscan", "benchmarks", "eval_results_real.json",
    )
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    logger.info("结果已写入: %s", json_out)

    # 4. 打印汇总
    print("\n" + "=" * 80)
    print("图片分类错标检测评估报告 — pHash Outlier 算法")
    print("数据集: sklearn digits (1797 张 64x64 灰度手写数字, 10 类)")
    print("=" * 80)
    print(f"{'噪声比例':>10} {'检测数':>8} {'真阳':>6} {'假阳':>6} {'假阴':>6} {'P@k':>8} {'R@k':>8} {'F1':>8} {'耗时(s)':>8}")
    print("-" * 80)
    for r in all_results:
        if "error" in r:
            print(f"  {r['noise_fraction']:.2f}  ERROR: {r['error']}")
        else:
            print(
                f"  {r['noise_fraction']:>8.2f} "
                f"  {r['detected']:>6} "
                f"  {r['tp']:>4} "
                f"  {r['fp']:>4} "
                f"  {r['fn']:>4} "
                f"  {r['precision_at_k']:>6.4f} "
                f"  {r['recall_at_k']:>6.4f} "
                f"  {r['f1']:>6.4f} "
                f"  {r['elapsed_seconds']:>6.1f}"
            )
    print("=" * 80)

    # 5. 打印混淆对和分类错标率（取最后一个噪声级别的）
    last = all_results[-1] if all_results else {}
    if "confusion_pairs_top_5" in last and last["confusion_pairs_top_5"]:
        print("\n高频混淆对 (noise=0.20):")
        for pair in last["confusion_pairs_top_5"]:
            print(f"  {pair['given_label']} → {pair['suggested_label']}  (count={pair['count']})")

    if "per_class_issue_rate" in last and last["per_class_issue_rate"]:
        print("\n各类别错标率 (noise=0.20):")
        for cls, rate in sorted(last["per_class_issue_rate"].items(), key=lambda x: -x[1]):
            print(f"  类别 {cls}: {rate*100:.2f}%")

    if "sample_issues" in last and last["sample_issues"]:
        print("\n检测样本 (noise=0.20, top 5):")
        for s in last["sample_issues"]:
            print(
                f"  {s['image_path']}  "
                f"原标签={s['given_label']} → 建议={s['suggested_label']}  "
                f"confidence={s['confidence_score']:.4f}  severity={s['severity']}"
            )

    print(f"\n详细结果 JSON: {json_out}")


if __name__ == "__main__":
    main()
