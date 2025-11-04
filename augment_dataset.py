"""
Data Augmentation Runner
Applies augmentations to the annotated dataset
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from augmentation import DataAugmentor
from utils import load_config, setup_logging

def main():
    """Run data augmentation on the annotated dataset"""
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Setup logging
    setup_logging(config)
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("BASKETBALL DATASET AUGMENTATION - PHASE 3")
    logger.info("="*60)
    
    # Define paths
    # Annotate directly on extracted frames now that quality filtering is removed
    input_dir = "data/extracted_frames"
    output_dir = "data/augmented"
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        logger.error("Please ensure your annotated dataset is in data/extracted_frames")
        return
    
    logger.info(f"\nInput directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Initialize augmentor
    augmentor = DataAugmentor(config)
    
    # Run augmentation
    logger.info("\nStarting augmentation...")
    stats = augmentor.augment_dataset(
        input_dir=input_dir,
        output_dir=output_dir
    )
    
    if stats.get('success'):
        logger.info("\nAugmentation completed successfully!")
        logger.info(f"Original images: {stats['original_count']}")
        logger.info(f"Augmented images: {stats['augmented_count']}")
        logger.info(f"Total dataset size: {stats['total_count']}")
        logger.info(f"\nAugmented dataset saved to: {stats['output_dir']}")
    else:
        logger.error(f"\nAugmentation failed: {stats.get('reason', 'unknown error')}")
    
    logger.info("\n" + "="*60)
    logger.info("AUGMENTATION COMPLETE")
    logger.info("="*60 + "\n")

if __name__ == "__main__":
    main()
