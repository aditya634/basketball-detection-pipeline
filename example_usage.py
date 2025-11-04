"""
Basketball Dataset Pipeline - Example Usage and Testing
This script demonstrates how to use individual components
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import load_config, setup_logging
from src.frame_extractor import FrameExtractor
from src.quality_filter import QualityFilter


def example_usage():
    """Example of how to use the pipeline components"""
    
    print("="*60)
    print("Basketball Dataset Pipeline - Example Usage")
    print("="*60 + "\n")
    
    # Load configuration
    print("1. Loading configuration...")
    config = load_config('config/config.yaml')
    print(f"   ✓ Config loaded\n")
    
    # Setup logging
    print("2. Setting up logging...")
    setup_logging(config)
    print(f"   ✓ Logging configured\n")
    
    # Initialize components
    print("3. Initializing components...")
    extractor = FrameExtractor(config)
    quality_filter = QualityFilter(config)
    print(f"   ✓ Frame Extractor ready")
    print(f"   ✓ Quality Filter ready\n")
    
    # Show configuration
    print("4. Current Configuration:")
    print(f"   Small dataset interval: {extractor.small_interval} frames")
    print(f"   Large dataset interval: {extractor.large_interval} frames")
    print(f"   Quality filtering: {'Enabled' if quality_filter.enabled else 'Disabled'}")
    print(f"   Min brightness: {quality_filter.min_brightness}")
    print(f"   Min sharpness: {quality_filter.min_sharpness}\n")
    
    print("="*60)
    print("Ready to process videos!")
    print("="*60)
    print("\nTo run the full pipeline:")
    print("  python main.py")
    print("\nOr customize with options:")
    print("  python main.py --video-dir path/to/videos")
    print("  python main.py --skip-extraction")
    print("  python main.py --skip-filtering")
    print("="*60 + "\n")


if __name__ == '__main__':
    example_usage()
