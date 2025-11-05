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


def stage1_trim_videos(videos_to_trim: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
    """Stage 1: Trim videos to create clips
    
    Returns:
        Tuple of (success: bool, trimmed_video_folders: List[str])
    """
    print_header("STAGE 1: VIDEO TRIMMING")
    
    if not videos_to_trim:
        logger.warning("No videos selected for trimming. Skipping Stage 1.")
        return True, []
    
    success_count = 0
    trimmed_folders = []
    
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
            # Track the folder name for this video
            video_name = Path(video_path).stem
            trimmed_folders.append(f"data/all_video_frames/{video_name}")
    
    logger.info(f"\n✓ Stage 1 Complete: {success_count}/{len(videos_to_trim)} videos trimmed successfully")
    return success_count > 0, trimmed_folders


def stage2_extract_frames(only_from_folders: List[str] = None) -> bool:
    """Stage 2: Extract frames from clips
    
    Args:
        only_from_folders: If provided, only process videos in these specific folders
    """
    print_header("STAGE 2: FRAME EXTRACTION")
    
    # Check if clips exist
    clips_dir = "data/all_video_frames"
    if not os.path.exists(clips_dir):
        logger.error(f"Clips directory not found: {clips_dir}")
        return False
    
    # If specific folders provided, process only those
    if only_from_folders:
        logger.info(f"Processing only newly trimmed videos ({len(only_from_folders)} folder(s))")
        
        success_count = 0
        for folder in only_from_folders:
            if not os.path.exists(folder):
                logger.warning(f"Folder not found, skipping: {folder}")
                continue
            
            logger.info(f"\nExtracting frames from: {Path(folder).name}")
            cmd = ['python', 'main.py', '--config', 'config/config.yaml', '--video-dir', folder]
            
            if run_command(cmd, f"Extract frames from {Path(folder).name}"):
                success_count += 1
        
        logger.info(f"\n✓ Extracted frames from {success_count}/{len(only_from_folders)} folder(s)")
        return success_count > 0
    else:
        # Process all videos (legacy behavior)
        logger.info("Processing all videos in all_video_frames/")
        cmd = ['python', 'main.py', '--config', 'config/config.yaml']
        return run_command(cmd, "Extract frames from clips")


def stage3_ball_detection(only_from_folders: List[str] = None, batch_size: int = 32, device: int = 0) -> bool:
    """Stage 3: Run ball detection on extracted frames
    
    Args:
        only_from_folders: If provided, only process frames from these specific video folders
        batch_size: Batch size for inference
        device: GPU device (0) or 'cpu'
    """
    print_header("STAGE 3: BALL DETECTION")
    
    extracted_dir = Path("data/extracted_frames")
    if not extracted_dir.exists():
        logger.error(f"Extracted frames directory not found: {extracted_dir}")
        return False
    
    # Determine which folders to process
    if only_from_folders:
        # Convert video folder names to extracted frame folder names
        # e.g., "data/all_video_frames/game1" -> "data/extracted_frames/game1_clip01__skip30"
        frame_folders = []
        for video_folder in only_from_folders:
            video_name = Path(video_folder).name
            # Find all extracted frame folders that start with this video name
            matching = [f for f in extracted_dir.iterdir() 
                       if f.is_dir() and f.name.startswith(video_name)]
            frame_folders.extend(matching)
        
        if not frame_folders:
            logger.warning(f"No extracted frame folders found for the trimmed videos")
            return False
        
        logger.info(f"Processing only newly extracted frames ({len(frame_folders)} folder(s))")
    else:
        # Process all frame folders
        frame_folders = [f for f in extracted_dir.iterdir() if f.is_dir()]
        logger.info(f"Processing all frame folders ({len(frame_folders)} folder(s))")
    
    if not frame_folders:
        logger.warning("No frame folders found for ball detection")
        return False
    
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


def get_already_trimmed_videos() -> set:
    """Get list of videos that were already trimmed (have folders in all_video_frames)"""
    all_video_frames_dir = Path("data/all_video_frames")
    if not all_video_frames_dir.exists():
        return set()
    
    # Get all folder names in all_video_frames
    trimmed_folders = {folder.name for folder in all_video_frames_dir.iterdir() if folder.is_dir()}
    return trimmed_folders


def interactive_mode():
    """Run pipeline in interactive mode"""
    print_header("BASKETBALL PIPELINE - INTERACTIVE MODE")
    
    # List available videos
    source_videos = list_source_videos()
    
    if not source_videos:
        logger.error("No videos found in data/source_videos/")
        logger.info("Please add videos to data/source_videos/ and try again")
        return 1
    
    # Check which videos were already trimmed
    already_trimmed = get_already_trimmed_videos()
    
    print(f"Found {len(source_videos)} video(s) in data/source_videos/:\n")
    for idx, video in enumerate(source_videos, 1):
        video_stem = video.stem  # filename without extension
        status = "✓ Already trimmed" if video_stem in already_trimmed else "○ Not trimmed yet"
        print(f"  {idx}. {video.name:40s} [{status}]")
    
    print("\n" + "-"*70)
    
    # Filter out already trimmed videos
    untrimmed_videos = [v for v in source_videos if v.stem not in already_trimmed]
    
    if not untrimmed_videos:
        print("\n✓ All videos have already been trimmed!")
        choice = input("\nDo you want to re-trim some videos? (y/n): ").strip().lower()
        if choice != 'y':
            logger.info("No new videos to process. Exiting.")
            return 0
        # If user wants to re-trim, use all videos
        untrimmed_videos = source_videos
    else:
        print(f"\n📌 {len(untrimmed_videos)} video(s) not trimmed yet")
        print(f"📌 {len(already_trimmed)} video(s) already trimmed (will be skipped)\n")
    
    print("-"*70)
    
    # Ask which videos to trim
    videos_to_trim = {}
    
    for video in untrimmed_videos:
        video_stem = video.stem
        is_already_trimmed = video_stem in already_trimmed
        
        print(f"\n📹 Video: {video.name}")
        if is_already_trimmed:
            print(f"   ⚠️  Already trimmed (folder exists: data/all_video_frames/{video_stem}/)")
            choice = input("   Re-trim this video? (y/n): ").strip().lower()
        else:
            choice = input("   Trim this video? (y/n): ").strip().lower()
        
        if choice == 'y':
            ranges = get_time_ranges_interactive()
            if ranges:
                videos_to_trim[str(video)] = ranges
                logger.info(f"✓ Added {video.name} with {len(ranges)} range(s)")
            else:
                logger.info(f"  Skipped {video.name} (no ranges provided)")
        else:
            if not is_already_trimmed:
                logger.info(f"  Will use full video for {video.name}")
            else:
                logger.info(f"  Skipping {video.name} (already trimmed)")
    
    if len(untrimmed_videos) == 0 and len(videos_to_trim) == 0:
        logger.warning("\nNo videos to process.")
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
    
    # Stage 1: Trim videos (returns success status and list of trimmed folders)
    trimmed_folders = []
    if videos_to_trim:
        success, trimmed_folders = stage1_trim_videos(videos_to_trim)
        if not success:
            logger.error("Stage 1 failed. Stopping pipeline.")
            return 1
    
    # Stage 2: Extract frames (only from newly trimmed videos if any were trimmed)
    if trimmed_folders:
        logger.info(f"\n=== Processing {len(trimmed_folders)} newly trimmed video(s) ===")
        if not stage2_extract_frames(only_from_folders=trimmed_folders):
            logger.error("Stage 2 failed. Stopping pipeline.")
            return 1
    else:
        # No trimming happened, process all videos (legacy behavior)
        if not stage2_extract_frames():
            logger.error("Stage 2 failed. Stopping pipeline.")
            return 1
    
    # Stage 3: Ball detection (only on newly extracted frames)
    if not stage3_ball_detection(only_from_folders=trimmed_folders if trimmed_folders else None, 
                                  batch_size=batch_size, device=device):
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
    """Run pipeline automatically using config file
    
    Note: Auto mode currently processes all videos. 
    For selective processing, use interactive mode.
    """
    print_header("BASKETBALL PIPELINE - AUTO MODE")
    
    logger.info("Running with config/trim_ranges.yaml")
    logger.info("Note: Auto mode processes ALL videos in all_video_frames/")
    
    # Stage 1: Trim using config
    cmd = ['python', 'trim_videos.py', '--config', 'config/trim_ranges.yaml']
    if not run_command(cmd, "Trim videos from config"):
        logger.error("Stage 1 failed")
        return 1
    
    # Stage 2: Extract frames (processes all videos in auto mode)
    if not stage2_extract_frames():
        logger.error("Stage 2 failed")
        return 1
    
    # Stage 3: Ball detection (processes all extracted frames in auto mode)
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
