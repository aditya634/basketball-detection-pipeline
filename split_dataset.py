"""
Split Runner - Phase 4 (Option B: by-video split)
Builds YOLO-ready dataset structure from augmented data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils import load_config, setup_logging
from dataset_splitter import DatasetSplitter
import logging

def main():
    config = load_config('config/config.yaml')
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info('='*60)
    logger.info('PHASE 4: DATASET SPLIT (Option B - by video)')
    logger.info('='*60)

    splitter = DatasetSplitter(config)
    result = splitter.split()

    if result.get('success'):
        logger.info('\nSplit completed successfully!')
        logger.info(f"Train images: {result['train_images']}")
        logger.info(f"Val images:   {result['val_images']}")
        logger.info(f"Test images:  {result['test_images']}")
        logger.info(f"Output dir:   {result['output_dir']}")
        logger.info('\nYOLO data.yaml is ready. You can start training.')
    else:
        logger.error(f"Split failed: {result.get('reason', 'unknown error')}")

if __name__ == '__main__':
    main()
