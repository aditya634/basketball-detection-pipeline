"""
Quick YOLO prediction script.
- Uses best trained weights if found, otherwise falls back to a small pretrained model.
- Runs prediction on a folder of images or a video file.
"""

import argparse
from pathlib import Path
import sys

# Ensure src utils are importable if needed later
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def default_weights() -> str:
    # Prefer trained weights
    best = Path('runs/train/basketball-yolov8s/weights/best.pt')
    if best.exists():
        return str(best)
    # Fallback to lightweight pretrained (fast sanity check)
    return 'yolo11n.pt'


def default_source() -> str:
    # Prefer val images from the built dataset
    val_images = Path('data/yolo_dataset/val/images')
    if val_images.exists():
        return str(val_images)
    # Fallback to augmented images root if available
    augmented = Path('data/augmented')
    if augmented.exists():
        return str(augmented)
    # Last resort: project root
    return '.'


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--weights', type=str, default=default_weights(), help='Path to weights .pt file')
    p.add_argument('--source', type=str, default=default_source(), help='Image/video path or directory')
    p.add_argument('--imgsz', type=int, default=640, help='Inference image size')
    p.add_argument('--conf', type=float, default=0.25, help='Confidence threshold')
    p.add_argument('--device', type=str, default='0', help='CUDA device id or cpu')
    return p.parse_args()


def main():
    args = parse_args()
    try:
        from ultralytics import YOLO
    except Exception as e:
        print('Ultralytics not installed. Install with: pip install ultralytics')
        print(f'Import error: {e}')
        return

    print(f'Loading weights: {args.weights}')
    model = YOLO(args.weights)

    print(f'Predicting on: {args.source}')
    results = model.predict(
        source=args.source,
        imgsz=args.imgsz,
        conf=args.conf,
        device=args.device,
        project='runs/predict',
        name='demo',
        exist_ok=True,
        save=True,
        save_txt=False,
        verbose=True,
    )
    print('Prediction complete. Results saved under runs/predict/.')
    if isinstance(results, list) and results:
        print(f'First result: {results[0].path if hasattr(results[0], "path") else type(results[0])}')


if __name__ == '__main__':
    main()
