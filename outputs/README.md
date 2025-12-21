# Outputs Directory

This directory contains generated outputs from video analysis:

- **Annotated videos**: `*_annotated_*.mp4` files with bounding boxes and tracking IDs
- **JSON results**: `*_tracks_*.json` files with complete analysis data

Files are automatically named with timestamp to avoid overwrites.

## Cleanup

To clean old outputs:

```bash
# Windows PowerShell
Remove-Item outputs\* -Include *.mp4,*.json

# Linux/Mac
rm outputs/*.mp4 outputs/*.json
```
