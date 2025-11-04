# Basketball Pipeline - New Workflow

## Folder Structure

```
/project_root
├── source_videos/              # Raw uploaded videos (DO NOT process directly)
│   ├── courtMumbai_vid12.mp4
│   ├── courtDelhi_vid07.mp4
│   └── ...
│
├── all_video_frames/           # Curated clips (created by trim_videos.py)
│   ├── courtMumbai_vid12/
│   │   ├── courtMumbai_vid12_clip01.mp4
│   │   ├── courtMumbai_vid12_clip02.mp4
│   │   └── courtMumbai_vid12_clip03.mp4
│   ├── courtDelhi_vid07/
│   │   ├── courtDelhi_vid07_clip01.mp4
│   │   └── ...
│   └── ...
│
├── extracted_frames/           # Frames from clips (created by main.py)
│   ├── courtMumbai_vid12_clip01__skip25/
│   │   ├── courtMumbai_vid12_clip01_skipped_25_frame_000001.jpg
│   │   ├── courtMumbai_vid12_clip01_skipped_25_frame_000002.jpg
│   │   └── ...
│   └── ...
```

## Workflow Steps

### Step 1: Trim Videos (Remove Breaks)
Extract only match sections from raw videos, removing breaks and pauses.

**Using config file (recommended for multiple videos):**
```bash
# 1. Edit config/trim_ranges.yaml with your time ranges
# 2. Run:
python trim_videos.py --config config/trim_ranges.yaml
```

**Using command line (for single video):**
```bash
python trim_videos.py \
  --input "source_videos/courtMumbai_vid12.mp4" \
  --ranges "0:00-15:00" "25:00-35:00" "45:00-55:00"
```

Output: Clips saved to `all_video_frames/videoname/`

### Step 2: Extract Frames
Extract every 25th frame from trimmed clips.

```bash
# Process all clips from all_video_frames/
python main.py --config config/config.yaml

# Or specify custom clip directory
python main.py --video-dir "all_video_frames" --config config/config.yaml
```

Output: Frames saved to `extracted_frames/clipname__skip25/`

### Step 3: Separate Frames by Ball Detection
Move frames to Ball_detected / No_ball_detected folders.

```bash
# Process specific clip frames
python seperation/separate_images_by_ball.py \
  --input "extracted_frames/courtMumbai_vid12_clip01__skip25" \
  --batch-size 32 \
  --device 0

# Process all frames in extracted_frames/
for folder in extracted_frames/*/; do
  python seperation/separate_images_by_ball.py --input "$folder" --batch-size 32
done
```

### Step 4: Annotate & Train
1. Review frames in Ball_detected folders
2. Annotate with YOLO format
3. Run augmentation and training pipeline

## Time Format Examples

For `trim_videos.py --ranges`:
- `"5:30-20:00"` = 5 min 30 sec to 20 min 0 sec
- `"1:05:30-1:25:00"` = 1 hr 5 min 30 sec to 1 hr 25 min 0 sec

## Quick Start Example

```bash
# 1. Trim one video
python trim_videos.py \
  --input "source_videos/bnsw_vs_ripcity.mp4" \
  --ranges "2:00-12:00" "18:00-28:00"

# 2. Extract frames from clips
python main.py --config config/config.yaml

# 3. Separate by ball detection
python seperation/separate_images_by_ball.py \
  --input "extracted_frames/bnsw_vs_ripcity_clip01__skip25" \
  --batch-size 32
```

## Notes

- **Frame interval**: Currently fixed at 25 (extracts every 25th frame)
- **Naming convention**: `videoname_clipNN_skipped_25_frame_NNNNNN.jpg`
- **GPU**: Ball detection uses GPU by default (--device 0)
- **Batch size**: 32 recommended for RTX 3050, adjust if out-of-memory errors occur
