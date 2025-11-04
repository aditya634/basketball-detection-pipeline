"""
Data Augmentation Module
Applies basketball-specific augmentations while preserving YOLO annotations
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import random

logger = logging.getLogger(__name__)


class DataAugmentor:
    """
    Applies data augmentation to images and their YOLO annotations
    """
    
    def __init__(self, config: Dict):
        """
        Initialize DataAugmentor with configuration
        
        Args:
            config: Configuration dictionary containing augmentation settings
        """
        self.config = config
        self.aug_config = config.get('augmentation', {})
        self.output_config = config.get('output', {})
        
        self.enabled = self.aug_config.get('enabled', True)
        self.aug_per_image = self.aug_config.get('augmentations_per_image', 3)
        
        # Augmentation probabilities
        self.brightness_prob = self.aug_config.get('brightness_probability', 0.7)
        self.contrast_prob = self.aug_config.get('contrast_probability', 0.5)
        self.flip_prob = self.aug_config.get('flip_probability', 0.5)
        self.rotation_prob = self.aug_config.get('rotation_probability', 0.3)
        self.zoom_prob = self.aug_config.get('zoom_probability', 0.3)
        self.noise_prob = self.aug_config.get('noise_probability', 0.2)
        
        # Augmentation parameters
        self.brightness_range = self.aug_config.get('brightness_range', [-30, 30])
        self.contrast_range = self.aug_config.get('contrast_range', [0.8, 1.2])
        self.rotation_range = self.aug_config.get('rotation_range', [-10, 10])
        self.zoom_range = self.aug_config.get('zoom_range', [0.9, 1.1])
        self.noise_std = self.aug_config.get('noise_std', 10)
        
        logger.info(f"DataAugmentor initialized (enabled={self.enabled}, "
                   f"augmentations_per_image={self.aug_per_image})")
    
    def adjust_brightness(self, image: np.ndarray, delta: int) -> np.ndarray:
        """
        Adjust image brightness
        
        Args:
            image: Input image
            delta: Brightness adjustment (-255 to 255)
            
        Returns:
            Brightness-adjusted image
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + delta, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def adjust_contrast(self, image: np.ndarray, factor: float) -> np.ndarray:
        """
        Adjust image contrast
        
        Args:
            image: Input image
            factor: Contrast factor (0.5 = less contrast, 1.5 = more contrast)
            
        Returns:
            Contrast-adjusted image
        """
        mean = np.mean(image)
        return np.clip((image - mean) * factor + mean, 0, 255).astype(np.uint8)
    
    def horizontal_flip(self, image: np.ndarray, bboxes: List[List[float]]) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Flip image and adjust YOLO bounding boxes
        
        Args:
            image: Input image
            bboxes: YOLO format bboxes [[class, x_center, y_center, width, height], ...]
            
        Returns:
            Flipped image and adjusted bboxes
        """
        flipped = cv2.flip(image, 1)
        
        # Adjust YOLO bboxes (flip x_center)
        flipped_bboxes = []
        for bbox in bboxes:
            cls, x_center, y_center, width, height = bbox
            new_x = 1.0 - x_center  # Flip x coordinate
            flipped_bboxes.append([cls, new_x, y_center, width, height])
        
        return flipped, flipped_bboxes
    
    def rotate_image(self, image: np.ndarray, angle: float, bboxes: List[List[float]]) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Rotate image and adjust YOLO bounding boxes
        
        Args:
            image: Input image
            angle: Rotation angle in degrees (-10 to 10 recommended for basketball)
            bboxes: YOLO format bboxes
            
        Returns:
            Rotated image and adjusted bboxes
        """
        h, w = image.shape[:2]
        center = (w / 2, h / 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate image
        rotated = cv2.warpAffine(image, M, (w, h), 
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(0, 0, 0))
        
        # Adjust bboxes (approximate - for small angles, bboxes stay roughly valid)
        # For small rotations (<15 degrees), we keep bboxes as-is
        # For production, you'd want to rotate the corners and recalculate
        rotated_bboxes = bboxes.copy()
        
        return rotated, rotated_bboxes
    
    def zoom_image(self, image: np.ndarray, zoom_factor: float, bboxes: List[List[float]]) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Zoom image (crop and resize) and adjust bboxes
        
        Args:
            image: Input image
            zoom_factor: Zoom factor (>1 = zoom in, <1 = zoom out)
            bboxes: YOLO format bboxes
            
        Returns:
            Zoomed image and adjusted bboxes
        """
        h, w = image.shape[:2]
        
        if zoom_factor > 1.0:
            # Zoom in (crop center and resize)
            new_h, new_w = int(h / zoom_factor), int(w / zoom_factor)
            top = (h - new_h) // 2
            left = (w - new_w) // 2
            
            cropped = image[top:top+new_h, left:left+new_w]
            zoomed = cv2.resize(cropped, (w, h))
            
            # Adjust bboxes
            zoomed_bboxes = []
            for bbox in bboxes:
                cls, x_center, y_center, width, height = bbox
                
                # Convert to pixel coordinates
                x_pix = x_center * w
                y_pix = y_center * h
                w_pix = width * w
                h_pix = height * h
                
                # Adjust for crop
                new_x = (x_pix - left) * zoom_factor
                new_y = (y_pix - top) * zoom_factor
                new_w = w_pix * zoom_factor
                new_h = h_pix * zoom_factor
                
                # Convert back to YOLO format
                if 0 <= new_x <= w and 0 <= new_y <= h:  # Keep only visible bboxes
                    zoomed_bboxes.append([
                        cls,
                        new_x / w,
                        new_y / h,
                        new_w / w,
                        new_h / h
                    ])
        else:
            # Zoom out (add padding)
            zoomed = image.copy()
            zoomed_bboxes = bboxes.copy()
        
        return zoomed, zoomed_bboxes
    
    def add_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Add Gaussian noise to image
        
        Args:
            image: Input image
            
        Returns:
            Noisy image
        """
        noise = np.random.normal(0, self.noise_std, image.shape).astype(np.float32)
        noisy = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return noisy
    
    def apply_augmentations(
        self, 
        image: np.ndarray, 
        bboxes: List[List[float]],
        augmentation_id: int = 0
    ) -> Tuple[np.ndarray, List[List[float]], str]:
        """
        Apply random augmentations to image and bboxes
        
        Args:
            image: Input image
            bboxes: YOLO format bboxes
            augmentation_id: ID for this augmentation variant
            
        Returns:
            Augmented image, adjusted bboxes, and augmentation description
        """
        aug_image = image.copy()
        aug_bboxes = bboxes.copy()
        aug_desc = []
        
        # Brightness adjustment
        if random.random() < self.brightness_prob:
            delta = random.randint(self.brightness_range[0], self.brightness_range[1])
            aug_image = self.adjust_brightness(aug_image, delta)
            aug_desc.append(f"bright{delta:+d}")
        
        # Contrast adjustment
        if random.random() < self.contrast_prob:
            factor = random.uniform(self.contrast_range[0], self.contrast_range[1])
            aug_image = self.adjust_contrast(aug_image, factor)
            aug_desc.append(f"contrast{factor:.2f}")
        
        # Horizontal flip (basketball: OK to flip horizontally, NOT vertically)
        if random.random() < self.flip_prob:
            aug_image, aug_bboxes = self.horizontal_flip(aug_image, aug_bboxes)
            aug_desc.append("hflip")
        
        # Rotation (small angles only for basketball)
        if random.random() < self.rotation_prob:
            angle = random.uniform(self.rotation_range[0], self.rotation_range[1])
            aug_image, aug_bboxes = self.rotate_image(aug_image, angle, aug_bboxes)
            aug_desc.append(f"rot{angle:.1f}")
        
        # Zoom
        if random.random() < self.zoom_prob:
            zoom_factor = random.uniform(self.zoom_range[0], self.zoom_range[1])
            aug_image, aug_bboxes = self.zoom_image(aug_image, zoom_factor, aug_bboxes)
            aug_desc.append(f"zoom{zoom_factor:.2f}")
        
        # Noise
        if random.random() < self.noise_prob:
            aug_image = self.add_noise(aug_image)
            aug_desc.append("noise")
        
        aug_name = f"aug{augmentation_id}_" + "_".join(aug_desc) if aug_desc else f"aug{augmentation_id}"
        
        return aug_image, aug_bboxes, aug_name
    
    def parse_yolo_annotation(self, annotation_path: str) -> List[List[float]]:
        """
        Parse YOLO annotation file
        
        Args:
            annotation_path: Path to .txt annotation file
            
        Returns:
            List of bboxes [[class, x_center, y_center, width, height], ...]
        """
        if not os.path.exists(annotation_path):
            return []
        
        bboxes = []
        with open(annotation_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                    bboxes.append([cls, x, y, w, h])
        
        return bboxes
    
    def save_yolo_annotation(self, annotation_path: str, bboxes: List[List[float]]) -> None:
        """
        Save YOLO annotation file
        
        Args:
            annotation_path: Path to save .txt annotation
            bboxes: List of bboxes
        """
        os.makedirs(os.path.dirname(annotation_path), exist_ok=True)
        
        with open(annotation_path, 'w') as f:
            for bbox in bboxes:
                cls, x, y, w, h = bbox
                f.write(f"{int(cls)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    
    def augment_dataset(
        self, 
        input_dir: str, 
        output_dir: str,
        labels_dir: Optional[str] = None
    ) -> Dict:
        """
        Augment entire dataset
        
        Args:
            input_dir: Directory with images (and labels if labels_dir is None)
            output_dir: Directory to save augmented images
            labels_dir: Optional separate directory for labels
            
        Returns:
            Augmentation statistics
        """
        if not self.enabled:
            logger.info("Augmentation disabled in config")
            return {'success': False, 'reason': 'disabled'}
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        
        # Find images
        image_extensions = ['.jpg', '.jpeg', '.png']
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(input_dir).glob(f'**/*{ext}'))
        
        if not image_files:
            logger.warning(f"No images found in: {input_dir}")
            return {'success': False, 'reason': 'no_images'}
        
        logger.info(f"Augmenting {len(image_files)} images with {self.aug_per_image} variants each")
        logger.info(f"Preserving folder structure from {input_dir}")
        
        total_original = 0
        total_augmented = 0
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        for img_path in image_files:
            # Read image
            image = cv2.imread(str(img_path))
            if image is None:
                logger.warning(f"Failed to read: {img_path}")
                continue
            
            # Calculate relative path to preserve folder structure
            try:
                relative_path = img_path.relative_to(input_path)
                relative_folder = relative_path.parent
            except ValueError:
                # Fallback if path is not relative
                relative_folder = Path("")
            
            # Create output subfolder matching input structure
            output_subfolder = output_path / relative_folder
            os.makedirs(output_subfolder, exist_ok=True)
            
            # Find annotation file
            ann_path = img_path.with_suffix('.txt')
            bboxes = self.parse_yolo_annotation(str(ann_path))
            
            # Copy original with same name
            orig_name = img_path.stem
            orig_output_path = output_subfolder / f"{orig_name}.jpg"
            cv2.imwrite(str(orig_output_path), image)
            
            if bboxes:
                orig_ann_path = output_subfolder / f"{orig_name}.txt"
                self.save_yolo_annotation(str(orig_ann_path), bboxes)
            
            total_original += 1
            
            # Generate augmentations in the same subfolder
            for aug_id in range(self.aug_per_image):
                aug_image, aug_bboxes, aug_desc = self.apply_augmentations(
                    image, bboxes, aug_id + 1
                )
                
                # Save augmented image in same subfolder
                aug_name = f"{orig_name}_{aug_desc}"
                aug_output_path = output_subfolder / f"{aug_name}.jpg"
                cv2.imwrite(str(aug_output_path), aug_image)
                
                # Save augmented annotation in same subfolder
                if aug_bboxes:
                    aug_ann_path = output_subfolder / f"{aug_name}.txt"
                    self.save_yolo_annotation(str(aug_ann_path), aug_bboxes)
                
                total_augmented += 1
            
            if (total_original + total_augmented) % 100 == 0:
                logger.info(f"Processed {total_original} images, "
                          f"generated {total_augmented} augmented variants")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"AUGMENTATION SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Original images: {total_original}")
        logger.info(f"Augmented images: {total_augmented}")
        logger.info(f"Total dataset size: {total_original + total_augmented}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"{'='*50}\n")
        
        return {
            'success': True,
            'original_count': total_original,
            'augmented_count': total_augmented,
            'total_count': total_original + total_augmented,
            'output_dir': output_dir
        }
