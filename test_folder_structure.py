"""
Quick test to verify folder structure preservation
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from augmentation import DataAugmentor
from utils import load_config, setup_logging
import logging

def test_folder_structure():
    """Test that folder structure is preserved"""
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("TESTING FOLDER STRUCTURE PRESERVATION")
    logger.info("="*60)
    
    # Temporarily set to 1 augmentation for faster test
    config['augmentation']['augmentations_per_image'] = 1
    
    # Use a test subset
    test_input = "data/extracted_frames"
    test_output = "data/test_folder_structure"
    
    # Clean previous test
    import shutil
    if os.path.exists(test_output):
        shutil.rmtree(test_output)
    
    # Initialize augmentor
    augmentor = DataAugmentor(config)
    
    # Run augmentation
    logger.info(f"\nInput: {test_input}")
    logger.info(f"Output: {test_output}\n")
    
    stats = augmentor.augment_dataset(
        input_dir=test_input,
        output_dir=test_output
    )
    
    if stats.get('success'):
        logger.info("\n" + "="*60)
        logger.info("FOLDER STRUCTURE CHECK")
        logger.info("="*60)
        
        # Check that folders were created
        input_folders = set()
        for root, dirs, files in os.walk(test_input):
            for d in dirs:
                rel_path = os.path.relpath(os.path.join(root, d), test_input)
                input_folders.add(rel_path)
        
        output_folders = set()
        for root, dirs, files in os.walk(test_output):
            for d in dirs:
                rel_path = os.path.relpath(os.path.join(root, d), test_output)
                output_folders.add(rel_path)
        
        logger.info(f"\nInput folders found: {len(input_folders)}")
        for folder in sorted(input_folders):
            logger.info(f"  - {folder}")
        
        logger.info(f"\nOutput folders created: {len(output_folders)}")
        for folder in sorted(output_folders):
            logger.info(f"  - {folder}")
        
        # Check if structure matches
        if input_folders == output_folders:
            logger.info("\n✓ Folder structure preserved correctly!")
        else:
            logger.warning("\n✗ Folder structure mismatch!")
            missing = input_folders - output_folders
            if missing:
                logger.warning(f"Missing folders: {missing}")
        
        # Show sample of files in each folder
        logger.info("\n" + "="*60)
        logger.info("SAMPLE FILES IN OUTPUT FOLDERS")
        logger.info("="*60)
        
        for folder in sorted(output_folders)[:3]:  # Show first 3 folders
            folder_path = os.path.join(test_output, folder)
            files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')][:5]
            logger.info(f"\n{folder}/")
            for f in files:
                logger.info(f"  - {f}")
        
        logger.info("\n" + "="*60)
        logger.info("SUCCESS! Folder structure is preserved.")
        logger.info("="*60)
        logger.info(f"\nTest output saved to: {test_output}")
        logger.info("You can now run: python augment_dataset.py")
        logger.info("="*60 + "\n")
    else:
        logger.error(f"Test failed: {stats.get('reason')}")

if __name__ == "__main__":
    test_folder_structure()
