"""
Pipeline Status Checker
Check the current status of your basketball dataset pipeline
Shows: Source Videos → Trimmed Clips → Extracted Frames → Ball Detection
"""

import os
from pathlib import Path


def count_files_in_dir(directory, extensions=None):
    """Count files in directory"""
    if not os.path.exists(directory):
        return 0
    
    files = list(Path(directory).iterdir())
    if extensions:
        files = [f for f in files if f.suffix.lower() in extensions]
    
    return len([f for f in files if f.is_file()])


def count_subdirs(directory):
    """Count subdirectories"""
    if not os.path.exists(directory):
        return 0
    return len([d for d in Path(directory).iterdir() if d.is_dir()])


def count_files_recursive(directory, extensions=None):
    """Recursively count files in directory and subdirectories"""
    if not os.path.exists(directory):
        return 0
    
    count = 0
    path = Path(directory)
    
    # Count files in all subdirectories
    for subdir in path.iterdir():
        if subdir.is_dir():
            files = list(subdir.iterdir())
            if extensions:
                files = [f for f in files if f.is_file() and f.suffix.lower() in extensions]
            else:
                files = [f for f in files if f.is_file()]
            count += len(files)
    
    return count


def check_ball_detection_folders():
    """Check Ball_detected and No_ball_detected folders inside extracted_frames"""
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    extracted_dir = base_dir / "data" / "extracted_frames"
    
    ball_detected_count = 0
    no_ball_count = 0
    folders_with_detection = 0
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    if not extracted_dir.exists():
        return 0, 0, 0
    
    # Check each video folder in extracted_frames
    for video_folder in extracted_dir.iterdir():
        if not video_folder.is_dir():
            continue
        
        ball_detected_dir = video_folder / "Ball_detected"
        no_ball_dir = video_folder / "No_ball_detected"
        
        has_detection = False
        
        if ball_detected_dir.exists():
            files = [f for f in ball_detected_dir.iterdir() 
                    if f.is_file() and f.suffix.lower() in image_extensions]
            ball_detected_count += len(files)
            if len(files) > 0:
                has_detection = True
        
        if no_ball_dir.exists():
            files = [f for f in no_ball_dir.iterdir() 
                    if f.is_file() and f.suffix.lower() in image_extensions]
            no_ball_count += len(files)
            if len(files) > 0:
                has_detection = True
        
        if has_detection:
            folders_with_detection += 1
    
    return ball_detected_count, no_ball_count, folders_with_detection


