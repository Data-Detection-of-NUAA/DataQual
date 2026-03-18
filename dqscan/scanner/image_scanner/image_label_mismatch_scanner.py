"""
图片分类错标检测扫描器（Image Label Mismatch Scanner）。

支持两种算法：
1. simifeat_knn（主线）：CLIP ViT-B/32 embedding + KNN 邻域投票
2. phash_outlier（兜底）：感知哈希 + 类内平均汉明距离离群

依赖降级策略：
- simifeat_knn 需要 torch + transformers + Pillow
- phash_outlier 需要 Pillow + imagehash
- 若 simifeat_knn 依赖缺失，自动降级到 phash_outlier
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np

from dqscan.scanner.common.base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class ImageLabelMismatchScanner(BaseScanner):
    """图片分类错标检测。"""

    def __init__(
        self,
        *,
        algorithm: str = "simifeat_knn",
        k: int = 10,
        threshold: float = 0.5,
        max_samples: int = 5000,
        max_examples: int = 500,
        batch_size: int = 32,
        device: str = "auto",
        model_name: str = "openai/clip-vit-base-patch32",
        hash_size: int = 16,
    ):
        super().__init__(name="image_label_mismatch")
        self.algorithm = algorithm
        self.k = k
        self.threshold = threshold
        self.max_samples = max_samples
        self.max_examples = max_examples
        self.batch_size = batch_size
        self.device = device
        self.model_name = model_name
        self.hash_size = hash_size

    def scan(
        self,
        image_dir: str = "",
        label_df: Any = None,
        image_column: str = "image_path",
        label_column: str = "label",
        output_dir: str = "",
        emit: Any = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        执行图片错标检测。

        Parameters
        ----------
        image_dir : str
            图片根目录
        label_df : pd.DataFrame
            标签 DataFrame，必须包含 image_column 和 label_column
        image_column : str
            图片路径列名
        label_column : str
            标签列名
        output_dir : str
            输出目录（缩略图存放位置）
        emit : callable, optional
            事件回调
        """
        import pandas as pd

        if label_df is None or label_df.empty:
            return self._error_result("标签数据为空")

        # 采样
        if len(label_df) > self.max_samples:
            label_df = label_df.sample(n=self.max_samples, random_state=42)
            if emit:
                emit({
                    "type": "log",
                    "message": f"数据集过大，已采样 {self.max_samples} 条",
                })

        # 验证图片文件存在性
        valid_mask = label_df[image_column].apply(
            lambda p: os.path.isfile(os.path.join(image_dir, p))
        )
        n_missing = (~valid_mask).sum()
        if n_missing > 0:
            if emit:
                emit({
                    "type": "log",
                    "message": f"警告: {n_missing} 张图片文件不存在，已跳过",
                })
            label_df = label_df[valid_mask].reset_index(drop=True)

        if label_df.empty:
            return self._error_result("没有有效的图片文件")

        # 选择算法
        algorithm_used = self.algorithm
        if algorithm_used == "simifeat_knn":
            try:
                result = self._run_simifeat_knn(
                    image_dir, label_df, image_column, label_column, output_dir, emit
                )
            except ImportError as exc:
                logger.warning("simifeat_knn 依赖缺失 (%s)，降级到 phash_outlier", exc)
                if emit:
                    emit({
                        "type": "log",
                        "message": f"CLIP 依赖缺失 ({exc})，降级到 pHash 兜底算法",
                    })
                algorithm_used = "phash_outlier"
                result = self._run_phash_outlier(
                    image_dir, label_df, image_column, label_column, output_dir, emit
                )
        elif algorithm_used == "phash_outlier":
            result = self._run_phash_outlier(
                image_dir, label_df, image_column, label_column, output_dir, emit
            )
        else:
            return self._error_result(f"未知算法: {algorithm_used}")

        result["algorithm"] = algorithm_used
        return result

    # ------------------------------------------------------------------ #
    #  SimiFeat KNN (CLIP ViT-B/32 + KNN 投票)
    # ------------------------------------------------------------------ #

    def _run_simifeat_knn(
        self,
        image_dir: str,
        label_df: Any,
        image_column: str,
        label_column: str,
        output_dir: str,
        emit: Any,
    ) -> dict[str, Any]:
        """SimiFeat KNN: CLIP embedding + KNN 邻域投票检测错标。"""
        import torch
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor

        if emit:
            emit({"type": "log", "message": "加载 CLIP 模型..."})

        # --- 设备选择 ---
        if self.device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = self.device

        # --- 加载模型 ---
        try:
            processor = CLIPProcessor.from_pretrained(self.model_name)
            model = CLIPModel.from_pretrained(self.model_name).to(device)
            model.eval()
        except Exception as exc:
            raise ImportError(f"CLIP 模型加载失败: {exc}") from exc

        if emit:
            emit({"type": "log", "message": f"CLIP 模型已加载 (device={device})"})

        # --- 提取 embedding ---
        image_paths = label_df[image_column].tolist()
        labels = label_df[label_column].tolist()
        embeddings = []
        valid_indices = []

        for batch_start in range(0, len(image_paths), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(image_paths))
            batch_paths = image_paths[batch_start:batch_end]
            batch_images = []
            batch_valid = []

            for i, rel_path in enumerate(batch_paths):
                abs_path = os.path.join(image_dir, rel_path)
                try:
                    img = Image.open(abs_path).convert("RGB")
                    batch_images.append(img)
                    batch_valid.append(batch_start + i)
                except Exception:
                    logger.debug("图片加载失败: %s", abs_path)

            if not batch_images:
                continue

            try:
                inputs = processor(images=batch_images, return_tensors="pt", padding=True)
                inputs = {k: v.to(device) for k, v in inputs.items()}

                with torch.no_grad():
                    raw_out = model.get_image_features(**inputs)
                    # transformers >= 5.x returns BaseModelOutputWithPooling
                    if hasattr(raw_out, "pooler_output"):
                        image_features = raw_out.pooler_output
                    elif isinstance(raw_out, torch.Tensor):
                        image_features = raw_out
                    else:
                        image_features = raw_out
                    image_features = image_features / image_features.norm(
                        dim=-1, keepdim=True
                    )

                embeddings.append(image_features.cpu().numpy())
                valid_indices.extend(batch_valid)
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower() and device == "cuda":
                    logger.warning("CUDA OOM，fallback 到 CPU 重试")
                    if emit:
                        emit({"type": "log", "message": "GPU 内存不足，切换到 CPU"})
                    torch.cuda.empty_cache()
                    device = "cpu"
                    model = model.to(device)
                    inputs = processor(
                        images=batch_images, return_tensors="pt", padding=True
                    )
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    with torch.no_grad():
                        raw_out = model.get_image_features(**inputs)
                        if hasattr(raw_out, "pooler_output"):
                            image_features = raw_out.pooler_output
                        elif isinstance(raw_out, torch.Tensor):
                            image_features = raw_out
                        else:
                            image_features = raw_out
                        image_features = image_features / image_features.norm(
                            dim=-1, keepdim=True
                        )
                    embeddings.append(image_features.cpu().numpy())
                    valid_indices.extend(batch_valid)
                else:
                    raise

            if emit:
                progress = int(10 + 60 * min(batch_end, len(image_paths)) / len(image_paths))
                emit({"type": "progress", "value": progress})

        # 释放模型
        del model
        del processor
        if device == "cuda":
            torch.cuda.empty_cache()

        if not embeddings:
            return self._error_result("没有成功提取到图片 embedding")

        all_embeddings = np.concatenate(embeddings, axis=0)  # (N, 512)
        valid_labels = [labels[i] for i in valid_indices]
        valid_paths = [image_paths[i] for i in valid_indices]

        if emit:
            emit({
                "type": "log",
                "message": f"Embedding 提取完成: {len(all_embeddings)} 张图片, 维度={all_embeddings.shape[1]}",
            })

        # --- KNN 邻域投票 ---
        return self._knn_vote(
            all_embeddings, valid_labels, valid_paths, image_dir, output_dir, emit
        )

    def _knn_vote(
        self,
        embeddings: np.ndarray,
        labels: list,
        image_paths: list[str],
        image_dir: str,
        output_dir: str,
        emit: Any,
    ) -> dict[str, Any]:
        """基于 cosine similarity 的 KNN 邻域投票。"""
        from collections import Counter

        n = len(labels)
        k = min(self.k, n - 1)
        if k < 1:
            return self._error_result("样本数过少，无法执行 KNN")

        if emit:
            emit({"type": "log", "message": f"执行 KNN 投票 (k={k})..."})

        # cosine similarity matrix
        sim_matrix = embeddings @ embeddings.T  # (N, N)
        np.fill_diagonal(sim_matrix, -1.0)  # 排除自身

        # 找 top-k 邻居
        top_k_indices = np.argsort(-sim_matrix, axis=1)[:, :k]

        issues = []
        per_class_issues: dict[str, int] = {}
        per_class_total: dict[str, int] = {}
        confusion_pairs: dict[tuple[str, str], int] = {}

        for i in range(n):
            given_label = str(labels[i])
            per_class_total[given_label] = per_class_total.get(given_label, 0) + 1

            neighbor_labels = [str(labels[j]) for j in top_k_indices[i]]
            disagreement = sum(1 for nl in neighbor_labels if nl != given_label) / k
            label_counts = Counter(neighbor_labels)
            most_common_label = label_counts.most_common(1)[0][0]

            if disagreement > self.threshold and most_common_label != given_label:
                confidence = disagreement
                severity = (
                    "severe" if confidence > 0.8
                    else "moderate" if confidence > 0.6
                    else "light"
                )

                issues.append({
                    "data_id": image_paths[i],
                    "issue_type": "疑似错标（图片）",
                    "severity": severity,
                    "details": {
                        "given_label": given_label,
                        "suggested_label": most_common_label,
                        "confidence_score": round(confidence, 4),
                        "neighbor_agreement": round(1 - disagreement, 4),
                        "image_path": image_paths[i],
                    },
                })
                per_class_issues[given_label] = per_class_issues.get(given_label, 0) + 1
                pair = (given_label, most_common_label)
                confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

        # 按 confidence 排序，取 top max_examples
        issues.sort(key=lambda x: x["details"]["confidence_score"], reverse=True)
        issues = issues[: self.max_examples]

        # 生成缩略图
        self._generate_thumbnails(issues, image_dir, output_dir)

        # 统计
        total_issues = len(issues)
        issue_rate = round(total_issues / n, 4) if n > 0 else 0.0

        per_class_issue_rate = {}
        for cls, cnt in per_class_issues.items():
            total = per_class_total.get(cls, 1)
            per_class_issue_rate[cls] = round(cnt / total, 4)

        confusion_top = sorted(
            [
                {"given_label": g, "suggested_label": s, "count": c}
                for (g, s), c in confusion_pairs.items()
            ],
            key=lambda x: x["count"],
            reverse=True,
        )[:20]

        return {
            "has_issues": total_issues > 0,
            "total_issues": total_issues,
            "issue_percentage": issue_rate,
            "image_label_mismatch_count": total_issues,
            "image_label_mismatch_rate": issue_rate,
            "algorithm": "SimiFeat KNN (CLIP ViT-B/32)",
            "detailed_issues": issues,
            "per_class_issue_rate": per_class_issue_rate,
            "confusion_pairs_top": confusion_top,
        }

    # ------------------------------------------------------------------ #
    #  pHash 类内离群 (兜底算法)
    # ------------------------------------------------------------------ #

    def _run_phash_outlier(
        self,
        image_dir: str,
        label_df: Any,
        image_column: str,
        label_column: str,
        output_dir: str,
        emit: Any,
    ) -> dict[str, Any]:
        """pHash 类内离群检测：同类平均汉明距离过大 → 疑似错标。"""
        try:
            import imagehash
            from PIL import Image
        except ImportError as exc:
            return self._error_result(f"pHash 依赖缺失: {exc}（需要 Pillow + imagehash）")

        if emit:
            emit({"type": "log", "message": "计算 pHash..."})

        image_paths = label_df[image_column].tolist()
        labels = label_df[label_column].tolist()

        # 计算所有图片的 pHash
        hashes = []
        valid_indices = []
        for i, rel_path in enumerate(image_paths):
            abs_path = os.path.join(image_dir, rel_path)
            try:
                img = Image.open(abs_path)
                h = imagehash.phash(img, hash_size=self.hash_size)
                hashes.append(h)
                valid_indices.append(i)
            except Exception:
                logger.debug("图片 pHash 计算失败: %s", abs_path)

            if emit and i % 200 == 0:
                progress = int(10 + 50 * i / len(image_paths))
                emit({"type": "progress", "value": progress})

        if not hashes:
            return self._error_result("没有成功计算到 pHash")

        valid_labels = [str(labels[i]) for i in valid_indices]
        valid_paths = [image_paths[i] for i in valid_indices]
        n = len(hashes)

        # 按类分组
        class_indices: dict[str, list[int]] = {}
        for idx, lbl in enumerate(valid_labels):
            class_indices.setdefault(lbl, []).append(idx)

        if emit:
            emit({"type": "log", "message": "计算类内/类间汉明距离..."})

        issues = []
        per_class_issues: dict[str, int] = {}
        per_class_total: dict[str, int] = {lbl: len(ids) for lbl, ids in class_indices.items()}
        confusion_pairs: dict[tuple[str, str], int] = {}

        for idx in range(n):
            given_label = valid_labels[idx]
            same_class = class_indices[given_label]

            if len(same_class) < 2:
                continue

            # 类内平均汉明距离
            intra_dists = [
                hashes[idx] - hashes[j] for j in same_class if j != idx
            ]
            avg_intra = sum(intra_dists) / len(intra_dists) if intra_dists else 0

            # 类间最小平均汉明距离
            min_inter_dist = float("inf")
            closest_class = given_label
            for other_label, other_indices in class_indices.items():
                if other_label == given_label or not other_indices:
                    continue
                inter_dists = [hashes[idx] - hashes[j] for j in other_indices]
                avg_inter = sum(inter_dists) / len(inter_dists)
                if avg_inter < min_inter_dist:
                    min_inter_dist = avg_inter
                    closest_class = other_label

            # outlier_score = avg_intra - min_inter (> 0 表示"更像其他类")
            outlier_score = avg_intra - min_inter_dist if min_inter_dist < float("inf") else 0

            if outlier_score > 0:
                severity = (
                    "severe" if outlier_score > 20
                    else "moderate" if outlier_score > 10
                    else "light"
                )
                issues.append({
                    "data_id": valid_paths[idx],
                    "issue_type": "疑似错标（图片）",
                    "severity": severity,
                    "details": {
                        "given_label": given_label,
                        "suggested_label": closest_class,
                        "confidence_score": round(
                            min(outlier_score / 30.0, 1.0), 4
                        ),
                        "avg_intra_dist": round(avg_intra, 2),
                        "min_inter_dist": round(
                            min_inter_dist if min_inter_dist < float("inf") else 0, 2
                        ),
                        "outlier_score": round(outlier_score, 2),
                        "image_path": valid_paths[idx],
                    },
                })
                per_class_issues[given_label] = per_class_issues.get(given_label, 0) + 1
                pair = (given_label, closest_class)
                confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

            if emit and idx % 100 == 0:
                progress = int(60 + 30 * idx / n)
                emit({"type": "progress", "value": progress})

        # 排序
        issues.sort(key=lambda x: x["details"]["confidence_score"], reverse=True)
        issues = issues[: self.max_examples]

        # 生成缩略图
        self._generate_thumbnails(issues, image_dir, output_dir)

        total_issues = len(issues)
        issue_rate = round(total_issues / n, 4) if n > 0 else 0.0

        per_class_issue_rate = {}
        for cls, cnt in per_class_issues.items():
            total = per_class_total.get(cls, 1)
            per_class_issue_rate[cls] = round(cnt / total, 4)

        confusion_top = sorted(
            [
                {"given_label": g, "suggested_label": s, "count": c}
                for (g, s), c in confusion_pairs.items()
            ],
            key=lambda x: x["count"],
            reverse=True,
        )[:20]

        return {
            "has_issues": total_issues > 0,
            "total_issues": total_issues,
            "issue_percentage": issue_rate,
            "image_label_mismatch_count": total_issues,
            "image_label_mismatch_rate": issue_rate,
            "algorithm": "pHash 类内离群",
            "detailed_issues": issues,
            "per_class_issue_rate": per_class_issue_rate,
            "confusion_pairs_top": confusion_top,
        }

    # ------------------------------------------------------------------ #
    #  缩略图生成
    # ------------------------------------------------------------------ #

    def _generate_thumbnails(
        self,
        issues: list[dict[str, Any]],
        image_dir: str,
        output_dir: str,
        thumb_size: tuple[int, int] = (64, 64),
    ) -> None:
        """为 issues 中的图片生成缩略图，存储到 output_dir/thumbnails/。"""
        if not issues or not output_dir:
            return

        try:
            from PIL import Image
        except ImportError:
            return

        thumb_dir = os.path.join(output_dir, "thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)

        for issue in issues:
            details = issue.get("details", {})
            img_path = details.get("image_path", "")
            if not img_path:
                continue

            abs_path = os.path.join(image_dir, img_path)
            if not os.path.isfile(abs_path):
                continue

            try:
                img = Image.open(abs_path).convert("RGB")
                img.thumbnail(thumb_size)
                thumb_name = (
                    Path(img_path).stem + "_thumb.jpg"
                )
                thumb_path = os.path.join(thumb_dir, thumb_name)
                img.save(thumb_path, "JPEG", quality=75)
                details["thumbnail_path"] = f"thumbnails/{thumb_name}"
            except Exception:
                logger.debug("缩略图生成失败: %s", abs_path)
