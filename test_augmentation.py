"""
Test Augmentation on Sample Images
Validates augmentation functionality before processing entire dataset
"""

import os
import sys
from pathlib import Path
import cv2
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from augmentation import DataAugmentor
from utils import load_config, setup_logging

def test_augmentation_sample():
    """Test augmentation on a few sample images"""
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Setup logging
    setup_logging(config)
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("TESTING AUGMENTATION ON SAMPLE IMAGES")
    logger.info("="*60)
    
    # Find sample images from extracted_frames
    quality_dir = "data/extracted_frames"
    test_output_dir = "data/augmentation_test"
    
    if not os.path.exists(quality_dir):
        logger.error(f"Frames directory not found: {quality_dir}")
        return
    
    # Find all images
    image_files = list(Path(quality_dir).glob('**/*.jpg'))
    
    if not image_files:
        logger.error(f"No images found in: {quality_dir}")
        return
    
    # Select 2 random samples
    num_samples = min(2, len(image_files))
    sample_images = random.sample(image_files, num_samples)
    
    logger.info(f"\nTesting on {num_samples} sample images:")
    for img in sample_images:
        logger.info(f"  - {img.name}")
    
    # Create test output directory
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Initialize augmentor
    augmentor = DataAugmentor(config)
    
    # Test each sample
    for img_path in sample_images:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {img_path.name}")
        logger.info(f"{'='*50}")
        
        # Read image
        image = cv2.imread(str(img_path))
        if image is None:
            logger.error(f"Failed to read image: {img_path}")
            continue
        
        logger.info(f"Image shape: {image.shape}")
        
        # Check for annotation
        ann_path = img_path.with_suffix('.txt')
        bboxes = augmentor.parse_yolo_annotation(str(ann_path))
        
        logger.info(f"Found {len(bboxes)} bounding boxes")
        if bboxes:
            for i, bbox in enumerate(bboxes):
                cls, x, y, w, h = bbox
                logger.info(f"  Box {i+1}: class={int(cls)}, "
                          f"center=({x:.3f}, {y:.3f}), size=({w:.3f}, {h:.3f})")
        
        # Copy original
        orig_name = img_path.stem
        orig_output = os.path.join(test_output_dir, f"{orig_name}_original.jpg")
        cv2.imwrite(orig_output, image)
        logger.info(f"Saved original: {orig_output}")
        
        # Generate augmentations
        num_augs = config['augmentation'].get('augmentations_per_image', 3)
        logger.info(f"\nGenerating {num_augs} augmented variants...")
        
        for aug_id in range(num_augs):
            aug_image, aug_bboxes, aug_desc = augmentor.apply_augmentations(
                image, bboxes, aug_id + 1
            )
            
            # Save augmented image
            aug_output = os.path.join(test_output_dir, f"{orig_name}_{aug_desc}.jpg")
            cv2.imwrite(aug_output, aug_image)
            
            logger.info(f"\n  Augmentation {aug_id + 1}: {aug_desc}")
            logger.info(f"    Saved: {aug_output}")
            logger.info(f"    Bboxes: {len(aug_bboxes)}")
            
            # Show bbox changes
            if aug_bboxes and bboxes:
                for i, (orig_bbox, aug_bbox) in enumerate(zip(bboxes, aug_bboxes)):
                    orig_cls, orig_x, orig_y, orig_w, orig_h = orig_bbox
                    aug_cls, aug_x, aug_y, aug_w, aug_h = aug_bbox
                    
                    if orig_x != aug_x or orig_y != aug_y:
                        logger.info(f"    Box {i+1} changed: "
                                  f"center ({orig_x:.3f}, {orig_y:.3f}) -> "
                                  f"({aug_x:.3f}, {aug_y:.3f})")
            
            # Save augmented annotation
            if aug_bboxes:
                aug_ann_output = os.path.join(test_output_dir, f"{orig_name}_{aug_desc}.txt")
                augmentor.save_yolo_annotation(aug_ann_output, aug_bboxes)
    
    logger.info(f"\n{'='*60}")
    logger.info("TEST COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"\nTest results saved to: {test_output_dir}")
    logger.info(f"Total images: {len(list(Path(test_output_dir).glob('*.jpg')))}")
    logger.info(f"Total labels: {len(list(Path(test_output_dir).glob('*.txt')))}")
    logger.info("\nPlease review the augmented images to verify:")
    logger.info("  1. Images look realistic for basketball scenes")
    logger.info("  2. Bounding boxes are correctly transformed")
    logger.info("  3. Augmentation variety is appropriate")
    logger.info("\nIf satisfied, run: python augment_dataset.py")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    test_augmentation_sample()
