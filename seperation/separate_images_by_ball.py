
r"""Separate images into Ball_detected / No_ball_detected using a YOLO model.


Usage:
	python separate_images_by_ball.py --input "D:\\Brainy Neurals\\basketball pipeline\\data\\extracted_frames\\video_aps_vs_agsv" --device 0
	For GPU with batching for maximum speed:
	python "d:\Brainy Neurals\basketball pipeline\seperation\separate_images_by_ball.py" --input "D:\Brainy Neurals\basketball pipeline\data\extracted_frames\video_aps_vs_agsv" --batch-size 32 --device 0


By default the script uses a model at project root `best_det.pt` and a confidence
threshold of 0.05. For each image in the input folder (non-recursive) the script
runs inference and moves the file into a subfolder of the input folder named
`Ball_detected` or `No_ball_detected`.

The script is defensive: it will create destination folders if missing and will
avoid overwriting files by appending a numeric suffix if needed.

Performance options:
- --batch-size N (default 16) batches multiple images per inference call.
- --workers N (default 0) enables multiprocessing with N worker processes.
	Each worker loads the model once and returns detection booleans; the parent
	process performs the actual file moves. Note: if using a single GPU, batching
	(workers=0) is usually faster and more memory-efficient than multiprocessing.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple
import multiprocessing as mp


def is_image_file(p: Path) -> bool:
	return p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff"}


def find_images(folder: Path) -> Iterable[Path]:
	for p in sorted(folder.iterdir()):
		if p.is_file() and is_image_file(p):
			yield p


def safe_move(src: Path, dst_dir: Path) -> Path:
	dst_dir.mkdir(parents=True, exist_ok=True)
	dst = dst_dir / src.name
	if not dst.exists():
		shutil.move(str(src), str(dst))
		return dst

	# avoid overwrite: append _1, _2, ...
	stem = src.stem
	suffix = src.suffix
	i = 1
	while True:
		candidate = dst_dir / f"{stem}_{i}{suffix}"
		if not candidate.exists():
			shutil.move(str(src), str(candidate))
			return candidate
		i += 1


def chunked(seq: List[Path], size: int) -> Iterable[List[Path]]:
	if size <= 0:
		size = len(seq) or 1
	for i in range(0, len(seq), size):
		yield seq[i:i + size]


def _ball_detected_from_result(model, res) -> bool:
	"""Return True if the result contains a basketball detection.

	If model.names is available, only count detections whose class name contains
	'ball', 'basket', or 'basketball'. Otherwise, any detection counts.
	"""
	detected = False
	boxes = getattr(res, "boxes", None)
	if boxes is not None and len(boxes) > 0:
		names = getattr(model, "names", None)
		try:
			cls_ids = [int(x) for x in boxes.cls.tolist()]
		except Exception:
			cls_ids = list(range(len(boxes)))

		if names:
			for cid in cls_ids:
				nm = str(names.get(cid, "")).lower()
				if "ball" in nm or "basket" in nm or "basketball" in nm:
					detected = True
					break
			else:
				detected = False
		else:
			detected = len(cls_ids) > 0
	return detected


# --- Multiprocessing helpers (Windows-safe: top-level definitions) ---
_MP_MODEL = None


def _mp_init(weights: str, device: str):
	global _MP_MODEL
	from ultralytics import YOLO  # local import per process
	_MP_MODEL = YOLO(weights)
	_MP_MODEL.to(device)


def _mp_detect_one(args: Tuple[str, float, str]) -> Tuple[str, bool, str | None]:
	"""Detect one image in a worker process.
	Returns (img_path_str, detected_bool, error_message_or_None)
	"""
	img_path_str, conf, device = args
	try:
		results = _MP_MODEL.predict(source=img_path_str, conf=conf, device=device, verbose=False)
		res = results[0]
		detected = _ball_detected_from_result(_MP_MODEL, res)
		return (img_path_str, detected, None)
	except Exception as e:
		return (img_path_str, False, str(e))


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Move images based on ball detection (Ultralytics YOLO).")
	parser.add_argument("--input", "-i", required=False,
						default=r"D:\\Brainy Neurals\\basketball pipeline\\data\\extracted_frames\\video_aps_vs_agsv",
						help="Input: folder containing images (non-recursive) OR a single image file path.")
	parser.add_argument("--weights", "-w", default=r"D:\Brainy Neurals\basketball pipeline\best_det.pt",
						help="Path to YOLO weights (default: best_det.pt in project root).")
	parser.add_argument("--conf", "-c", type=float, default=0.05,
						help="Confidence threshold for detections (default: 0.05).")
	parser.add_argument("--dry-run", action="store_true", help="Print what would be moved but don't move files.")
	parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference when processing folders.")
	parser.add_argument("--workers", type=int, default=0, help="Number of worker processes for multiprocessing. 0 disables multiprocessing.")
	parser.add_argument("--device", default=0, type=int, help="Device to run inference on. 0 for GPU, -1 or 'cpu' for CPU (default: 0).")
	args = parser.parse_args(argv)
	
	# Convert device to proper format for YOLO
	if isinstance(args.device, str) and args.device.lower() == 'cpu':
		device = 'cpu'
	else:
		device = int(args.device) if args.device != 'cpu' else 'cpu'

	input_path = Path(args.input)
	if not input_path.exists():
		print(f"Input path does not exist: {input_path}")
		return 2
	
	# Determine if input is a single file or a folder
	if input_path.is_file():
		if not is_image_file(input_path):
			print(f"Input file is not a valid image: {input_path}")
			return 2
		images_to_process = [input_path]
	elif input_path.is_dir():
		images_to_process = list(find_images(input_path))
	else:
		print(f"Input path is neither a file nor a directory: {input_path}")
		return 2

	try:
		# Import here so script can still be parsed without ultralytics installed
		from ultralytics import YOLO
	except Exception as exc:  # pragma: no cover - environment dependent
		print("Failed to import ultralytics. Install with: pip install ultralytics")
		print("Import error:", exc)
		return 3

	model = YOLO(args.weights)
	model.to(device)  # Explicitly set device for GPU usage

	# Automatically determine output directories based on input path
	# If input is a file, use its parent directory; if folder, use the folder itself
	base_dir = input_path.parent if input_path.is_file() else input_path
	ball_dir = base_dir / "Ball_detected"
	no_ball_dir = base_dir / "No_ball_detected"
	
	# Create output directories if they don't exist
	ball_dir.mkdir(parents=True, exist_ok=True)
	no_ball_dir.mkdir(parents=True, exist_ok=True)

	total = 0
	moved_ball = 0
	moved_no_ball = 0

	if len(images_to_process) == 1 and args.workers == 0:
		# single image fast path
		img_path = images_to_process[0]
		total = 1
		try:
			results = model.predict(source=str(img_path), conf=args.conf, device=device, verbose=False)
			res = results[0]
			detected = _ball_detected_from_result(model, res)
		except Exception as e:
			print(f"Error running model on {img_path}: {e}")
			detected = False

		target = ball_dir if detected else no_ball_dir
		if args.dry_run:
			print(f"DRY-RUN: would move {img_path} -> {target} (detected={detected})")
		else:
			safe_move(img_path, target)
			if detected:
				moved_ball += 1
			else:
				moved_no_ball += 1
	else:
		if args.workers and args.workers > 0:
			# Multiprocessing: workers return booleans; parent moves files
			with mp.get_context("spawn").Pool(processes=args.workers, initializer=_mp_init, initargs=(str(args.weights), device)) as pool:
				for img_path_str, detected, err in pool.imap_unordered(_mp_detect_one, [(str(p), args.conf, device) for p in images_to_process]):
					total += 1
					img_path = Path(img_path_str)
					if err is not None:
						print(f"Error running model on {img_path}: {err}")
						detected = False
					target = ball_dir if detected else no_ball_dir
					if args.dry_run:
						print(f"DRY-RUN: would move {img_path} -> {target} (detected={detected})")
					else:
						safe_move(img_path, target)
						if detected:
							moved_ball += 1
						else:
							moved_no_ball += 1
		else:
			# Batched single-process inference
			bs = max(1, int(args.batch_size))
			for batch in chunked(images_to_process, bs):
				paths = [str(p) for p in batch]
				try:
					results = model.predict(source=paths, conf=args.conf, device=device, verbose=False)
				except Exception as e:
					# On batch failure, fall back to per-image to continue progress
					for p in batch:
						total += 1
						print(f"Error running model on {p}: {e}")
						target = no_ball_dir
						if args.dry_run:
							print(f"DRY-RUN: would move {p} -> {target}")
						else:
							safe_move(p, target)
							moved_no_ball += 1
					continue

				for p, res in zip(batch, results):
					total += 1
					detected = _ball_detected_from_result(model, res)
					target = ball_dir if detected else no_ball_dir
					if args.dry_run:
						print(f"DRY-RUN: would move {p} -> {target} (detected={detected})")
					else:
						safe_move(p, target)
						if detected:
							moved_ball += 1
						else:
							moved_no_ball += 1

	print(f"Processed {total} images: moved to Ball_detected={moved_ball}, No_ball_detected={moved_no_ball}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
