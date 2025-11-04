"""
Video Trimming Script
Trims basketball videos to extract only match sections (removing breaks/pauses)

Usage:
    # Using time ranges from command line
    python trim_videos.py --input "source_videos/courtMumbai_vid12.mp4" --ranges "0:00-15:00" "25:00-35:00" "45:00-55:00"
    
    # Using a YAML config file
    python trim_videos.py --config config/trim_ranges.yaml
    
    # Process single video with output override
    python trim_videos.py --input "source_videos/video.mp4" --ranges "5:30-20:00" --output "all_video_frames"
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def parse_timestamp(timestamp: str) -> float:
    """Convert timestamp string (MM:SS or HH:MM:SS) to seconds.
    
    Args:
        timestamp: Time in format "MM:SS" or "HH:MM:SS"
        
    Returns:
        Total seconds as float
        
    Examples:
        "5:30" -> 330.0
        "1:05:30" -> 3930.0
    """
    parts = timestamp.split(':')
    if len(parts) == 2:  # MM:SS
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Use MM:SS or HH:MM:SS")


def parse_range(range_str: str) -> Tuple[float, float]:
    """Parse time range string like "5:30-20:00" into (start_sec, end_sec).
    
    Args:
        range_str: Range in format "START-END" (e.g., "5:30-20:00")
        
    Returns:
        Tuple of (start_seconds, end_seconds)
    """
    if '-' not in range_str:
        raise ValueError(f"Invalid range format: {range_str}. Use START-END (e.g., '5:30-20:00')")
    
    start_str, end_str = range_str.split('-', 1)
    start_sec = parse_timestamp(start_str.strip())
    end_sec = parse_timestamp(end_str.strip())
    
    if end_sec <= start_sec:
        raise ValueError(f"End time must be after start time: {range_str}")
    
    return start_sec, end_sec


def trim_video_clip(
    input_video: str,
    output_path: str,
    start_sec: float,
    end_sec: float
) -> bool:
    """Trim a video clip using ffmpeg.
    
    Args:
        input_video: Path to source video
        output_path: Path for output clip
        start_sec: Start time in seconds
        end_sec: End time in seconds
        
    Returns:
        True if successful, False otherwise
    """
    duration = end_sec - start_sec
    
    # ffmpeg command: -ss (start), -t (duration), -c copy (fast, no re-encode)
    cmd = [
        'ffmpeg',
        '-y',  # overwrite output
        '-ss', str(start_sec),
        '-i', input_video,
        '-t', str(duration),
        '-c', 'copy',  # copy streams (fast, no quality loss)
        '-avoid_negative_ts', '1',
        output_path
    ]
    
    try:
        logger.info(f"  Trimming {start_sec:.1f}s to {end_sec:.1f}s ({duration:.1f}s) -> {Path(output_path).name}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"  ffmpeg error: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg and add to PATH.")
        logger.error("Download from: https://ffmpeg.org/download.html")
        return False


def process_video(
    input_video: str,
    time_ranges: List[Tuple[float, float]],
    output_base_dir: str = "all_video_frames"
) -> List[str]:
    """Process a video and create clips for each time range.
    
    Args:
        input_video: Path to source video
        time_ranges: List of (start, end) tuples in seconds
        output_base_dir: Base directory for output clips
        
    Returns:
        List of created clip paths
    """
    input_path = Path(input_video)
    if not input_path.exists():
        logger.error(f"Input video not found: {input_video}")
        return []
    
    video_name = input_path.stem
    video_ext = input_path.suffix
    
    # Create output directory: all_video_frames/videoname/
    output_dir = Path(output_base_dir) / video_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\nProcessing: {video_name}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Creating {len(time_ranges)} clip(s)...")
    
    created_clips = []
    for idx, (start_sec, end_sec) in enumerate(time_ranges, 1):
        clip_name = f"{video_name}_clip{idx:02d}{video_ext}"
        clip_path = output_dir / clip_name
        
        success = trim_video_clip(str(input_path), str(clip_path), start_sec, end_sec)
        if success:
            created_clips.append(str(clip_path))
    
    logger.info(f"✓ Created {len(created_clips)}/{len(time_ranges)} clips successfully")
    return created_clips


def load_config(config_path: str) -> dict:
    """Load trim configuration from YAML file.
    
    Expected format:
    ```yaml
    output_dir: "all_video_frames"
    videos:
      - input: "source_videos/courtMumbai_vid12.mp4"
        ranges:
          - "0:00-15:00"
          - "25:00-35:00"
          - "45:00-55:00"
      - input: "source_videos/courtDelhi_vid07.mp4"
        ranges:
          - "2:00-18:00"
          - "30:00-42:00"
    ```
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Trim basketball videos to extract match sections (remove breaks)"
    )
    
    parser.add_argument(
        '--input', '-i',
        help='Input video file path'
    )
    
    parser.add_argument(
        '--ranges', '-r',
        nargs='+',
        help='Time ranges to extract (e.g., "0:00-15:00" "25:00-35:00")'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='YAML config file with video trim specifications'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='data/all_video_frames',
        help='Output base directory (default: data/all_video_frames)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.config and not (args.input and args.ranges):
        parser.error("Either --config or both --input and --ranges must be provided")
    
    if args.config and (args.input or args.ranges):
        parser.error("Cannot use --config with --input/--ranges (choose one mode)")
    
    logger.info("="*60)
    logger.info("Basketball Video Trimming Tool")
    logger.info("="*60)
    
    all_clips = []
    
    if args.config:
        # Config file mode
        logger.info(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        
        output_base = config.get('output_dir', args.output)
        videos = config.get('videos', [])
        
        for video_spec in videos:
            input_video = video_spec.get('input')
            range_strs = video_spec.get('ranges', [])
            
            if not input_video or not range_strs:
                logger.warning(f"Skipping incomplete video spec: {video_spec}")
                continue
            
            try:
                time_ranges = [parse_range(r) for r in range_strs]
                clips = process_video(input_video, time_ranges, output_base)
                all_clips.extend(clips)
            except Exception as e:
                logger.error(f"Error processing {input_video}: {e}")
    
    else:
        # Command-line mode
        try:
            time_ranges = [parse_range(r) for r in args.ranges]
            clips = process_video(args.input, time_ranges, args.output)
            all_clips.extend(clips)
        except Exception as e:
            logger.error(f"Error: {e}")
            return 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info(f"TRIMMING COMPLETE")
    logger.info("="*60)
    logger.info(f"Total clips created: {len(all_clips)}")
    logger.info(f"Output directory: {args.output if not args.config else config.get('output_dir', args.output)}")
    logger.info("="*60)
    logger.info("\nNext step: Run frame extraction on the clips")
    logger.info(f"  python main.py --video-dir {args.output if not args.config else config.get('output_dir', args.output)}")
    logger.info("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
