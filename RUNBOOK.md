# Basketball Pipeline: Step-by-Step Runbook

This single guide walks you from adding videos to training and prediction. It supports two modes:
- Without labels yet (pipeline wiring, training auto-skips)
- With labels (real YOLO training)

All commands below are for Windows PowerShell (pwsh).

---

## 0) Install dependencies (one-time)

```powershell
# From repo root
pip install -r requirements.txt
# If you need GPU acceleration, ensure you have a CUDA-enabled PyTorch installed
# See INSTALLATION_GUIDE.md for details.
```

Optional: verify Ultralytics can import.

```powershell
python - << 'PY'
try:
    import ultralytics
    print('Ultralytics OK:', ultralytics.__version__)
except Exception as e:
    print('Ultralytics import failed:', e)
PY
```

---

## 1) Add your videos

- Put your game clips under `data/raw_videos/`.
- Supported: .mp4, .avi, .mov, .mkv, .flv, .wmv

Folder snapshot:
```
data/
  raw_videos/
    game1.mp4
    game2.mp4
```

---

## 2) Configure (optional)

Edit `config/config.yaml` as needed:
- frame extraction interval and limits
- quality filter thresholds
- augmentation settings
- split ratios (by video)
- training params (epochs, imgsz, batch, device)

You can keep defaults to start.

---

## 3) Phase 1: Extract frames

This runs extraction (config-driven) and writes outputs under `data/extracted_frames/`.

```powershell
python .\main.py
```

Useful checks:
```powershell
# Quick health/status
python .\check_status.py
```

---

## 4) Phase 2: Annotate (Label) the dataset

Before training, you need bounding-box annotations. Do this once over your base images in `data/extracted_frames/` (not the augmented set) — our augmentation step will automatically transform and carry labels forward.

What to label
- Use images under `data/extracted_frames/<video_name>/...`
- Keep a consistent class set across all projects.

Recommended tools (YOLO format)
- LabelImg: https://github.com/heartexlabs/labelImg
- CVAT (web, team-friendly): https://cvat.org / https://github.com/opencv/cvat
- Roboflow Annotate: https://roboflow.com/annotate

YOLO label format
- One .txt per image, same basename as the image
- Each line: `class_id cx cy w h` normalized to [0,1]
- Class IDs (by default):
  - 0: ball
  - 1: jersey_number
  - 2: net
  - 3: team_a
  - 4: team_b

Where to save labels
- Save the .txt files alongside the images in `data/extracted_frames/...`
- Example:
  ```
  data/extracted_frames/video_001/
    frame_000123.jpg
    frame_000123.txt   # YOLO labels for the image above
  ```

Quick checks (PowerShell)
```powershell
# Count images vs labels in extracted_frames
Get-ChildItem -Recurse .\data\extracted_frames -Include *.jpg,*.png | Measure-Object
Get-ChildItem -Recurse .\data\extracted_frames -Include *.txt | Measure-Object

# Peek a few labels
Get-ChildItem -Recurse .\data\extracted_frames -Include *.txt | Select-Object -First 3 | ForEach-Object { Get-Content $_.FullName | Select-Object -First 5 }
```

Notes
- Annotate the base images first; do not hand-annotate augmented images.
- Our augmentation step will read YOLO labels from `extracted_frames` and write transformed labels next to augmented images in `data/augmented/`.

---

## 5) Phase 3: Augment dataset (optional, recommended)

Takes images from `data/extracted_frames/` and writes augmented copies to `data/augmented/`, preserving the original per-video folder structure.

```powershell
python .\augment_dataset.py
```

Notes:
- YOLO bboxes are preserved/updated by our augmentation code.
- You can tune augmentation probabilities in `config/config.yaml`.

---

## 6) Phase 4: Split into train/val/test (by video)

Builds a YOLO-ready dataset under `data/yolo_dataset/` with:
- `train/val/test/images` and `train/val/test/labels`
- `data/yolo_dataset/data.yaml` with relative paths
- `split_summary.json` for bookkeeping

```powershell
python .\split_dataset.py
```

After this step, you should have structure like:
```
data/yolo_dataset/
  train/
    images/...
    labels/...
  val/
    images/...
    labels/...
  test/
    images/...
    labels/...
  data.yaml
  split_summary.json
```

If you do not have labels yet, the `labels` folders will be present but empty.

---

## 7) Phase 5: Train YOLO

The training runner reads `training` config from `config/config.yaml` and consumes `data/yolo_dataset/data.yaml`.

```powershell
python .\train_yolo.py
```

Behavior:
- If labels are missing/empty, training is skipped with a clear log message.
- When labels are present, full training runs and results go under `runs/train/`.

Where to put labels when you have them:
- YOLO format .txt files under:
  - `data/yolo_dataset/train/labels`
  - `data/yolo_dataset/val/labels`
  - `data/yolo_dataset/test/labels`

Each .txt line: `class cx cy w h` normalized to [0,1]. Classes are defined in `data.yaml`.

---

## 8) Quick prediction (sanity check)

You can run inference to verify the end-to-end flow, even without labels-trained weights:

```powershell
# Uses best weights if available, otherwise a small pretrained model.
python .\predict_yolo.py

# Or specify exactly
python .\predict_yolo.py --source "data/yolo_dataset/val/images" --weights "runs\train\basketball-yolov8s\weights\best.pt" --imgsz 640 --conf 0.25 --device 0
```

Outputs are written to `runs/predict/`.

---

## Typical order of operations

1) Install dependencies
2) Add videos to `data/raw_videos/`
3) Run extraction: `python .\main.py`
4) Annotate (YOLO labels) in `data/extracted_frames/`
5) Augment: `python .\augment_dataset.py`
6) Split: `python .\split_dataset.py`
7) Train: `python .\train_yolo.py` (skips cleanly if no labels)
8) Predict: `python .\predict_yolo.py`

When labeled data is ready, drop YOLO labels into train/val/test and re-run step 6.

---

## Tips and troubleshooting

- CUDA/GPU
  - If you have an RTX 3050, set `device: 0` in `config/config.yaml` under `training`.
  - If out-of-memory, try lowering `batch` or `imgsz`.

- Ultralytics import error
  - `pip install ultralytics`
  - If still failing, ensure your Python environment matches the one VS Code uses.

- Empty labels warnings during training
  - Expected if you have not annotated yet. Our `train_yolo.py` will skip training gracefully.

- Bad paths in `data.yaml`
  - We generate relative paths (e.g., `train/images`). If you hand-edit, keep them relative to `data.yaml` location.

- Where things get saved
  - Extracted frames: `data/extracted_frames/`
  
  - Augmented: `data/augmented/`
  - YOLO dataset: `data/yolo_dataset/`
  - Training runs: `runs/train/`
  - Predictions: `runs/predict/`

---

## Class names (default)

Defined in `data/yolo_dataset/data.yaml`:
- ball
- jersey_number
- net
- team_a
- team_b

You can customize these in the splitter or by editing `data.yaml` before training.
