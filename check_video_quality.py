"""
Video Quality Analyzer
Extract and display quality metrics for all videos in source_videos/
Shows: Resolution, FPS, Duration, Bitrate, Codec, File Size
"""

import os
import cv2
from pathlib import Path
from datetime import timedelta


def get_video_info(video_path):
    """Extract comprehensive video quality information"""
    try:
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return None
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate duration
        duration_seconds = frame_count / fps if fps > 0 else 0
        duration = str(timedelta(seconds=int(duration_seconds)))
        
        # Get codec information
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        
        # Get file size
        file_size_bytes = os.path.getsize(video_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        file_size_gb = file_size_bytes / (1024 * 1024 * 1024)
        
        # Calculate bitrate (bits per second)
        if duration_seconds > 0:
            bitrate_bps = (file_size_bytes * 8) / duration_seconds
            bitrate_mbps = bitrate_bps / (1024 * 1024)
        else:
            bitrate_mbps = 0
        
        cap.release()
        
        return {
            'resolution': f"{width}x{height}",
            'width': width,
            'height': height,
            'fps': round(fps, 2),
            'frame_count': frame_count,
            'duration': duration,
            'duration_seconds': round(duration_seconds, 2),
            'codec': fourcc.strip(),
            'file_size_mb': round(file_size_mb, 2),
            'file_size_gb': round(file_size_gb, 3),
            'bitrate_mbps': round(bitrate_mbps, 2)
        }
    
    except Exception as e:
        print(f"Error processing video: {e}")
        return None


def get_quality_category(width, height):
    """Categorize video quality based on resolution"""
    pixels = width * height
    
    if pixels >= 3840 * 2160:  # 4K
        return "4K UHD"
    elif pixels >= 2560 * 1440:  # 2K
        return "2K QHD"
    elif pixels >= 1920 * 1080:  # Full HD
        return "Full HD (1080p)"
    elif pixels >= 1280 * 720:  # HD
        return "HD (720p)"
    elif pixels >= 854 * 480:  # SD
        return "SD (480p)"
    else:
        return "Low Quality"


def analyze_videos():
    """Analyze all videos in source_videos directory"""
    
    print("="*80)
    print("  🎥 VIDEO QUALITY ANALYZER")
    print("="*80 + "\n")
    
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    source_dir = base_dir / 'data' / 'source_videos'
    
    if not source_dir.exists():
        print(f"❌ Source videos directory not found: {source_dir}")
        return
    
    # Find all video files
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    videos = []
    for ext in video_extensions:
        videos.extend(source_dir.glob(f'*{ext}'))
        videos.extend(source_dir.glob(f'*{ext.upper()}'))
    
    videos = sorted(set(videos), key=lambda p: p.name.lower())
    
    if not videos:
        print(f"❌ No videos found in {source_dir}")
        return
    
    print(f"Found {len(videos)} video(s) in {source_dir}\n")
    print("="*80)
    
    # Analyze each video
    video_info_list = []
    
    for idx, video_path in enumerate(videos, 1):
        print(f"\n📹 [{idx}/{len(videos)}] {video_path.name}")
        print("-" * 80)
        
        info = get_video_info(video_path)
        
        if info:
            quality = get_quality_category(info['width'], info['height'])
            
            print(f"  Resolution:      {info['resolution']} ({quality})")
            print(f"  Frame Rate:      {info['fps']} FPS")
            print(f"  Duration:        {info['duration']} ({info['duration_seconds']}s)")
            print(f"  Total Frames:    {info['frame_count']:,}")
            print(f"  Codec:           {info['codec']}")
            print(f"  File Size:       {info['file_size_mb']:.2f} MB ({info['file_size_gb']:.3f} GB)")
            print(f"  Bitrate:         {info['bitrate_mbps']:.2f} Mbps")
            
            video_info_list.append({
                'name': video_path.name,
                'info': info,
                'quality': quality
            })
        else:
            print(f"  ❌ Failed to read video information")
    
    # Summary
    if video_info_list:
        print("\n" + "="*80)
        print("  📊 SUMMARY")
        print("="*80 + "\n")
        
        total_duration = sum(v['info']['duration_seconds'] for v in video_info_list)
        total_frames = sum(v['info']['frame_count'] for v in video_info_list)
        total_size_gb = sum(v['info']['file_size_gb'] for v in video_info_list)
        avg_fps = sum(v['info']['fps'] for v in video_info_list) / len(video_info_list)
        avg_bitrate = sum(v['info']['bitrate_mbps'] for v in video_info_list) / len(video_info_list)
        
        # Resolution distribution
        resolutions = {}
        for v in video_info_list:
            res = v['info']['resolution']
            resolutions[res] = resolutions.get(res, 0) + 1
        
        # Quality distribution
        qualities = {}
        for v in video_info_list:
            qual = v['quality']
            qualities[qual] = qualities.get(qual, 0) + 1
        
        print(f"  Total Videos:        {len(video_info_list)}")
        print(f"  Total Duration:      {str(timedelta(seconds=int(total_duration)))} ({total_duration:.2f}s)")
        print(f"  Total Frames:        {total_frames:,}")
        print(f"  Total Size:          {total_size_gb:.3f} GB ({total_size_gb * 1024:.2f} MB)")
        print(f"  Average FPS:         {avg_fps:.2f}")
        print(f"  Average Bitrate:     {avg_bitrate:.2f} Mbps")
        
        print(f"\n  Quality Distribution:")
        for quality, count in sorted(qualities.items()):
            print(f"    • {quality}: {count} video(s)")
        
        print(f"\n  Resolution Distribution:")
        for res, count in sorted(resolutions.items()):
            print(f"    • {res}: {count} video(s)")
        
        # Find highest/lowest quality
        highest_res = max(video_info_list, key=lambda v: v['info']['width'] * v['info']['height'])
        lowest_res = min(video_info_list, key=lambda v: v['info']['width'] * v['info']['height'])
        
        print(f"\n  Highest Quality:     {highest_res['name']} ({highest_res['info']['resolution']})")
        print(f"  Lowest Quality:      {lowest_res['name']} ({lowest_res['info']['resolution']})")
        
        # Export to CSV option
        print("\n" + "="*80)
        export = input("\n💾 Export to CSV file? (y/n): ").strip().lower()
        
        if export == 'y':
            csv_path = base_dir / 'video_quality_report.csv'
            with open(csv_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("Filename,Resolution,Width,Height,Quality,FPS,Duration,Frame Count,")
                f.write("Codec,File Size (MB),File Size (GB),Bitrate (Mbps)\n")
                
                # Data
                for v in video_info_list:
                    info = v['info']
                    f.write(f"{v['name']},")
                    f.write(f"{info['resolution']},{info['width']},{info['height']},")
                    f.write(f"{v['quality']},{info['fps']},{info['duration']},{info['frame_count']},")
                    f.write(f"{info['codec']},{info['file_size_mb']},{info['file_size_gb']},")
                    f.write(f"{info['bitrate_mbps']}\n")
            
            print(f"✅ Report saved to: {csv_path}")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    analyze_videos()
