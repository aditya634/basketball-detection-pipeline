# Basketball Dataset Creation Pipeline - Quick Start Guide

## Getting Started in 3 Steps! 🏀

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Add Your Videos
Place your basketball game videos in:
```
data/raw_videos/
```

### Step 3: Run the Pipeline
```bash
python main.py
```

---

## What Happens?

1. **Frame Extraction** ⚡
   - Automatically detects your dataset size
   - Small dataset (≤10 videos) → Every 3rd frame
   - Large dataset (>10 videos) → Every 7th frame
   - Saves to: `data/extracted_frames/`

2. **Ready for Annotation** 📝
   - Frames ready in `data/extracted_frames/`
   - Next: Annotate with YOLO format!

---

## Expected Output

```
basketball_pipeline/
├── data/
│   ├── raw_videos/
│   │   ├── game1.mp4
│   │   └── game2.mp4
│   ├── extracted_frames/
│   │   ├── video_game1/
│   │   │   ├── game1_frame_000000.jpg
│   │   │   ├── game1_frame_000001.jpg
│   │   │   └── ...
│   │   └── video_game2/
│   │       └── ...
│   └── augmented/
│       └── ...
```

---

## Customization

### Want to adjust settings?
Edit `config/config.yaml`:

```yaml
frame_extraction:
  small_dataset_interval: 3    # Change to 2 for more frames
  large_dataset_interval: 7    # Change to 5 for more frames

 
```

---

## Command Line Options

```bash
# Basic run
python main.py

# Use custom config
python main.py --config path/to/config.yaml

# Use custom video directory
python main.py --video-dir path/to/videos

# Skip extraction (only filter)
python main.py --skip-extraction

 

# Custom output location
python main.py --output-dir path/to/output
```

---

## Troubleshooting

### ❌ "No video files found"
- Check that videos are in `data/raw_videos/`
- Supported: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`

 

### ❌ "Pipeline too slow"
- Increase frame interval in config (extract fewer frames)
- Process fewer videos at once

---

## What's Next?

1. ✅ **Phase 1 Complete** - Frames extracted and ready!
2. 🎯 **Annotate** - Label your frames with YOLO format
3. 🔄 **Phase 2** - Data augmentation (coming next)
4. 📊 **Phase 3** - Train/test/val split
5. 🚀 **Phase 4** - Train your YOLO model!

---

## Basketball Classes to Annotate

When annotating, label these objects:
- `ball` - The basketball
- `jersey_number` - Player jersey numbers
- `net` - Basketball net/hoop
- `team_a` - Players from team A
- `team_b` - Players from team B

---

**Ready to build your basketball AI! 🏀🚀**
