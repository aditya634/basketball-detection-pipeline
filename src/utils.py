"""
Utility Functions
Helper functions for the basketball dataset creation pipeline
"""

import os
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Optional numpy support for JSON serialization
try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False


def setup_logging(config: Dict) -> None:
    """
    Setup logging configuration
    
    Args:
        config: Configuration dictionary containing logging settings
    """
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    save_logs = log_config.get('save_logs', True)
    log_file = log_config.get('log_file', 'pipeline.log')
    
    # Convert string level to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Configure logging
    handlers = [logging.StreamHandler()]
    
    if save_logs:
        handlers.append(logging.FileHandler(log_file, mode='a'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {log_level} level")


def load_config(config_path: str) -> Dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration YAML file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}


def _json_default(o):
    """Default JSON serializer that handles numpy and Path types."""
    if isinstance(o, Path):
        return str(o)
    if _HAS_NUMPY:
        # Handle numpy scalar types
        if isinstance(o, (_np.generic,)):
            try:
                return o.item()
            except Exception:
                return str(o)
    # Fallback: stringify unknown objects
    return str(o)


def save_metadata(data: Dict, output_path: str) -> None:
    """
    Save metadata to JSON file
    
    Args:
        data: Metadata dictionary
        output_path: Path to save JSON file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=_json_default)
        
        logging.getLogger(__name__).info(f"Metadata saved to: {output_path}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error saving metadata: {e}")


def load_metadata(metadata_path: str) -> Dict:
    """
    Load metadata from JSON file
    
    Args:
        metadata_path: Path to metadata JSON file
        
    Returns:
        Metadata dictionary
    """
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading metadata from {metadata_path}: {e}")
        return {}


def count_files(directory: str, extensions: list = None) -> int:
    """
    Count files in a directory with optional extension filter
    
    Args:
        directory: Directory to count files in
        extensions: List of file extensions to filter (e.g., ['.jpg', '.png'])
        
    Returns:
        Number of files
    """
    if not os.path.exists(directory):
        return 0
    
    files = list(Path(directory).iterdir())
    
    if extensions:
        files = [f for f in files if f.suffix.lower() in [ext.lower() for ext in extensions]]
    
    return len(files)


def get_video_files(directory: str, recursive: bool = True) -> list:
    """
    Get all video files from a directory
    
    Args:
        directory: Directory to search for videos
        recursive: If True, search recursively in subdirectories (default: True)
        
    Returns:
        List of video file paths
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    video_files = []
    
    pattern = '**/*' if recursive else '*'
    
    for ext in video_extensions:
        video_files.extend(Path(directory).glob(f'{pattern}{ext}'))
        video_files.extend(Path(directory).glob(f'{pattern}{ext.upper()}'))
    
    return sorted(video_files)


def get_image_files(directory: str) -> list:
    """
    Get all image files from a directory
    
    Args:
        directory: Directory to search for images
        
    Returns:
        List of image file paths
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(Path(directory).glob(f'*{ext}'))
        image_files.extend(Path(directory).glob(f'*{ext.upper()}'))
    
    return sorted(image_files)


def create_directory_structure(base_dir: str, subdirs: list) -> None:
    """
    Create directory structure
    
    Args:
        base_dir: Base directory path
        subdirs: List of subdirectory names to create
    """
    for subdir in subdirs:
        path = os.path.join(base_dir, subdir)
        os.makedirs(path, exist_ok=True)
    
    logging.getLogger(__name__).info(f"Created directory structure in: {base_dir}")


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def get_timestamp() -> str:
    """
    Get current timestamp as string
    
    Returns:
        Timestamp string (YYYY-MM-DD_HH-MM-SS)
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def print_pipeline_header(title: str) -> None:
    """
    Print formatted pipeline header
    
    Args:
        title: Header title
    """
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def print_pipeline_summary(stats: Dict) -> None:
    """
    Print pipeline execution summary
    
    Args:
        stats: Statistics dictionary
    """
    print("\n" + "="*60)
    print("  PIPELINE EXECUTION SUMMARY")
    print("="*60)
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("="*60 + "\n")


def validate_directories(directories: Dict) -> bool:
    """
    Validate that required directories exist
    
    Args:
        directories: Dictionary of {name: path} to validate
        
    Returns:
        True if all directories exist, False otherwise
    """
    logger = logging.getLogger(__name__)
    all_exist = True
    
    for name, path in directories.items():
        if not os.path.exists(path):
            logger.error(f"{name} directory not found: {path}")
            all_exist = False
        else:
            logger.debug(f"{name} directory found: {path}")
    
    return all_exist
