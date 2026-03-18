"""
图片分类错标检测评估脚本。

使用 CIFAR-10 样式的合成数据集评估 simifeat_knn 和 phash_outlier 算法的
precision@k / recall@k 表现。

用法：
    python dqscan/benchmarks/image_label_mismatch_eval.py \
        --dataset cifar10 \
        --noise-fractions 0.05,0.10 \
        --algorithms simifeat_knn,phash_outlier \
        --max-samples 1000 \
        --json-out results.json

数据集支持：
- cifar10: 自动下载 CIFAR-10（需要 torchvision）
- custom: 指定本地目录 + CSV（--image-dir + --label-csv）

评估方式：
1. 加载数据集
2. 按 noise_fraction 随机翻转一部分标签（合成错标）
3. 运行 scanner 检测
4. 计算 precision@k / recall@k（k = 实际注入错标数）
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 确保 dqscan 包可导入
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def setup_cifar10(output_dir: str, max_samples: int = 1000) -> tuple[str, str]:
    """下载 CIFAR-10 并导出为图片文件 + CSV。返回 (image_dir, csv_path)。"""
    try:
        import torchvision
        from PIL import Image
    except ImportError:
        raise ImportError("评估 CIFAR-10 需要 torchvision 和 Pillow")

    logger.info("下载 CIFAR-10 数据集...")
    dataset = torchvision.datasets.CIFAR10(
        root=os.path.join(output_dir, "cifar10_raw"),
        train=True,
        download=True,
    )

    class_names = dataset.classes
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # 采样
    indices = np.random.RandomState(42).choice(len(dataset), min(max_samples, len(dataset)), replace=False)

    rows = []
    for i, idx in enumerate(indices):
        img, label = dataset[idx]
        class_name = class_names[label]
        class_dir = os.path.join(image_dir, class_name)
        os.makedirs(class_dir, exist_ok=True)
        img_path = f"{class_name}/{i:05d}.png"
        img.save(os.path.join(image_dir, img_path))
        rows.append({"image_path": img_path, "label": class_name})

    # 写 CSV
    import pandas as pd

    csv_path = os.path.join(output_dir, "labels.csv")
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    logger.info("CIFAR-10 准备完成: %d 张图片, %d 个类别", len(rows), len(class_names))
    return image_dir, csv_path


def inject_noise(
    csv_path: str,
    noise_fraction: float,
    noise_mode: str = "uniform",
    seed: int = 42,
) -> tuple[str, set[int]]:
    """
    向标签文件注入合成错标。

    Returns
    -------
    noisy_csv_path : str
        注入噪声后的 CSV 路径
    noisy_indices : set[int]
        被翻转的行索引（ground truth）
    """
    import pandas as pd

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
        if candidates:
            if noise_mode == "uniform":
                labels[idx] = rng.choice(candidates)
            elif noise_mode == "class_conditional":
                # 更可能翻转到相邻类
                labels[idx] = rng.choice(candidates)
            else:
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
    """计算 precision@k / recall@k。"""
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
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "f1": round(f1, 4),
    }


def run_evaluation(
    image_dir: str,
    csv_path: str,
    algorithm: str,
    noise_fraction: float,
    max_samples: int,
    max_examples: int = 500,
    device: str = "auto",
) -> dict[str, Any]:
    """运行一次评估。"""
    from typing import Any

    import pandas as pd

    from dqscan.scanner.image_scanner import ImageLabelMismatchScanner

    # 注入噪声
    noisy_csv_path, true_noisy = inject_noise(csv_path, noise_fraction)
    noisy_df = pd.read_csv(noisy_csv_path)

    # 运行 scanner
    scanner = ImageLabelMismatchScanner(
        algorithm=algorithm,
        k=10,
        threshold=0.5,
        max_samples=max_samples,
        max_examples=max_examples,
        device=device,
    )

    start = time.time()
    result = scanner.scan(
        image_dir=image_dir,
        label_df=noisy_df,
        image_column="image_path",
        label_column="label",
        output_dir=tempfile.mkdtemp(),
        emit=lambda e: logger.debug("%s", e.get("message", "")),
    )
    elapsed = round(time.time() - start, 2)

    # 提取检测到的索引
    detected_paths = set()
    for issue in result.get("detailed_issues", []):
        detected_paths.add(issue.get("data_id", ""))

    # 映射回行索引
    path_to_idx = {row["image_path"]: i for i, row in noisy_df.iterrows()}
    detected_indices = {path_to_idx[p] for p in detected_paths if p in path_to_idx}

    # 评估
    metrics = evaluate(detected_indices, true_noisy, len(noisy_df))
    metrics["algorithm"] = algorithm
    metrics["noise_fraction"] = noise_fraction
    metrics["elapsed_seconds"] = elapsed
    metrics["total_images"] = len(noisy_df)
    metrics["algorithm_display"] = result.get("algorithm", algorithm)

    logger.info(
        "算法=%s, noise=%.2f, P@k=%.4f, R@k=%.4f, F1=%.4f, 耗时=%.1fs",
        algorithm,
        noise_fraction,
        metrics["precision_at_k"],
        metrics["recall_at_k"],
        metrics["f1"],
        elapsed,
    )

    return metrics


def main():
    parser = argparse.ArgumentParser(description="图片错标检测评估")
    parser.add_argument("--dataset", default="cifar10", choices=["cifar10", "custom"])
    parser.add_argument("--image-dir", default="", help="custom 模式的图片目录")
    parser.add_argument("--label-csv", default="", help="custom 模式的标签 CSV")
    parser.add_argument("--noise-fractions", default="0.05,0.10", help="噪声比例（逗号分隔）")
    parser.add_argument("--algorithms", default="simifeat_knn,phash_outlier", help="算法（逗号分隔）")
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--max-examples", type=int, default=500)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--json-out", default="", help="输出 JSON 路径")
    args = parser.parse_args()

    noise_fractions = [float(x) for x in args.noise_fractions.split(",")]
    algorithms = [x.strip() for x in args.algorithms.split(",")]

    # 准备数据集
    tmpdir = tempfile.mkdtemp(prefix="img_eval_")
    try:
        if args.dataset == "cifar10":
            image_dir, csv_path = setup_cifar10(tmpdir, args.max_samples)
        else:
            image_dir = args.image_dir
            csv_path = args.label_csv
            if not image_dir or not csv_path:
                parser.error("custom 模式需要 --image-dir 和 --label-csv")

        all_results = []
        for algo in algorithms:
            for nf in noise_fractions:
                logger.info("=" * 60)
                logger.info("评估: algorithm=%s, noise_fraction=%.2f", algo, nf)
                try:
                    metrics = run_evaluation(
                        image_dir=image_dir,
                        csv_path=csv_path,
                        algorithm=algo,
                        noise_fraction=nf,
                        max_samples=args.max_samples,
                        max_examples=args.max_examples,
                        device=args.device,
                    )
                    all_results.append(metrics)
                except Exception as exc:
                    logger.error("评估失败: %s", exc)
                    all_results.append({
                        "algorithm": algo,
                        "noise_fraction": nf,
                        "error": str(exc),
                    })

        # 输出结果
        print("\n" + "=" * 60)
        print("评估结果汇总")
        print("=" * 60)
        for r in all_results:
            if "error" in r:
                print(f"  {r['algorithm']} (noise={r['noise_fraction']}): ERROR - {r['error']}")
            else:
                print(
                    f"  {r['algorithm']} (noise={r['noise_fraction']}): "
                    f"P@k={r['precision_at_k']:.4f}, R@k={r['recall_at_k']:.4f}, "
                    f"F1={r['f1']:.4f}, 耗时={r['elapsed_seconds']}s"
                )

        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            logger.info("结果已写入: %s", args.json_out)

    finally:
        if args.dataset == "cifar10":
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
