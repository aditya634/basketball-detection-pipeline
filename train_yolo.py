"""
Phase 5: YOLO Training Runner
Uses Ultralytics YOLO with settings from config/config.yaml.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils import load_config, setup_logging
import logging


def main():
    config = load_config('config/config.yaml')
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info('='*60)
    logger.info('PHASE 5: YOLO TRAINING')
    logger.info('='*60)

    train_cfg = config.get('training', {})
    data_yaml = train_cfg.get('data_yaml', 'data/yolo_dataset/data.yaml')
    model_name = train_cfg.get('model', 'yolov8s.pt')

    # Sanity checks
    if not Path(data_yaml).exists():
        logger.error(f'data.yaml not found at {data_yaml}. Run split_dataset.py first.')
        return

    try:
        from ultralytics import YOLO
    except Exception as e:
        logger.error('Ultralytics is not installed. Please install with: pip install ultralytics')
        logger.error(f'Import error: {e}')
        return

    # Log GPU info if available
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f'CUDA available: {torch.cuda.get_device_name(0)}')
        else:
            logger.warning('CUDA not available; training will use CPU (slow).')
    except Exception:
        logger.warning('Could not query torch/cuda status.')

    # Helper: check if any labels exist in dataset splits
    def dataset_has_labels(yaml_path: str) -> bool:
        try:
            import yaml as _yaml
            base = Path(yaml_path).parent
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = _yaml.safe_load(f)
            has_any = False
            for key in ('train', 'val', 'test'):
                if key not in data or not data[key]:
                    continue
                images_path = (base / Path(str(data[key]))).resolve()
                # labels dir is sibling of images dir
                labels_dir = images_path.parent / 'labels'
                if not labels_dir.exists():
                    continue
                for txt in labels_dir.glob('*.txt'):
                    try:
                        with open(txt, 'r', encoding='utf-8') as lf:
                            for line in lf:
                                line = line.strip()
                                if not line:
                                    continue
                                parts = line.split()
                                if len(parts) >= 5 and parts[0].lstrip('-').isdigit():
                                    return True
                    except Exception:
                        continue
            return has_any
        except Exception as e:
            logger.warning(f'Label presence check failed: {e}. Proceeding as if no labels.')
            return False

    # Load model
    logger.info(f'Loading model: {model_name}')
    model = YOLO(model_name)

    # Build train args from config
    train_args = {
        'data': data_yaml,
        'epochs': int(train_cfg.get('epochs', 100)),
        'imgsz': int(train_cfg.get('imgsz', 640)),
        'batch': int(train_cfg.get('batch', 8)),
        'workers': int(train_cfg.get('workers', 2)),
        'seed': int(train_cfg.get('seed', 42)),
        'device': train_cfg.get('device', 0),
        'project': train_cfg.get('project', 'runs/train'),
        'name': train_cfg.get('name', 'basketball-yolov8s'),
        'exist_ok': bool(train_cfg.get('exist_ok', True)),
        'save': bool(train_cfg.get('save', True)),
        'verbose': bool(train_cfg.get('verbose', True)),
    }

    freeze = int(train_cfg.get('freeze', 10))
    if freeze and freeze > 0:
        train_args['freeze'] = freeze

    logger.info('Training args:')
    for k, v in train_args.items():
        logger.info(f'  {k}: {v}')

    # If no labels present, skip training gracefully
    if not dataset_has_labels(data_yaml):
        logger.info('\nNo labels found in dataset splits. Skipping training step.\n'
                    'This is expected if you have not annotated yet.\n'
                    'When your labeled data is ready, add YOLO txt labels under train/val/test labels folders and re-run.')
        return

    # Start training
    logger.info('\nStarting training...')
    results = model.train(**train_args)

    logger.info('\nTraining complete! Best weights and metrics saved under runs/train/.')
    logger.info(f'Results object: {results}')

    # Optional: run validation on best model
    try:
        logger.info('\nValidating best model...')
        model.val(data=data_yaml, imgsz=train_args['imgsz'])
    except Exception as e:
        logger.warning(f'Validation step failed/skipped: {e}')


if __name__ == '__main__':
    main()
