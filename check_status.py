"""
Pipeline Status Checker
Check the current status of your basketball dataset pipeline
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


def check_pipeline_status():
    """Check and display pipeline status"""
    
    print("="*70)
    print("  🏀 BASKETBALL DATASET PIPELINE - STATUS CHECK")
    print("="*70 + "\n")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    # Check directories
    raw_videos_dir = os.path.join(data_dir, 'raw_videos')
    extracted_dir = os.path.join(data_dir, 'extracted_frames')
    # quality frames removed; annotate directly on extracted frames
    
    # Count videos
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    num_videos = count_files_in_dir(raw_videos_dir, video_extensions)
    
    # Count extracted frames
    num_extracted_subdirs = count_subdirs(extracted_dir)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    total_extracted = 0
    if num_extracted_subdirs > 0:
        for subdir in Path(extracted_dir).iterdir():
            if subdir.is_dir():
                total_extracted += count_files_in_dir(str(subdir), image_extensions)
    else:
        total_extracted = count_files_in_dir(extracted_dir, image_extensions)
    
    # No separate quality frames step anymore
    
    # Display status
    print("📊 DATASET STATUS:\n")
    
    # Input videos
    print(f"  📹 Raw Videos:")
    print(f"     Location: {raw_videos_dir}")
    print(f"     Count: {num_videos} video(s)")
    
    if num_videos == 0:
        print(f"     ⚠️  No videos found! Add videos to start.")
    else:
        print(f"     ✅ Videos ready for processing")
    
    print()
    
    # Extracted frames
    print(f"  🎞️  Extracted Frames:")
    print(f"     Location: {extracted_dir}")
    print(f"     Video folders: {num_extracted_subdirs}")
    print(f"     Total frames: {total_extracted}")
    
    if total_extracted == 0:
        print(f"     ℹ️  No frames extracted yet. Run: python main.py")
    else:
        print(f"     ✅ Frames extracted")
    
    print()
    
    # Skip quality frames section
    
    print()
    print("="*70)
    
    # Next steps
    print("  📋 NEXT STEPS:\n")
    
    if num_videos == 0:
        print("  1. Add basketball videos to: data/raw_videos/")
        print("  2. Run the pipeline: python main.py")
    elif total_extracted == 0:
        print("  1. Run the pipeline: python main.py")
    else:
        print("  ✅ Phase 1 Complete!")
        print("  1. Annotate frames in: data/extracted_frames/")
        print("  2. Use YOLO format for annotation")
        print("  3. Prepare for Phase 2: Augmentation")
    
    print("\n" + "="*70 + "\n")
    
    # Configuration check
    config_file = os.path.join(base_dir, 'config', 'config.yaml')
    if os.path.exists(config_file):
        print("  ✅ Configuration file: config/config.yaml")
    else:
        print("  ⚠️  Configuration file missing!")
    
    # Requirements check
    req_file = os.path.join(base_dir, 'requirements.txt')
    if os.path.exists(req_file):
        print("  ✅ Requirements file: requirements.txt")
    else:
        print("  ⚠️  Requirements file missing!")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    check_pipeline_status()
