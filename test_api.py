#!/usr/bin/env python
"""
Test script for Bird Counting API
"""
import requests
import json
import sys
from pathlib import Path


def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing /health endpoint...")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Status: {data['status']}")
        print(f"✓ Message: {data['message']}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Could not connect to server")
        print("  Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_analyze_video(video_path: str):
    """Test video analysis endpoint"""
    print("\n" + "="*60)
    print("Testing /analyze_video endpoint...")
    print("="*60)
    
    if not Path(video_path).exists():
        print(f"✗ ERROR: Video file not found: {video_path}")
        return False
    
    print(f"Video: {video_path}")
    print("Uploading and processing...")
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'fps_sample': 5,
                'conf_thresh': 0.25,
                'iou_thresh': 0.45
            }
            
            response = requests.post(
                "http://localhost:8000/analyze_video",
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            print("\n✓ Analysis Complete!")
            print(f"  - Total frames processed: {result['video_info']['total_frames_processed']}")
            print(f"  - Total unique tracks: {result['video_info']['total_tracks']}")
            print(f"  - Count records: {len(result['counts'])}")
            print(f"  - Weight estimates: {len(result['weight_estimates']['per_bird'])}")
            
            print("\n  Artifacts generated:")
            print(f"    - Annotated video: {result['artifacts']['annotated_video']}")
            print(f"    - Tracks JSON: {result['artifacts']['tracks_json']}")
            
            # Save response
            output_file = "test_response.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n  Response saved to: {output_file}")
            
            return True
            
    except requests.exceptions.Timeout:
        print("✗ ERROR: Request timed out (video processing takes too long)")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("Bird Counting API Test Script")
    print("=" * 60)
    
    # Test health endpoint
    if not test_health():
        print("\n⚠ Server is not running!")
        print("Start the server first: python main.py")
        sys.exit(1)
    
    # Test video analysis
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        print("\nUsage: python test_api.py <path_to_video>")
        print("\nExample:")
        print("  python test_api.py sample_data/poultry_video.mp4")
        sys.exit(0)
    
    if test_analyze_video(video_path):
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("✗ Tests failed!")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
