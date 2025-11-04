"""
Frame Extractor Module
Extracts frames from basketball videos with adaptive sampling based on dataset size
"""

'''
    Script running command : 
    For example: python trim_videos.py --input "source_videos/bnsw_vs_ripcity.mp4" --ranges "0:00-10:00" "15:00-25:00" "30:00-40:00"
'''

import cv2
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FrameExtractor:
    """
    Extracts frames from videos with adaptive sampling strategy
    """
    
    def __init__(self, config: Dict):
        """
        Initialize FrameExtractor with configuration
        
        Args:
            config: Configuration dictionary containing frame extraction settings
        """
        self.config = config
        self.frame_config = config.get('frame_extraction', {})
        self.output_config = config.get('output', {})
        
        self.small_threshold = self.frame_config.get('small_dataset_threshold', 10)
        self.small_interval = self.frame_config.get('small_dataset_interval', 3)
        self.large_interval = self.frame_config.get('large_dataset_interval', 7)
        self.max_frames = self.frame_config.get('max_frames_per_video', None)
        
        logger.info(f"FrameExtractor initialized with small_interval={self.small_interval}, "
                   f"large_interval={self.large_interval}")
    
    def determine_frame_interval(self, num_videos: int) -> int:
        """
        Always extract every 30th frame, regardless of dataset size or config.
        """
        interval = 30
        logger.info(f"Frame extraction interval forced to: {interval}")
        return interval
    
    def extract_frames_from_video(
        self, 
        video_path: str, 
        output_dir: str, 
        frame_interval: int,
        video_name: str = None
    ) -> Dict:
        """
        Extract frames from a single video
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save extracted frames
            frame_interval: Extract every Nth frame
            video_name: Optional custom name for the video
            
        Returns:
            Dictionary with extraction statistics
        """
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return {'success': False, 'error': 'Video file not found'}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return {'success': False, 'error': 'Failed to open video'}
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Processing video: {video_path}")
        logger.info(f"FPS: {fps}, Total frames: {total_frames}, Duration: {duration:.2f}s")
        
        # Extract frames
        frame_count = 0
        saved_count = 0
        metadata = []
        
        if video_name is None:
            video_name = Path(video_path).stem
        
        frame_format = self.output_config.get('frame_format', 'jpg')
        frame_quality = self.output_config.get('frame_quality', 95)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract every Nth frame
            if frame_count % frame_interval == 0:
                # Check max frames limit
                if self.max_frames and saved_count >= self.max_frames:
                    logger.info(f"Reached max frames limit: {self.max_frames}")
                    break
                
                # Generate frame filename
                timestamp = frame_count / fps if fps > 0 else 0
                frame_filename = f"{video_name}_skipped_30_frame_{saved_count:06d}.{frame_format}"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # Save frame
                if frame_format.lower() in ['jpg', 'jpeg']:
                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, frame_quality])
                else:
                    cv2.imwrite(frame_path, frame)
                
                # Store metadata
                metadata.append({
                    'frame_number': frame_count,
                    'saved_index': saved_count,
                    'timestamp': timestamp,
                    'filename': frame_filename,
                    'path': frame_path
                })
                
                saved_count += 1
                
                if saved_count % 100 == 0:
                    logger.info(f"Extracted {saved_count} frames...")
            
            frame_count += 1
        
        cap.release()
        
        logger.info(f"Extraction complete: {saved_count} frames saved from {total_frames} total frames")
        
        return {
            'success': True,
            'video_path': video_path,
            'video_name': video_name,
            'total_frames': total_frames,
            'frames_extracted': saved_count,
            'fps': fps,
            'duration': duration,
            'frame_interval': frame_interval,
            'output_dir': output_dir,
            'metadata': metadata
        }
    
    def extract_frames_from_videos(
        self, 
        video_dir: str, 
        output_base_dir: str,
        recursive: bool = True
    ) -> List[Dict]:
        """
        Extract frames from all videos in a directory (supports recursive search for clips)
        
        Args:
            video_dir: Directory containing video files (or subdirectories with clips)
            output_base_dir: Base directory for output frames
            recursive: If True, search subdirectories for clips (default: True)
            
        Returns:
            List of extraction results for each video
        """
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        found_files = []
        
        video_dir_path = Path(video_dir)
        
        if recursive:
            # Search recursively (for all_video_frames structure with subdirectories)
            for ext in video_extensions:
                found_files.extend(video_dir_path.glob(f'**/*{ext}'))
                found_files.extend(video_dir_path.glob(f'**/*{ext.upper()}'))
        else:
            # Search only top level (old behavior)
            for ext in video_extensions:
                found_files.extend(video_dir_path.glob(f'*{ext}'))
                found_files.extend(video_dir_path.glob(f'*{ext.upper()}'))

        # Deduplicate by resolved absolute path
        unique_map = {}
        for f in found_files:
            try:
                key = str(f.resolve())
            except Exception:
                key = str(f)
            unique_map[key] = f
        video_files = sorted(unique_map.values(), key=lambda p: p.name.lower())

        if not video_files:
            logger.warning(f"No video files found in: {video_dir}")
            return []
        
        logger.info(f"Found {len(video_files)} unique video(s)")
        
        # Determine frame interval (always 25 now)
        frame_interval = self.determine_frame_interval(len(video_files))
        
        # Process each video
        results = []
        organize_by_video = self.output_config.get('organize_by_video', True)
        
        for idx, video_path in enumerate(video_files, 1):
            video_name = video_path.stem
            logger.info(f"\n[{idx}/{len(video_files)}] Processing: {video_name}")
            
            # Create output directory with new naming: clipname__skip25/
            if organize_by_video:
                output_dir = os.path.join(output_base_dir, f"{video_name}__skip{frame_interval}")
            else:
                output_dir = output_base_dir
            
            # Extract frames
            result = self.extract_frames_from_video(
                str(video_path), 
                output_dir, 
                frame_interval,
                video_name
            )
            results.append(result)
        
        # Summary
        total_extracted = sum(r.get('frames_extracted', 0) for r in results if r.get('success'))
        logger.info(f"\n{'='*50}")
        logger.info(f"EXTRACTION SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total videos processed: {len(video_files)}")
        logger.info(f"Total frames extracted: {total_extracted}")
        logger.info(f"Frame interval used: {frame_interval}")
        logger.info(f"{'='*50}\n")
        
        return results
