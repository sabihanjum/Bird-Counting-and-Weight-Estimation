# Quick Setup and Run Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

### 3. Test the API

Visit `http://localhost:8000/docs` in your browser for interactive API documentation.

Or use curl:

**Windows PowerShell:**
```powershell
# Health check
curl.exe http://localhost:8000/health

# Analyze video
curl.exe -X POST "http://localhost:8000/analyze_video" `
  -F "video=@sample_data/your_video.mp4" `
  -F "fps_sample=5" `
  -o response.json
```

**Linux/Mac:**
```bash
# Health check
curl http://localhost:8000/health

# Analyze video
curl -X POST "http://localhost:8000/analyze_video" \
  -F "video=@sample_data/your_video.mp4" \
  -F "fps_sample=5" \
  -o response.json
```

### 4. Check Results

- Annotated video: `outputs/[filename]_annotated_[timestamp].mp4`
- JSON results: `outputs/[filename]_tracks_[timestamp].json`

## Configuration

Edit `config.py` to adjust:
- Detection thresholds
- Tracking parameters
- Weight estimation factors
- API settings

## Need Help?

See the full [README.md](README.md) for detailed documentation.
