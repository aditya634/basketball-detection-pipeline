"""
Complete Basketball Pipeline - End-to-End Automation
Runs: Video Trimming → Frame Extraction → Ball Detection

Usage:
    python run_pipeline.py
    python run_pipeline.py --auto  # Skip interactive prompts (use config file)
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def list_source_videos(source_dir: str = "data/source_videos") -> List[Path]:
    """List all video files in source directory"""
    if not os.path.exists(source_dir):
        return []
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    videos = []
    for ext in video_extensions:
        videos.extend(Path(source_dir).glob(f'*{ext}'))
        videos.extend(Path(source_dir).glob(f'*{ext.upper()}'))
    
    return sorted(set(videos), key=lambda p: p.name.lower())


def get_time_ranges_interactive() -> List[str]:
    """Get time ranges from user input"""
    ranges = []
    print("Enter time ranges for match sections (e.g., '0:00-10:00', '15:00-25:00')")
    print("Format: MM:SS-MM:SS or HH:MM:SS-HH:MM:SS")
    print("Type 'done' when finished, or 'skip' to skip this video\n")
    
    while True:
        range_input = input(f"  Range {len(ranges)+1} (or 'done'/'skip'): ").strip()
        
        if range_input.lower() == 'done':
            break
        elif range_input.lower() == 'skip':
            return None
        elif range_input:
            ranges.append(range_input)
    
    return ranges if ranges else None


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"✗ Error running {description}: {e}")
        return False


def stage1_trim_videos(videos_to_trim: Dict[str, List[str]]) -> bool:
    """Stage 1: Trim videos to create clips"""
    print_header("STAGE 1: VIDEO TRIMMING")
    
    if not videos_to_trim:
        logger.warning("No videos selected for trimming. Skipping Stage 1.")
        return True
    
    success_count = 0
    for video_path, ranges in videos_to_trim.items():
        logger.info(f"\nTrimming: {Path(video_path).name}")
        logger.info(f"Ranges: {ranges}")
        
        cmd = [
            'python', 'trim_videos.py',
            '--input', video_path,
            '--ranges'
        ] + ranges
        
        if run_command(cmd, f"Trim {Path(video_path).name}"):
            success_count += 1
    
    logger.info(f"\n✓ Stage 1 Complete: {success_count}/{len(videos_to_trim)} videos trimmed successfully")
    return success_count > 0


def stage2_extract_frames() -> bool:
    """Stage 2: Extract frames from clips"""
    print_header("STAGE 2: FRAME EXTRACTION")
    
    # Check if clips exist
    clips_dir = "data/all_video_frames"
    if not os.path.exists(clips_dir):
        logger.error(f"Clips directory not found: {clips_dir}")
        return False
    
    cmd = ['python', 'main.py', '--config', 'config/config.yaml']
    
    return run_command(cmd, "Extract frames from clips")


def stage3_ball_detection(batch_size: int = 32, device: int = 0) -> bool:
    """Stage 3: Run ball detection on extracted frames"""
    print_header("STAGE 3: BALL DETECTION")
    
    extracted_dir = Path("data/extracted_frames")
    if not extracted_dir.exists():
        logger.error(f"Extracted frames directory not found: {extracted_dir}")
        return False
    
    # Find all frame folders
    frame_folders = [f for f in extracted_dir.iterdir() if f.is_dir()]
    
    if not frame_folders:
        logger.warning("No frame folders found for ball detection")
        return False
    
    logger.info(f"Found {len(frame_folders)} folder(s) to process")
    
    success_count = 0
    for folder in frame_folders:
        logger.info(f"\nProcessing: {folder.name}")
        
        cmd = [
            'python', 'seperation/separate_images_by_ball.py',
            '--input', str(folder),
            '--batch-size', str(batch_size),
            '--device', str(device)
        ]
        
        if run_command(cmd, f"Ball detection for {folder.name}"):
            success_count += 1
    
    logger.info(f"\n✓ Stage 3 Complete: {success_count}/{len(frame_folders)} folders processed")
    return success_count > 0


def copy_untrimmed_videos(source_videos: List[Path], videos_to_trim: Dict[str, List[str]]) -> bool:
    """Copy videos that weren't trimmed to all_video_frames/videoname/"""
    import shutil
    
    # Get list of videos that were NOT trimmed
    trimmed_paths = set(videos_to_trim.keys())
    untrimmed_videos = [v for v in source_videos if str(v) not in trimmed_paths]
    
    if not untrimmed_videos:
        return True
    
    logger.info(f"\nCopying {len(untrimmed_videos)} untrimmed video(s) to all_video_frames/")
    
    all_video_frames_dir = Path("data/all_video_frames")
    all_video_frames_dir.mkdir(parents=True, exist_ok=True)
    
    for video in untrimmed_videos:
        video_name = video.stem  # Get filename without extension
        dest_folder = all_video_frames_dir / video_name
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        dest_file = dest_folder / video.name
        
        logger.info(f"  Copying {video.name} -> {dest_folder.name}/{video.name}")
        shutil.copy2(str(video), str(dest_file))
    
    logger.info(f"✓ Copied {len(untrimmed_videos)} untrimmed video(s)")
    return True


