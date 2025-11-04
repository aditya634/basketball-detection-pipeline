# Basketball Dataset Creation Pipeline

## Phase 1: Frame Extraction

This pipeline extracts frames from basketball game videos to create a dataset for YOLO object detection and tracking.

---

## 🏀 Project Overview

**Goal**: Detect players, track them, detect goals/shots, and count individual player and team goals.

**Classes for Detection**:
- `ball` - The basketball
- `jersey_number` - Player jersey numbers
- `net` - Basketball net/hoop
- `team_a` - Players from team A
- `team_b` - Players from team B

**Basketball Scoring Context**:
- **1 Point**: Free throw (game stopped, from free-throw line)
- **2 Points**: Any shot inside the 3-point arc during live play
- **3 Points**: Any shot from outside the 3-point arc

---

## 📁 Project Structure

```
basketball_pipeline/
├── config/
│   └── config.yaml              # Configuration file
├── src/
│   ├── __init__.py
│   ├── frame_extractor.py       # Frame extraction module
│   └── utils.py                 # Utility functions
├── data/
│   ├── raw_videos/              # Place your videos here
│   ├── extracted_frames/        # Extracted frames (auto-generated)
│   └── augmented/               # Augmented images (auto-generated)
├── main.py                      # Main pipeline script
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Add Your Videos

Place your basketball game videos in the `data/raw_videos/` folder.

Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

### 3. Configure Settings (Optional)

Edit `config/config.yaml` to adjust:
- Frame extraction intervals
- Output format and quality

### 4. Run the Pipeline

```bash
python main.py
```

Or with custom config:

```bash
python main.py --config config/config.yaml
```

---

## 🔄 End-to-end pipeline (no labels yet)

If you're just wiring up the pipeline and don't have annotations yet, you can still run the stages to verify everything works. Training will be skipped automatically when no labels are found.

1) Extract frames (Phase 1)
- Place videos under `data/raw_videos/`
- Run `python main.py`

2) Augment the dataset (Phase 3)
- Run `python augment_dataset.py`

3) Split into train/val/test (by video) and build YOLO structure (Phase 4)
- Run `python split_dataset.py`

4) Train YOLO (Phase 5)
- Run `python train_yolo.py`
- If there are no labels, the script detects this and skips training gracefully with a clear message.

5) Optional: Quick predictions to sanity-check the model/inference path
- Run `python predict_yolo.py` to perform inference on `data/yolo_dataset/val/images` with either your best weights (if available) or a small pretrained model fallback.

When you add labels later (YOLO txt files in `train/labels`, `val/labels`, `test/labels`), re-run `python train_yolo.py` to start real training.

---

## ⚙️ Configuration

Edit `config/config.yaml` to customize the pipeline:

### Frame Extraction
- **Small dataset** (≤10 videos): Extract every 3rd frame
- **Large dataset** (>10 videos): Extract every 7th frame

### Annotation
- Create YOLO .txt labels alongside images in `data/extracted_frames/`

---

## 📊 Pipeline Steps

### Step 1: Frame Extraction
- Automatically detects dataset size (number of videos)
- Extracts frames at adaptive intervals:
  - **Small dataset**: Every 3rd frame
  - **Large dataset**: Every 7th frame
- Organizes frames by video in separate folders
- Saves metadata (timestamps, frame info)

### Step 2: Annotation
- Add YOLO labels next to images in `data/extracted_frames/`

---

## 💻 Usage Examples

### Basic Usage
```bash
python main.py
```

### Custom Video Directory
```bash
python main.py --video-dir "path/to/videos"
```

### Skip Frame Extraction (Only Filter)
```bash
python main.py --skip-extraction
```

 

### Custom Output Directory
```bash
python main.py --output-dir "path/to/output"
```

---

## 📈 Output

After running the pipeline:

1. **Extracted Frames**: `data/extracted_frames/video_[name]/`
2. **Augmented**: `data/augmented/video_[name]/`
3. **Metadata**: `data/pipeline_metadata_[timestamp].json`
4. **Logs**: `pipeline.log`

---

## 🔄 Next Steps (Phase 2 & 3)

After Phase 1 is complete:

1. **Annotation**: Annotate frames with YOLO format
   - Use tools like LabelImg, Roboflow, or CVAT
   - Define bounding boxes for: ball, jersey_number, net, team_a, team_b

2. **Phase 2 - Augmentation**: Apply basketball-specific augmentations
   - Brightness/contrast variations
   - Horizontal flip (NOT vertical)
   - Small rotations
   - Zoom variations

3. **Phase 3 - Dataset Splitting**: Split into train/test/val
   - Recommended: 70% train, 20% test, 10% validation

4. **Phase 4 - Training**: Train YOLO model for detection & tracking

---

## 🛠️ Troubleshooting

### No videos found?
- Make sure videos are in `data/raw_videos/`
- Check supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

 

### Pipeline runs slow?
- Reduce frame extraction by increasing interval in config
- Disable quality filtering: `python main.py --skip-filtering`

---

## 📝 Notes

- **Adaptive Sampling**: The pipeline automatically adjusts frame extraction based on dataset size
- **Organized Output**: Frames are organized by video for easy tracking
- **Organized Output**: Frames are organized by video for easy tracking
- **Metadata Tracking**: Complete metadata saved for reproducibility

---

## 🏀 Basketball-Specific Features

The pipeline is optimized for basketball with:
- Motion detection for active gameplay
- Brightness filtering for indoor court lighting
- Frame organization by game/video
- Ready for multi-class YOLO annotation (ball, jersey_number, net, team_a, team_b)

---

## 📧 Support

For questions or issues, please refer to the documentation or contact the development team.

**Happy Dataset Building! 🏀🚀**
