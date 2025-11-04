"""
Dataset Splitter (Phase 4)
Splits augmented dataset into train/val/test using Option B (by-video split).

Outputs a YOLO-ready folder structure:
data/yolo_dataset/
  train/images, train/labels
  val/images, val/labels
  test/images, test/labels

Also generates data.yaml and a split_summary.json.
"""

from __future__ import annotations

import os
import shutil
import random
import json
from pathlib import Path
from typing import Dict, List, Tuple

import logging

logger = logging.getLogger(__name__)


class DatasetSplitter:
    def __init__(self, config: Dict):
        self.config = config
        self.split_cfg = config.get("split", {})

        # Defaults
        self.train_ratio = float(self.split_cfg.get("train_ratio", 0.8))
        self.val_ratio = float(self.split_cfg.get("val_ratio", 0.1))
        self.test_ratio = float(self.split_cfg.get("test_ratio", 0.1))
        self.seed = int(self.split_cfg.get("seed", 42))
        self.split_by = str(self.split_cfg.get("split_by", "video"))
        self.create_empty_labels = bool(self.split_cfg.get("create_empty_labels", True))

        # IO
        self.input_dir = Path(self.split_cfg.get("input_dir", "data/augmented"))
        self.output_dir = Path(self.split_cfg.get("output_dir", "data/yolo_dataset"))

        # Classes for data.yaml
        self.classes: List[str] = list(self.config.get("classes", []))

    def _gather_videos(self) -> List[Tuple[Path, int]]:
        """Return list of (video_folder_path, image_count)."""
        videos: List[Tuple[Path, int]] = []
        if not self.input_dir.exists():
            logger.error(f"Input directory not found: {self.input_dir}")
            return videos

        for sub in sorted(self.input_dir.iterdir()):
            if sub.is_dir():
                count = len([p for p in sub.glob("*.jpg")])
                if count > 0:
                    videos.append((sub, count))

        if not videos:
            logger.error(f"No video folders with images found in: {self.input_dir}")
        else:
            logger.info(f"Found {len(videos)} video folders under {self.input_dir}")
        return videos

    def _assign_videos_to_splits(self, videos: List[Tuple[Path, int]]):
        """Assign whole video folders to train/val/test to match ratios by image count."""
        random.Random(self.seed).shuffle(videos)

        total_images = sum(c for _, c in videos)
        target_train = self.train_ratio * total_images
        target_val = self.val_ratio * total_images

        train, val, test = [], [], []
        c_train = c_val = 0

        for vid, cnt in videos:
            if c_train + cnt <= target_train or not train:
                train.append((vid, cnt))
                c_train += cnt
            elif c_val + cnt <= target_val or not val:
                val.append((vid, cnt))
                c_val += cnt
            else:
                test.append((vid, cnt))

        logger.info("Video assignment summary:")
        logger.info(f"  Train videos: {len(train)}, images: {sum(c for _, c in train)}")
        logger.info(f"  Val videos:   {len(val)}, images: {sum(c for _, c in val)}")
        logger.info(f"  Test videos:  {len(test)}, images: {sum(c for _, c in test)}")

        return train, val, test

    @staticmethod
    def _ensure_dirs(base: Path):
        for split in ("train", "val", "test"):
            (base / split / "images").mkdir(parents=True, exist_ok=True)
            (base / split / "labels").mkdir(parents=True, exist_ok=True)

    def _copy_image_and_label(self, src_img: Path, dst_images_dir: Path, dst_labels_dir: Path):
        # Copy image
        dst_img = dst_images_dir / src_img.name
        shutil.copy2(src_img, dst_img)

        # Label handling
        src_lbl = src_img.with_suffix(".txt")
        dst_lbl = dst_labels_dir / src_lbl.name
        if src_lbl.exists():
            shutil.copy2(src_lbl, dst_lbl)
        elif self.create_empty_labels:
            dst_lbl.write_text("")
        else:
            # Skip creating label file; some trainers require empty files
            pass

    def _copy_video_folder(self, video_folder: Path, split_name: str):
        dst_images = self.output_dir / split_name / "images"
        dst_labels = self.output_dir / split_name / "labels"

        imgs = sorted(video_folder.glob("*.jpg"))
        for img in imgs:
            self._copy_image_and_label(img, dst_images, dst_labels)

    def _write_data_yaml(self):
        data_yaml = self.output_dir / "data.yaml"
        # Use paths relative to data.yaml location to avoid duplication by ultralytics
        train_rel = "train/images"
        val_rel = "val/images"
        test_rel = "test/images"
        nc = len(self.classes)
        names = self.classes

        data_yaml.write_text(
            f"train: {train_rel}\n"
            f"val: {val_rel}\n"
            f"test: {test_rel}\n"
            f"nc: {nc}\n"
            "names: [" + ", ".join([f"'{n}'" for n in names]) + "]\n"
        )
        logger.info(f"Wrote YOLO data.yaml -> {data_yaml}")

    def _write_summary(self, train, val, test):
        summary = {
            "seed": self.seed,
            "ratios": {"train": self.train_ratio, "val": self.val_ratio, "test": self.test_ratio},
            "split_by": self.split_by,
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "counts": {
                "train": sum(c for _, c in train),
                "val": sum(c for _, c in val),
                "test": sum(c for _, c in test),
            },
            "videos": {
                "train": [p.name for p, _ in train],
                "val": [p.name for p, _ in val],
                "test": [p.name for p, _ in test],
            },
        }
        (self.output_dir).mkdir(parents=True, exist_ok=True)
        (self.output_dir / "split_summary.json").write_text(json.dumps(summary, indent=2))
        logger.info(f"Wrote split summary -> {self.output_dir / 'split_summary.json'}")

    def split(self) -> Dict:
        if self.split_by != "video":
            logger.warning(f"split_by={self.split_by} not supported yet. Defaulting to 'video'.")

        videos = self._gather_videos()
        if not videos:
            return {"success": False, "reason": "no_videos"}

        train, val, test = self._assign_videos_to_splits(videos)

        # Prepare output
        self._ensure_dirs(self.output_dir)

        # Copy files
        for p, _ in train:
            self._copy_video_folder(p, "train")
        for p, _ in val:
            self._copy_video_folder(p, "val")
        for p, _ in test:
            self._copy_video_folder(p, "test")

        # Write artifacts
        self._write_data_yaml()
        self._write_summary(train, val, test)

        result = {
            "success": True,
            "train_images": sum(c for _, c in train),
            "val_images": sum(c for _, c in val),
            "test_images": sum(c for _, c in test),
            "output_dir": str(self.output_dir),
        }
        logger.info(f"Split complete: {result}")
        return result
