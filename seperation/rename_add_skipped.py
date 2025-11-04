"""Add '_skipped_5' to image filenames before the frame number.

Renames files like:
  aps_vs_agsv_frame_000088.jpg
to:
  aps_vs_agsv_skipped_5_frame_000088.jpg

Usage:
  python rename_add_skipped.py --input "path/to/folder"
  python rename_add_skipped.py --input "path/to/folder" --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def rename_with_skipped(folder: Path, dry_run: bool = False) -> tuple[int, int]:
	"""Rename files in folder to add '_skipped_5' before frame number.
	
	Returns (renamed_count, skipped_count)
	"""
	renamed = 0
	skipped = 0
	
	# Pattern to match: video_name_frame_NNNNNN.ext or video_name_frame_NNNNNN_N.ext
	# We want to insert '_skipped_5' before '_frame_'
	# Handles both: aps_vs_agsv_frame_029161.jpg and aps_vs_agsv_frame_029161_1.jpg
	pattern = re.compile(r'^(.+?)(_frame_\d+)((?:_\d+)?(?:\.\w+))$')
	
	for file_path in sorted(folder.iterdir()):
		if not file_path.is_file():
			continue
		
		filename = file_path.name
		match = pattern.match(filename)
		
		if not match:
			print(f"SKIP (no match): {filename}")
			skipped += 1
			continue
		
		# Check if already has '_skipped_5'
		if '_skipped_5' in filename:
			print(f"SKIP (already renamed): {filename}")
			skipped += 1
			continue
		
		# Build new name: prefix + _skipped_5 + _frame_NNNNNN + (_N)? + extension
		prefix = match.group(1)
		frame_part = match.group(2)
		suffix_and_ext = match.group(3)  # includes _1.jpg or just .jpg
		new_name = f"{prefix}_skipped_5{frame_part}{suffix_and_ext}"
		new_path = folder / new_name
		
		if new_path.exists():
			print(f"ERROR: Target already exists: {new_name}")
			skipped += 1
			continue
		
		if dry_run:
			print(f"DRY-RUN: {filename} -> {new_name}")
		else:
			file_path.rename(new_path)
			print(f"RENAMED: {filename} -> {new_name}")
		
		renamed += 1
	
	return renamed, skipped


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Add '_skipped_5' to filenames before frame number.")
	parser.add_argument("--input", "-i", required=True,
						help="Folder containing images to rename.")
	parser.add_argument("--dry-run", action="store_true",
						help="Print what would be renamed without renaming.")
	args = parser.parse_args(argv)
	
	folder = Path(args.input)
	if not folder.exists() or not folder.is_dir():
		print(f"ERROR: Folder does not exist or is not a directory: {folder}")
		return 2
	
	print(f"Processing folder: {folder}")
	print(f"Mode: {'DRY-RUN' if args.dry_run else 'RENAMING'}")
	print("-" * 60)
	
	renamed, skipped = rename_with_skipped(folder, dry_run=args.dry_run)
	
	print("-" * 60)
	print(f"Summary: {renamed} renamed, {skipped} skipped")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