def interactive_mode():
    """Run pipeline in interactive mode"""
    print_header("BASKETBALL PIPELINE - INTERACTIVE MODE")
    
    # List available videos
    source_videos = list_source_videos()
    
    if not source_videos:
        logger.error("No videos found in data/source_videos/")
        logger.info("Please add videos to data/source_videos/ and try again")
        return 1
    
    print(f"Found {len(source_videos)} video(s) in data/source_videos/:\n")
    for idx, video in enumerate(source_videos, 1):
        print(f"  {idx}. {video.name}")
    
    print("\n" + "-"*70)
    
    # Ask which videos to trim
    videos_to_trim = {}
    
    for video in source_videos:
        print(f"\n📹 Video: {video.name}")
        choice = input("  Trim this video? (y/n): ").strip().lower()
        
        if choice == 'y':
            ranges = get_time_ranges_interactive()
            if ranges:
                videos_to_trim[str(video)] = ranges
                logger.info(f"✓ Added {video.name} with {len(ranges)} range(s)")
            else:
                logger.info(f"  Skipped {video.name} (no ranges provided)")
        else:
            logger.info(f"  Will use full video for {video.name}")
    
    if len(source_videos) == 0:
        logger.warning("\nNo videos found to process.")
        return 0
    
    # Configuration
    print("\n" + "-"*70)
    print("Pipeline Configuration:")
    print(f"  Videos to trim: {len(videos_to_trim)}")
    print(f"  Videos to copy (no trimming): {len(source_videos) - len(videos_to_trim)}")
    
    batch_size = input("  Ball detection batch size (default 32): ").strip() or "32"
    device = input("  Device (0 for GPU, cpu for CPU, default 0): ").strip() or "0"
    
    try:
        batch_size = int(batch_size)
        device = 0 if device == "0" else device
    except ValueError:
        batch_size = 32
        device = 0
    
    print(f"  Batch size: {batch_size}")
    print(f"  Device: {device}")
    
    print("\n" + "-"*70)
    choice = input("\nStart pipeline? (y/n): ").strip().lower()
    if choice != 'y':
        logger.info("Pipeline cancelled by user")
        return 0
    
    # Run pipeline stages
    print_header("STARTING PIPELINE EXECUTION")
    
    # Stage 0: Copy untrimmed videos to all_video_frames
    logger.info("\n=== Organizing Videos ===")
    if not copy_untrimmed_videos(source_videos, videos_to_trim):
        logger.error("Failed to copy untrimmed videos")
        return 1
    
    # Stage 1: Trim videos
    if videos_to_trim:
        if not stage1_trim_videos(videos_to_trim):
            logger.error("Stage 1 failed. Stopping pipeline.")
            return 1
    
    # Stage 2: Extract frames
    if not stage2_extract_frames():
        logger.error("Stage 2 failed. Stopping pipeline.")
        return 1
    
    # Stage 3: Ball detection
    if not stage3_ball_detection(batch_size=batch_size, device=device):
        logger.error("Stage 3 failed. Stopping pipeline.")
        return 1
    
    print_header("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    print("Results:")
    print(f"  • Trimmed clips: data/all_video_frames/")
    print(f"  • Extracted frames: data/extracted_frames/")
    print(f"  • Ball detection results: Check Ball_detected / No_ball_detected folders")
    print("="*70 + "\n")
    
    return 0


def auto_mode():
    """Run pipeline automatically using config file"""
    print_header("BASKETBALL PIPELINE - AUTO MODE")
    
    logger.info("Running with config/trim_ranges.yaml")
    
    # Stage 1: Trim using config
    cmd = ['python', 'trim_videos.py', '--config', 'config/trim_ranges.yaml']
    if not run_command(cmd, "Trim videos from config"):
        logger.error("Stage 1 failed")
        return 1
    
    # Stage 2: Extract frames
    if not stage2_extract_frames():
        logger.error("Stage 2 failed")
        return 1
    
    # Stage 3: Ball detection
    if not stage3_ball_detection(batch_size=32, device=0):
        logger.error("Stage 3 failed")
        return 1
    
    print_header("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    return 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Basketball Pipeline")
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Run in automatic mode using config/trim_ranges.yaml'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for ball detection (auto mode only, default: 32)'
    )
    parser.add_argument(
        '--device',
        default='0',
        help='Device for ball detection (auto mode only, default: 0)'
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if args.auto:
        return auto_mode()
    else:
        return interactive_mode()


if __name__ == '__main__':
    sys.exit(main())
