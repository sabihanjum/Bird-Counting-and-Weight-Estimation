"""
Example usage script demonstrating the Bird Counting API
"""
import requests
from pathlib import Path
import json


def analyze_video_example():
    """Example of how to use the API programmatically"""
    
    # API endpoint
    api_url = "http://localhost:8000/analyze_video"
    
    # Video file path
    video_path = "sample_data/poultry_video.mp4"
    
    # Check if video exists
    if not Path(video_path).exists():
        print(f"Error: Video not found at {video_path}")
        print("Please place a sample video in the sample_data/ directory")
        return
    
    # Parameters
    params = {
        'fps_sample': 5,        # Process every 5th frame
        'conf_thresh': 0.25,    # Detection confidence threshold
        'iou_thresh': 0.45      # NMS IoU threshold
    }
    
    # Prepare file
    with open(video_path, 'rb') as video_file:
        files = {'video': video_file}
        
        print(f"Uploading and analyzing: {video_path}")
        print(f"Parameters: {params}")
        print("Please wait, this may take a few minutes...\n")
        
        # Send request
        response = requests.post(api_url, files=files, data=params)
        
        if response.status_code == 200:
            result = response.json()
            
            # Print summary
            print("✓ Analysis Complete!\n")
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            
            video_info = result['video_info']
            print(f"Video: {video_info['filename']}")
            print(f"Frames processed: {video_info['total_frames_processed']}")
            print(f"Unique birds tracked: {video_info['total_tracks']}")
            
            print("\nBird Counts:")
            for i, count_data in enumerate(result['counts'][:5]):
                print(f"  {count_data['timestamp']} - {count_data['count']} birds")
            if len(result['counts']) > 5:
                print(f"  ... and {len(result['counts']) - 5} more timestamps")
            
            print("\nWeight Estimates:")
            weight_data = result['weight_estimates']
            agg = weight_data['aggregate']
            print(f"  Total birds: {agg['total_birds']}")
            print(f"  Mean weight index: {agg['mean_weight_index']:.2f}")
            print(f"  Range: {agg['min_weight_index']:.2f} - {agg['max_weight_index']:.2f}")
            print(f"  Std dev: {agg['std']:.2f}")
            
            print("\nGenerated Artifacts:")
            print(f"  Annotated video: {result['artifacts']['annotated_video']}")
            print(f"  Tracks JSON: {result['artifacts']['tracks_json']}")
            
            # Save full response
            output_file = "example_response.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull response saved to: {output_file}")
            
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print("Bird Counting API - Example Usage")
    print("=" * 60)
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("✓ API server is running\n")
            analyze_video_example()
        else:
            print("✗ API server returned error")
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to API server")
        print("\nPlease start the server first:")
        print("  python main.py")
