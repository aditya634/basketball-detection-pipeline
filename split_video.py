"""
Video Splitter
Splits long basketball match videos into smaller segments for the pipeline
Uses ffmpeg for fast, lossless splitting (no re-encoding)
"""

import os
import subprocess
from pathlib import Path
import argparse
import logging
from typing import Optional
import cv2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoSplitter:
    """
    Splits long videos into smaller segments using ffmpeg (fast, no re-encoding)
    Falls back to OpenCV if ffmpeg is not available
    """
    
    def __init__(self, segment_duration: int = 600, use_ffmpeg: bool = True):
        """
        Initialize VideoSplitter
        
        Args:
            segment_duration: Duration of each segment in seconds (default: 600 = 10 minutes)
            use_ffmpeg: Use ffmpeg for fast splitting (default: True)
        """
        self.segment_duration = segment_duration
        self.use_ffmpeg = use_ffmpeg and self._check_ffmpeg()
        
        if self.use_ffmpeg:
            logger.info(f"VideoSplitter initialized with ffmpeg (FAST mode)")
        else:
            logger.info(f"VideoSplitter initialized with OpenCV (SLOW mode - ffmpeg not found)")
        logger.info(f"Segment duration: {segment_duration}s ({segment_duration/60:.1f} min)")
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _format_time(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format for ffmpeg"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def split_video(
        self, 
        input_video: str, 
        output_dir: str,
        segment_duration: Optional[int] = None
    ) -> list:
        """
        Split a video into segments
        
        Args:
            input_video: Path to input video file
            output_dir: Directory to save split videos
            segment_duration: Override default segment duration (seconds)
            
        Returns:
            List of created segment file paths
        """
        if segment_duration is None:
            segment_duration = self.segment_duration
        
        # Validate input
        if not os.path.exists(input_video):
            logger.error(f"Video not found: {input_video}")
            return []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Use ffmpeg if available, otherwise fall back to OpenCV
        if self.use_ffmpeg:
            return self._split_with_ffmpeg(input_video, output_dir, segment_duration)
        else:
            return self._split_with_opencv(input_video, output_dir, segment_duration)
    
    def _split_with_ffmpeg(
        self,
        input_video: str,
        output_dir: str,
        segment_duration: int
    ) -> list:
        """Split video using ffmpeg (FAST - no re-encoding)"""
        # Get video duration using ffprobe
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 
                 'format=duration', '-of', 
                 'default=noprint_wrappers=1:nokey=1', input_video],
                capture_output=True,
                text=True,
                timeout=30
            )
            duration = float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            return []
        
        video_name = Path(input_video).stem
        num_segments = int(duration / segment_duration) + (1 if duration % segment_duration > 0 else 0)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing video: {Path(input_video).name}")
        logger.info(f"{'='*60}")
        logger.info(f"Duration: {duration/60:.1f} minutes ({duration:.1f}s)")
        logger.info(f"Segment duration: {segment_duration}s ({segment_duration/60:.1f} min)")
        logger.info(f"Estimated segments: {num_segments}")
        logger.info(f"Method: ffmpeg (FAST - no re-encoding)")
        logger.info(f"{'='*60}\n")
        
        segment_paths = []
        
        # Split using ffmpeg
        for i in range(num_segments):
            start_time = i * segment_duration
            segment_num = i + 1
            
            # Create segment filename
            segment_filename = f"{video_name}_segment_{segment_num:03d}.mp4"
            segment_path = os.path.join(output_dir, segment_filename)
            
            logger.info(f"Creating segment {segment_num}/{num_segments}: {segment_filename}")
            logger.info(f"  Time range: {self._format_time(start_time)} - {self._format_time(start_time + segment_duration)}")
            
            # ffmpeg command: -c copy for no re-encoding (super fast!)
            cmd = [
                'ffmpeg',
                '-i', input_video,
                '-ss', self._format_time(start_time),
                '-t', str(segment_duration),
                '-c', 'copy',  # Copy codec (no re-encoding)
                '-avoid_negative_ts', 'make_zero',
                '-y',  # Overwrite output file
                segment_path
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0 and os.path.exists(segment_path):
                    size_mb = os.path.getsize(segment_path) / (1024 * 1024)
                    logger.info(f"  ✓ Created ({size_mb:.1f} MB)")
                    segment_paths.append(segment_path)
                else:
                    logger.error(f"  ✗ Failed to create segment")
                    logger.error(f"  {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"  ✗ Timeout while creating segment")
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"SPLITTING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total segments created: {len(segment_paths)}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Segments:")
        for i, path in enumerate(segment_paths, 1):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"  {i}. {Path(path).name} ({size_mb:.1f} MB)")
        logger.info(f"{'='*60}\n")
        
        return segment_paths
    
    def _split_with_opencv(
        self,
        input_video: str,
        output_dir: str,
        segment_duration: int
    ) -> list:
        """Split video using OpenCV (SLOW - frame by frame re-encoding)"""
        
        # Open video
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {input_video}")
            return []
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing video: {Path(input_video).name}")
        logger.info(f"{'='*60}")
        logger.info(f"Duration: {duration/60:.1f} minutes ({duration:.1f}s)")
        logger.info(f"FPS: {fps}")
        logger.info(f"Total frames: {total_frames:,}")
        logger.info(f"Resolution: {width}x{height}")
        logger.info(f"Segment duration: {segment_duration}s ({segment_duration/60:.1f} min)")
        logger.info(f"Method: OpenCV (SLOW - frame by frame)")
        logger.info(f"WARNING: This will be slow! Install ffmpeg for 10-100x speed boost")
        
        # Calculate segments
        frames_per_segment = int(fps * segment_duration)
        estimated_segments = int(total_frames / frames_per_segment) + 1
        logger.info(f"Estimated segments: {estimated_segments}")
        logger.info(f"{'='*60}\n")
        
        # Get video codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Split video
        segment_paths = []
        segment_num = 1
        frame_count = 0
        current_segment_frames = 0
        
        video_name = Path(input_video).stem
        writer = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Start new segment
            if current_segment_frames == 0:
                if writer is not None:
                    writer.release()
                
                # Create segment filename
                segment_filename = f"{video_name}_segment_{segment_num:03d}.mp4"
                segment_path = os.path.join(output_dir, segment_filename)
                
                # Create video writer
                writer = cv2.VideoWriter(segment_path, fourcc, fps, (width, height))
                
                logger.info(f"Creating segment {segment_num}: {segment_filename}")
                segment_paths.append(segment_path)
            
            # Write frame
            writer.write(frame)
            current_segment_frames += 1
            frame_count += 1
            
            # Check if segment is complete
            if current_segment_frames >= frames_per_segment:
                current_segment_frames = 0
                segment_num += 1
            
            # Progress update
            if frame_count % 1000 == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"Progress: {progress:.1f}% ({frame_count:,}/{total_frames:,} frames)")
        
        # Release resources
        if writer is not None:
            writer.release()
        cap.release()
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"SPLITTING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total segments created: {len(segment_paths)}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Segments:")
        for i, path in enumerate(segment_paths, 1):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"  {i}. {Path(path).name} ({size_mb:.1f} MB)")
        logger.info(f"{'='*60}\n")
        
        return segment_paths
    
    def split_multiple_videos(
        self,
        input_dir: str,
        output_dir: str,
        segment_duration: Optional[int] = None
    ) -> dict:
        """
        Split multiple videos in a directory
        
        Args:
            input_dir: Directory containing videos to split
            output_dir: Base directory for output segments
            segment_duration: Override default segment duration (seconds)
            
        Returns:
            Dictionary mapping input video to list of segment paths
        """
        # Find video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(Path(input_dir).glob(f'*{ext}'))
            video_files.extend(Path(input_dir).glob(f'*{ext.upper()}'))
        
        # Deduplicate
        unique_map = {}
        for f in video_files:
            try:
                key = str(f.resolve())
            except Exception:
                key = str(f)
            unique_map[key] = f
        video_files = sorted(unique_map.values(), key=lambda p: p.name.lower())
        
        if not video_files:
            logger.warning(f"No video files found in: {input_dir}")
            return {}
        
        logger.info(f"Found {len(video_files)} video(s) to split\n")
        
        # Process each video
        results = {}
        for idx, video_path in enumerate(video_files, 1):
            logger.info(f"\n[{idx}/{len(video_files)}] Processing: {video_path.name}")
            
            # Create output subdirectory for this video
            video_output_dir = os.path.join(output_dir, video_path.stem + "_segments")
            
            # Split video
            segments = self.split_video(
                str(video_path),
                video_output_dir,
                segment_duration
            )
            results[str(video_path)] = segments
        
        # Final summary
        total_segments = sum(len(segs) for segs in results.values())
        logger.info(f"\n{'='*60}")
        logger.info(f"ALL VIDEOS PROCESSED")
        logger.info(f"{'='*60}")
        logger.info(f"Videos processed: {len(video_files)}")
        logger.info(f"Total segments created: {total_segments}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"{'='*60}\n")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Split long basketball match videos into smaller segments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split single video into 10-minute segments (default)
  python split_video.py --input game.mp4 --output data/raw_videos

  # Split into 5-minute segments
  python split_video.py --input game.mp4 --output data/raw_videos --duration 300

  # Split all videos in a directory
  python split_video.py --input-dir videos/ --output data/raw_videos

  # Split into 15-minute segments
  python split_video.py --input game.mp4 --output data/raw_videos --duration 900
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', type=str, help='Input video file')
    input_group.add_argument('--input-dir', type=str, help='Directory containing videos')
    
    # Output options
    parser.add_argument('--output', type=str, default='data/raw_videos',
                       help='Output directory (default: data/raw_videos)')
    
    # Segment duration
    parser.add_argument('--duration', type=int, default=600,
                       help='Segment duration in seconds (default: 600 = 10 minutes)')
    
    args = parser.parse_args()
    
    # Create splitter
    splitter = VideoSplitter(segment_duration=args.duration)
    
    # Process videos
    if args.input:
        # Single video
        splitter.split_video(args.input, args.output)
    else:
        # Multiple videos
        splitter.split_multiple_videos(args.input_dir, args.output)
    
    logger.info("✅ Done! Segments are ready to use in the pipeline.")
    logger.info(f"Next step: python main.py")


if __name__ == "__main__":
    main()
