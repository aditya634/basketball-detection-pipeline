"""
Quality Filter Module
Filters frames based on quality metrics and basketball-specific criteria
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Try to import scikit-image, fall back to custom implementation if not available
SSIM_AVAILABLE = False
try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except (ImportError, ValueError) as e:
    # ValueError can occur with numpy compatibility issues
    import warnings
    warnings.warn(f"scikit-image not available ({e}), using simplified similarity calculation")

logger = logging.getLogger(__name__)


class QualityFilter:
    """
    Filters frames based on image quality and basketball-specific criteria
    """
    
    def __init__(self, config: Dict):
        """
        Initialize QualityFilter with configuration
        
        Args:
            config: Configuration dictionary containing quality filter settings
        """
        self.config = config
        self.filter_config = config.get('quality_filter', {})
        self.output_config = config.get('output', {})
        
        self.enabled = self.filter_config.get('enabled', True)
        self.min_brightness = self.filter_config.get('min_brightness', 30)
        self.max_brightness = self.filter_config.get('max_brightness', 225)
        self.min_sharpness = self.filter_config.get('min_sharpness', 100)
        self.skip_similar = self.filter_config.get('skip_similar_frames', True)
        self.similarity_threshold = self.filter_config.get('similarity_threshold', 0.95)
        self.detect_motion = self.filter_config.get('detect_motion', True)
        self.min_motion_score = self.filter_config.get('min_motion_score', 500)

        # Fast metric mode: compute metrics on a downsized copy for speed
        fm_cfg = self.filter_config.get('fast_metrics', {})
        self.fast_metrics_enabled = fm_cfg.get('enabled', True)
        self.fast_metrics_max_dim = int(fm_cfg.get('max_dim', 640))

        # Previous frames for temporal comparisons
        self.previous_frame = None  # original-resolution frame (if needed later)
        self.previous_metric_frame = None  # downsized frame used for metrics

        logger.info(f"QualityFilter initialized (enabled={self.enabled})")

    def _resize_for_metrics(self, frame: np.ndarray) -> np.ndarray:
        """
        Optionally resize frame for metric computation to speed up filtering.
        Preserves aspect ratio and limits the max dimension to fast_metrics_max_dim.
        """
        if not self.fast_metrics_enabled or frame is None:
            return frame
        h, w = frame.shape[:2]
        max_dim = max(h, w)
        if max_dim <= self.fast_metrics_max_dim or max_dim == 0:
            return frame
        scale = self.fast_metrics_max_dim / float(max_dim)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    def calculate_brightness(self, frame: np.ndarray) -> float:
        """
        Calculate average brightness of a frame
        
        Args:
            frame: Input image frame
            
        Returns:
            Average brightness value (0-255)
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        return np.mean(gray)
    
    def calculate_sharpness(self, frame: np.ndarray) -> float:
        """
        Calculate sharpness (focus) of a frame using Laplacian variance
        Higher values indicate sharper images
        
        Args:
            frame: Input image frame
            
        Returns:
            Sharpness score (higher is better)
        """
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        return variance
    
    def calculate_motion_score(self, frame: np.ndarray, previous_frame: np.ndarray = None) -> float:
        """
        Calculate motion score between current and previous frame
        
        Args:
            frame: Current frame
            previous_frame: Previous frame for comparison
            
        Returns:
            Motion score (higher indicates more motion)
        """
        if previous_frame is None:
            return float('inf')  # Keep first frame
        
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray1 = frame
            
        if len(previous_frame.shape) == 3:
            gray2 = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray2 = previous_frame
        
        # Resize to same size if needed
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        motion_score = np.sum(diff)
        
        return motion_score
    
    def calculate_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Calculate structural similarity between two frames
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        # Convert to grayscale
        if len(frame1.shape) == 3:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        else:
            gray1 = frame1
            
        if len(frame2.shape) == 3:
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        else:
            gray2 = frame2
        
        # Resize to same size if needed
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
        
        # Calculate similarity
        if SSIM_AVAILABLE:
            # Use SSIM if available
            similarity = ssim(gray1, gray2)
        else:
            # Fallback: Use normalized correlation
            # Normalize images
            gray1_norm = gray1.astype(float) / 255.0
            gray2_norm = gray2.astype(float) / 255.0
            
            # Calculate mean squared error
            mse = np.mean((gray1_norm - gray2_norm) ** 2)
            
            # Convert to similarity (0-1, where 1 is identical)
            similarity = 1.0 - min(mse, 1.0)
        
        return similarity
    
    def is_quality_frame(
        self, 
        frame: np.ndarray, 
        frame_path: str = None
    ) -> Tuple[bool, Dict]:
        """
        Check if frame meets quality criteria
        
        Args:
            frame: Input frame to check
            frame_path: Optional path to frame (for logging)
            
        Returns:
            Tuple of (is_quality, metrics_dict)
        """
        if not self.enabled:
            return True, {}
        
        metrics = {}
        
        # Prepare metric frame (possibly downsized for speed)
        metric_frame = self._resize_for_metrics(frame)
        
        # Calculate brightness
        brightness = self.calculate_brightness(metric_frame)
        metrics['brightness'] = brightness
        
        if brightness < self.min_brightness or brightness > self.max_brightness:
            logger.debug(f"Frame rejected: brightness {brightness:.2f} out of range "
                        f"[{self.min_brightness}, {self.max_brightness}]")
            return False, metrics
        
        # Calculate sharpness
        sharpness = self.calculate_sharpness(metric_frame)
        metrics['sharpness'] = sharpness
        
        if sharpness < self.min_sharpness:
            logger.debug(f"Frame rejected: sharpness {sharpness:.2f} below threshold {self.min_sharpness}")
            return False, metrics
        
        # Check motion (if previous frame exists)
        if self.detect_motion and self.previous_metric_frame is not None:
            motion_score = self.calculate_motion_score(metric_frame, self.previous_metric_frame)
            metrics['motion_score'] = motion_score
            
            if motion_score < self.min_motion_score:
                logger.debug(f"Frame rejected: motion score {motion_score:.2f} below threshold {self.min_motion_score}")
                return False, metrics
        
        # Check similarity to previous frame
        if self.skip_similar and self.previous_metric_frame is not None:
            similarity = self.calculate_similarity(metric_frame, self.previous_metric_frame)
            metrics['similarity'] = similarity
            
            if similarity > self.similarity_threshold:
                logger.debug(f"Frame rejected: too similar to previous frame (similarity: {similarity:.3f})")
                return False, metrics
        
        # Stash the metric frame so caller can update previous on accept
        self._last_metric_frame = metric_frame
        return True, metrics
    
    def filter_frames(
        self, 
        input_dir: str, 
        output_dir: str
    ) -> Dict:
        """
        Filter frames from input directory and copy quality frames to output directory
        
        Args:
            input_dir: Directory containing extracted frames
            output_dir: Directory to save quality frames
            
        Returns:
            Dictionary with filtering statistics
        """
        if not os.path.exists(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return {'success': False, 'error': 'Input directory not found'}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(Path(input_dir).glob(f'*{ext}'))
            image_files.extend(Path(input_dir).glob(f'*{ext.upper()}'))
        
        # Sort by filename
        image_files = sorted(image_files)
        
        if not image_files:
            logger.warning(f"No image files found in: {input_dir}")
            return {'success': True, 'total_frames': 0, 'quality_frames': 0}
        
        logger.info(f"Filtering {len(image_files)} frames from: {input_dir}")
        
        # Reset previous frames
        self.previous_frame = None
        self.previous_metric_frame = None
        
        # Filter frames
        quality_count = 0
        rejected_count = 0
        quality_frames_info = []
        
        for idx, frame_path in enumerate(image_files, 1):
            # Read frame
            frame = cv2.imread(str(frame_path))
            
            if frame is None:
                logger.warning(f"Failed to read frame: {frame_path}")
                continue
            
            # Check quality
            is_quality, metrics = self.is_quality_frame(frame, str(frame_path))
            
            if is_quality:
                # Copy to output directory
                output_path = os.path.join(output_dir, frame_path.name)
                cv2.imwrite(output_path, frame)
                
                quality_frames_info.append({
                    'original_path': str(frame_path),
                    'output_path': output_path,
                    'metrics': metrics
                })
                
                quality_count += 1
                
                # Update previous frames (track last accepted frame for similarity/motion)
                self.previous_frame = frame.copy()
                # metric frame prepared in is_quality_frame
                if hasattr(self, '_last_metric_frame') and self._last_metric_frame is not None:
                    self.previous_metric_frame = self._last_metric_frame
                
                if quality_count % 50 == 0:
                    logger.info(f"Processed {idx}/{len(image_files)} frames, "
                              f"{quality_count} quality frames saved")
            else:
                rejected_count += 1
        
        logger.info(f"Filtering complete: {quality_count}/{len(image_files)} frames passed quality check")
        logger.info(f"Rejected: {rejected_count} frames")
        
        return {
            'success': True,
            'input_dir': input_dir,
            'output_dir': output_dir,
            'total_frames': len(image_files),
            'quality_frames': quality_count,
            'rejected_frames': rejected_count,
            'quality_frames_info': quality_frames_info
        }
    
    def filter_frames_batch(
        self, 
        input_base_dir: str, 
        output_base_dir: str
    ) -> List[Dict]:
        """
        Filter frames from multiple video folders
        
        Args:
            input_base_dir: Base directory containing video folders
            output_base_dir: Base directory for output quality frames
            
        Returns:
            List of filtering results for each video folder
        """
        # Find all subdirectories
        subdirs = [d for d in Path(input_base_dir).iterdir() if d.is_dir()]
        
        if not subdirs:
            logger.info("No subdirectories found, processing root directory")
            result = self.filter_frames(input_base_dir, output_base_dir)
            return [result]
        
        logger.info(f"Found {len(subdirs)} video folder(s)")
        
        results = []
        
        for idx, subdir in enumerate(subdirs, 1):
            logger.info(f"\n[{idx}/{len(subdirs)}] Filtering frames from: {subdir.name}")
            
            # Reset previous frame for each video
            self.previous_frame = None
            self.previous_metric_frame = None
            
            # Create corresponding output directory
            output_dir = os.path.join(output_base_dir, subdir.name)
            
            # Filter frames
            result = self.filter_frames(str(subdir), output_dir)
            results.append(result)
        
        # Summary
        total_input = sum(r.get('total_frames', 0) for r in results if r.get('success'))
        total_quality = sum(r.get('quality_frames', 0) for r in results if r.get('success'))
        
        logger.info(f"\n{'='*50}")
        logger.info(f"QUALITY FILTERING SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total frames processed: {total_input}")
        logger.info(f"Quality frames saved: {total_quality}")
        logger.info(f"Quality rate: {(total_quality/total_input*100):.2f}%" if total_input > 0 else "N/A")
        logger.info(f"{'='*50}\n")
        
        return results
