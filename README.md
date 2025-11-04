# 🏀 Basketball Detection Pipeline

**End-to-end pipeline for basketball video analysis**: Video trimming → Frame extraction → Ball detection → Dataset preparation → YOLO training

---

## 🎯 Project Overview

**Goal**: Create a complete basketball analysis system that can:
- Detect basketballs in game footage
- Track players and detect jersey numbers
- Identify nets/hoops
- Distinguish between teams
- Count shots and goals

**Detection Classes**:
- `ball` - Basketball
- `jersey_number` - Player jersey numbers
- `net` - Basketball net/hoop
- `team_a` - Team A players
- `team_b` - Team B players

---

## 📁 Project Structure

```
basketball_pipeline/
├── config/
│   ├── config.yaml              # Frame extraction config
│   └── trim_ranges.yaml         # Video trimming ranges
├── src/
│   ├── __init__.py
│   ├── frame_extractor.py       # Frame extraction module
│   ├── quality_filter.py        # Frame quality filtering
│   ├── augmentation.py          # Data augmentation
│   ├── dataset_splitter.py      # Train/val/test split
│   └── utils.py                 # Utility functions
├── seperation/
│   ├── separate_images_by_ball.py  # Ball detection classifier
│   └── rename_add_skipped.py       # Frame organization
├── data/
│   ├── source_videos/           # Place raw videos here
│   ├── all_video_frames/        # Trimmed video clips
│   ├── extracted_frames/        # Extracted frames (by video)
│   │   ├── video_name__skip30/
│   │   │   ├── Ball_detected/
│   │   │   └── No_ball_detected/
│   └── yolo_dataset/            # YOLO-formatted dataset (auto-generated)
│       ├── train/
│       ├── val/
│       └── test/
├── runs/
│   ├── train/                   # Training outputs
│   ├── detect/                  # Detection results
│   └── mlflow/                  # Experiment tracking
├── run_pipeline.py              # ⭐ Complete pipeline runner
├── trim_videos.py               # Video trimming utility
├── main.py                      # Frame extraction
├── augment_dataset.py           # Data augmentation
├── split_dataset.py             # Dataset splitting
├── train_yolo.py                # YOLO training
├── predict_yolo.py              # Inference/prediction
└── requirements.txt             # Python dependencies
```

---

## 🚀 Quick Start

### Option 1: Complete Pipeline (Recommended)

Run the entire pipeline with an interactive wizard:

```bash
python run_pipeline.py
```

This will guide you through:
1. **Video trimming** - Select match sections from full game footage
2. **Frame extraction** - Extract frames at configurable intervals
3. **Ball detection** - Separate frames with/without basketballs

**Or run in auto mode** (using config file):

```bash
python run_pipeline.py --auto
```

### Option 2: Step-by-Step

#### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 2: Add Your Videos

Place basketball game videos in `data/source_videos/`

Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

#### Step 3: Trim Videos (Optional)

Extract specific match sections:

```bash
# Interactive mode
python trim_videos.py --input data/source_videos/game1.mp4

# Using config file
python trim_videos.py --config config/trim_ranges.yaml
```

#### Step 4: Extract Frames

```bash
python main.py --config config/config.yaml
```

Frames will be extracted to `data/extracted_frames/video_name__skip30/`

#### Step 5: Ball Detection

Separate frames with/without basketballs:

```bash
python seperation/separate_images_by_ball.py --input data/extracted_frames/video_name__skip30
```

Creates `Ball_detected/` and `No_ball_detected/` folders.

---

## 📊 Complete Workflow

### Pipeline Stages

```
1. Video Trimming
   ├─ Input: Full game videos (data/source_videos/)
   ├─ Process: Extract match sections by time ranges
   └─ Output: Trimmed clips (data/all_video_frames/)

2. Frame Extraction
   ├─ Input: Trimmed clips
   ├─ Process: Extract every Nth frame (configurable)
   └─ Output: Individual frames (data/extracted_frames/)

3. Ball Detection
   ├─ Input: Extracted frames
   ├─ Process: YOLO-based basketball detection
   └─ Output: Ball_detected/ and No_ball_detected/

4. Annotation
   ├─ Input: Filtered frames
   ├─ Process: Manual labeling (LabelImg, Roboflow, CVAT)
   └─ Output: YOLO .txt labels

5. Augmentation
   ├─ Command: python augment_dataset.py
   └─ Output: Augmented frames in data/augmented/

6. Dataset Splitting
   ├─ Command: python split_dataset.py
   └─ Output: train/val/test split in data/yolo_dataset/

7. Training
   ├─ Command: python train_yolo.py
   └─ Output: Trained model weights in runs/train/

8. Inference
   ├─ Command: python predict_yolo.py
   └─ Output: Predictions in runs/detect/
```

---

## ⚙️ Configuration

### Frame Extraction (`config/config.yaml`)

```yaml
frame_extraction:
  small_dataset_interval: 30   # Extract every 30th frame
  large_dataset_interval: 30
  threshold_videos: 10

quality_filter:
  brightness_min: 30
  brightness_max: 220
```

### Video Trimming (`config/trim_ranges.yaml`)

```yaml
videos:
  - path: "data/source_videos/game1.mp4"
    ranges:
      - "0:00-5:30"
      - "10:00-15:45"
  - path: "data/source_videos/game2.mp4"
    ranges:
      - "2:00-12:00"
```