def check_pipeline_status():
    """Check and display pipeline status"""
    
    print("="*70)
    print("  🏀 BASKETBALL DATASET PIPELINE - STATUS CHECK")
    print("="*70 + "\n")
    
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    data_dir = base_dir / 'data'
    
    # Check directories
    source_videos_dir = data_dir / 'source_videos'
    all_video_frames_dir = data_dir / 'all_video_frames'
    extracted_dir = data_dir / 'extracted_frames'
    
    # Count videos
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    num_source_videos = count_files_in_dir(str(source_videos_dir), video_extensions)
    
    # Count trimmed video folders
    num_trimmed_folders = count_subdirs(str(all_video_frames_dir))
    num_trimmed_videos = count_files_recursive(str(all_video_frames_dir), video_extensions)
    
    # Count extracted frames (includes frames in Ball_detected/No_ball_detected)
    num_extracted_folders = count_subdirs(str(extracted_dir))
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # Check ball detection results first
    ball_detected, no_ball, folders_with_detection = check_ball_detection_folders()
    
    # Total frames = classified frames + unclassified frames
    unclassified_frames = count_files_recursive(str(extracted_dir), image_extensions)
    total_extracted = ball_detected + no_ball + unclassified_frames
    
    # Display status
    print("📊 PIPELINE STATUS:\n")
    
    # Stage 1: Source Videos
    print(f"  📹 STAGE 1: Source Videos")
    print(f"     Location: {source_videos_dir}")
    print(f"     Count: {num_source_videos} video(s)")
    
    if num_source_videos == 0:
        print(f"     ⚠️  No videos found! Add videos to data/source_videos/")
    else:
        print(f"     ✅ Videos ready for processing")
    
    print()
    
    # Stage 2: Trimmed Clips
    print(f"  ✂️  STAGE 2: Trimmed/Organized Videos")
    print(f"     Location: {all_video_frames_dir}")
    print(f"     Video folders: {num_trimmed_folders}")
    print(f"     Video files: {num_trimmed_videos}")
    
    if num_trimmed_folders == 0:
        print(f"     ℹ️  No videos trimmed yet. Run: python run_pipeline.py")
    else:
        print(f"     ✅ {num_trimmed_folders} video folder(s) ready")
    
    print()
    
    # Stage 3: Extracted Frames
    print(f"  🎞️  STAGE 3: Extracted Frames")
    print(f"     Location: {extracted_dir}")
    print(f"     Frame folders: {num_extracted_folders}")
    print(f"     Total frames: {total_extracted}")
    print(f"       • Classified: {ball_detected + no_ball}")
    print(f"       • Unclassified: {unclassified_frames}")
    
    if total_extracted == 0:
        print(f"     ℹ️  No frames extracted yet. Run: python run_pipeline.py")
    else:
        print(f"     ✅ {total_extracted} frame(s) extracted")
    
    print()
    
    # Stage 4: Ball Detection
    print(f"  ⚽ STAGE 4: Ball Detection Results")
    print(f"     Ball detected: {ball_detected} frames")
    print(f"     No ball: {no_ball} frames")
    print(f"     Folders processed: {folders_with_detection}/{num_extracted_folders}")
    print(f"     Total classified: {ball_detected + no_ball} frames")
    
    if ball_detected + no_ball == 0:
        print(f"     ℹ️  No ball detection done yet. Run: python run_pipeline.py")
    else:
        detection_rate = (ball_detected / (ball_detected + no_ball) * 100) if (ball_detected + no_ball) > 0 else 0
        print(f"     ✅ Detection complete ({detection_rate:.1f}% with ball)")
    
    print()
    print("="*70)
    
    # Next steps
    print("  📋 NEXT STEPS:\n")
    
    if num_source_videos == 0:
        print("  1. Add basketball videos to: data/source_videos/")
        print("  2. Run the pipeline: python run_pipeline.py")
    elif num_trimmed_folders == 0:
        print("  1. Run the pipeline: python run_pipeline.py")
        print("  2. Choose which videos to trim or use full videos")
    elif total_extracted == 0:
        print("  1. Pipeline will extract frames automatically")
        print("  2. Run: python run_pipeline.py (if not already running)")
    elif ball_detected + no_ball == 0:
        print("  1. Pipeline will run ball detection automatically")
        print("  2. Run: python run_pipeline.py (if not already running)")
    else:
        print("  ✅ Pipeline Complete!")
        print("  1. Review ball detection results:")
        print(f"     • Ball_detected/ ({ball_detected} frames)")
        print(f"     • No_ball_detected/ ({no_ball} frames)")
        print("  2. Annotate frames with ball for YOLO training")
        print("  3. Run augmentation: python augment_dataset.py")
        print("  4. Train YOLO model: python train_yolo.py")
    
    print("\n" + "="*70 + "\n")
    
    # Configuration check
    print("  📁 CONFIGURATION FILES:\n")
    
    config_file = base_dir / 'config' / 'config.yaml'
    if config_file.exists():
        print("  ✅ Frame extraction config: config/config.yaml")
    else:
        print("  ⚠️  config/config.yaml missing!")
    
    trim_config = base_dir / 'config' / 'trim_ranges.yaml'
    if trim_config.exists():
        print("  ✅ Trim ranges config: config/trim_ranges.yaml")
    else:
        print("  ℹ️  config/trim_ranges.yaml (optional)")
    
    req_file = base_dir / 'requirements.txt'
    if req_file.exists():
        print("  ✅ Requirements file: requirements.txt")
    else:
        print("  ⚠️  requirements.txt missing!")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    check_pipeline_status()
