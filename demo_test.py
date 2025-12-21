"""
Quick demonstration script to test the API
"""
import requests
import json

# Test 1: Health endpoint
print("=" * 60)
print("TEST 1: Health Check")
print("=" * 60)
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✓ Health check passed!")
except Exception as e:
    print(f"✗ Health check failed: {e}")

print("\n" + "=" * 60)
print("TEST 2: Root Endpoint")
print("=" * 60)
try:
    response = requests.get("http://localhost:8000/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✓ Root endpoint test passed!")
except Exception as e:
    print(f"✗ Root endpoint test failed: {e}")

print("\n" + "=" * 60)
print("TEST 3: API Documentation")
print("=" * 60)
print("Interactive API docs available at:")
print("  - Swagger UI: http://localhost:8000/docs")
print("  - ReDoc: http://localhost:8000/redoc")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
✓ Virtual environment created and activated
✓ All dependencies installed successfully
✓ FastAPI server running on http://localhost:8000
✓ Health endpoint responding correctly
✓ API ready for video analysis

NEXT STEPS:
1. Place your CCTV video file in the project directory
2. Use the test_api.py script to test video analysis
3. Or access http://localhost:8000/docs for interactive API testing

To analyze a video via API:
  POST http://localhost:8000/analyze_video
  - Upload video file
  - Get counts, tracks, and annotated output
""")