---

## 🛠️ Individual Script Usage

### Trim Videos

```bash
# Interactive - specify ranges manually
python trim_videos.py --input data/source_videos/game.mp4 --ranges "0:00-5:00" "10:00-15:00"

# Batch mode - use config file
python trim_videos.py --config config/trim_ranges.yaml
```

### Extract Frames

```bash
# Default config
python main.py

# Custom config
python main.py --config my_config.yaml
```

### Ball Detection

```bash
# Process single folder
python seperation/separate_images_by_ball.py --input data/extracted_frames/video_game1__skip30

# Custom batch size and GPU
python seperation/separate_images_by_ball.py --input data/extracted_frames/video_game1__skip30 --batch-size 16 --device 0
```

### Augmentation

```bash
python augment_dataset.py
```

### Dataset Splitting

```bash
python split_dataset.py
```

### Training

```bash
# Train with default settings
python train_yolo.py

# Custom settings
python train_yolo.py --epochs 100 --batch 16 --img 640
```

### Inference

```bash
python predict_yolo.py
```

---

## 📈 Output Structure

After running the complete pipeline:

```
data/
├── source_videos/               # Your original videos
├── all_video_frames/            # Trimmed clips organized by video
│   ├── game1/
│   │   ├── game1_clip01.mp4
│   │   └── game1_clip02.mp4
│   └── game2/
├── extracted_frames/            # Extracted frames
│   ├── game1_clip01__skip30/
│   │   ├── Ball_detected/
│   │   │   ├── frame_000000.jpg
│   │   │   └── ...
│   │   └── No_ball_detected/
│   │       └── ...
│   └── game2_clip01__skip30/
└── yolo_dataset/                # YOLO-formatted dataset
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── val/
    │   ├── images/
    │   └── labels/
    └── test/
        ├── images/
        └── labels/

runs/
├── train/
│   └── basketball-yolov8s/
│       ├── weights/
│       │   ├── best.pt
│       │   └── last.pt
│       └── results.csv
└── detect/
    └── predictions/
```

---

## 🎥 Basketball Scoring Context

Understanding basketball scoring helps with annotation:
- **1 Point**: Free throw (game stopped, from free-throw line)
- **2 Points**: Shot inside the 3-point arc during live play
- **3 Points**: Shot from outside the 3-point arc

---

## 🔄 Workflow Examples

### Example 1: Process Single Game

```bash
# 1. Trim the game to match quarters
python trim_videos.py --input data/source_videos/game1.mp4 --ranges "0:00-10:00" "12:00-22:00"

# 2. Extract frames
python main.py

# 3. Detect balls
python seperation/separate_images_by_ball.py --input data/extracted_frames/game1_clip01__skip30

# 4. Annotate frames in Ball_detected/ folder
# (Use LabelImg or similar tool)

# 5. Augment
python augment_dataset.py

# 6. Split dataset
python split_dataset.py

# 7. Train
python train_yolo.py
```

### Example 2: Automated Batch Processing

```bash
# Set up config/trim_ranges.yaml with all your videos
# Then run the complete pipeline
python run_pipeline.py --auto
```

---

## 🛠️ Troubleshooting

### No videos found?
- Ensure videos are in `data/source_videos/`
- Check file extensions match supported formats

### Ball detection not working?
- Ensure YOLO model weights are present (`best_det.pt`, `yolo11n.pt`, or `yolov8s.pt`)
- Check GPU availability with `--device 0` or use CPU with `--device cpu`

### Training fails with "no labels found"?
- Ensure annotations exist in `data/yolo_dataset/train/labels/`
- Check label format is YOLO txt (class x_center y_center width height)

### Pipeline runs slow?
- Increase frame skip interval in config (e.g., skip every 60th frame)
- Reduce batch size for ball detection
- Use GPU for faster processing

---

## 📚 Additional Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Detailed setup instructions
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 3 steps
- **[RUNBOOK.md](RUNBOOK.md)** - Step-by-step operational guide
- **[PIPELINE_SUMMARY.md](PIPELINE_SUMMARY.md)** - Technical pipeline overview
- **[AUGMENTATION_GUIDE.md](AUGMENTATION_GUIDE.md)** - Data augmentation details
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - High-level project goals
- **[NEW_WORKFLOW.md](NEW_WORKFLOW.md)** - Latest workflow updates

---

## 🏀 Features

- ✅ **Automated video trimming** - Extract only relevant match sections
- ✅ **Smart frame extraction** - Adaptive sampling based on dataset size
- ✅ **Ball detection** - Pre-filter frames to focus on active gameplay
- ✅ **Quality filtering** - Remove poor quality/dark frames
- ✅ **Basketball-specific augmentation** - Realistic data augmentation
- ✅ **YOLO integration** - Complete training pipeline
- ✅ **MLflow tracking** - Experiment management
- ✅ **Organized output** - Clear folder structure by video/clip

---

## 🔧 Requirements

- Python 3.8+
- OpenCV
- Ultralytics YOLO
- PyTorch (CUDA recommended for training)
- NumPy, Pillow, PyYAML

See `requirements.txt` for complete list.

---

## 📧 Support

For questions, issues, or contributions:
- Check existing documentation in the repo
- Open an issue on GitHub
- Review example configurations in `config/`

---

**Happy Basketball AI Building! 🏀🚀**
