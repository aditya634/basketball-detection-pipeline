"""
Basketball Dataset Creation Pipeline - Main Script
Phase 1: Extract frames from basketball videos

Usage:
    python main.py --config config/config.yaml
    python main.py --config config/config.yaml --skip-extraction
    
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.frame_extractor import FrameExtractor
from src.utils import (
    load_config, 
    setup_logging, 
    save_metadata,
    print_pipeline_header,
    print_pipeline_summary,
    validate_directories,
    get_timestamp
)

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Basketball Dataset Creation Pipeline - Phase 1'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--video-dir',
        type=str,
        default=None,
        help='Override video/clips directory from config (use all_video_frames for clips)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Search for videos recursively in subdirectories (default: True for clips structure)'
    )
    
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Skip frame extraction step'
    )
    
    # Quality filtering removed from pipeline
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Override output directory'
    )
    
    return parser.parse_args()


def run_frame_extraction(config, video_dir, output_dir, recursive=True):
    """
    Run frame extraction step
    
    Args:
        config: Configuration dictionary
        video_dir: Directory containing videos (or clips in subdirectories)
        output_dir: Directory to save extracted frames
        recursive: Search recursively for clips in subdirectories
        
    Returns:
        Extraction results
    """
    logger.info("="*60)
    logger.info("STEP 1: FRAME EXTRACTION")
    logger.info("="*60)
    
    extractor = FrameExtractor(config)
    results = extractor.extract_frames_from_videos(video_dir, output_dir, recursive=recursive)
    
    return results


# Quality filtering step has been removed from the pipeline


def main():
    """Main pipeline execution"""
    
    # Parse arguments
    args = parse_arguments()
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"ERROR: Configuration file not found: {args.config}")
        print("Please create a config file or specify a valid path with --config")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    
    print_pipeline_header("Basketball Dataset Creation Pipeline - Phase 1")
    logger.info(f"Configuration loaded from: {args.config}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    # New hierarchy: source_videos -> all_video_frames (clips) -> extracted_frames
    source_videos_dir = os.path.join(data_dir, 'source_videos')
    all_clips_dir = os.path.join(data_dir, 'all_video_frames')
    
    # Default: extract from all_video_frames (trimmed clips)
    # Use --video-dir to override (e.g., for source_videos or custom path)
    video_dir = args.video_dir or all_clips_dir
    extracted_dir = os.path.join(data_dir, 'extracted_frames')
    # quality_frames concept removed; use extracted_frames directly for annotation
    
    if args.output_dir:
        extracted_dir = os.path.join(args.output_dir, 'extracted_frames')
    
    logger.info(f"Source videos directory: {source_videos_dir}")
    logger.info(f"Clips directory: {all_clips_dir}")
    logger.info(f"Processing videos from: {video_dir}")
    logger.info(f"Extracted frames directory: {extracted_dir}")
    logger.info(f"Recursive search: {args.recursive}")
    
    # Validate video directory exists
    if not os.path.exists(video_dir):
        logger.error(f"Video directory not found: {video_dir}")
        logger.info("Pipeline hierarchy:")
        logger.info("  1. source_videos/     - Raw uploaded videos")
        logger.info("  2. all_video_frames/  - Trimmed clips (created by trim_videos.py)")
        logger.info("  3. extracted_frames/  - Frames from clips (created by this script)")
        logger.info("\nRun trim_videos.py first to create clips from source videos")
        sys.exit(1)
    
    # Check if videos exist
    from src.utils import get_video_files
    video_files = get_video_files(video_dir, recursive=args.recursive)
    
    if not video_files and not args.skip_extraction:
        logger.warning(f"No video files found in: {video_dir}")
        logger.info("Please add video files to continue")
        sys.exit(1)
    
    # Create output directories
    os.makedirs(extracted_dir, exist_ok=True)
    # no quality frames directory to create
    
    # Pipeline execution
    pipeline_results = {
        'start_time': get_timestamp(),
        'config_file': args.config,
        'video_directory': video_dir,
    'extracted_directory': extracted_dir
    }
    
    try:
        # Step 1: Frame Extraction
        if not args.skip_extraction:
            extraction_results = run_frame_extraction(config, video_dir, extracted_dir, recursive=args.recursive)
            pipeline_results['extraction_results'] = extraction_results
            
            # Calculate stats
            total_videos = len(extraction_results)
            total_frames = sum(r.get('frames_extracted', 0) for r in extraction_results if r.get('success'))
            
            logger.info(f"Frame extraction complete: {total_frames} frames from {total_videos} video(s)")
        else:
            logger.info("Skipping frame extraction (--skip-extraction flag set)")
        
        # Step 2 removed
        
        # Save pipeline metadata
        pipeline_results['end_time'] = get_timestamp()
        pipeline_results['status'] = 'completed'
        
        metadata_path = os.path.join(data_dir, f'pipeline_metadata_{get_timestamp()}.json')
        save_metadata(pipeline_results, metadata_path)
        
        # Print summary
        print("\n" + "="*60)
        print("  PIPELINE COMPLETED SUCCESSFULLY! ✓")
        print("="*60)
        print(f"\n  📁 Frames ready at: {extracted_dir}")
        print(f"  📝 Metadata saved to: {metadata_path}")
        print("\n" + "="*60)
        print("\n  NEXT STEPS:")
        print(f"  1. Review frames in: {extracted_dir}/")
        print("  2. Run ball detection to separate frames:")
        print(f"     python seperation/separate_images_by_ball.py --input <folder> --batch-size 32")
        print("  3. Annotate frames with YOLO format")
        print("  4. Run Phase 2: Data Augmentation & Splitting")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        pipeline_results['status'] = 'failed'
        pipeline_results['error'] = str(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
