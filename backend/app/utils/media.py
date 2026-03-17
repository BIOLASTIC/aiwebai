import os
import uuid
import httpx
from pathlib import Path
from backend.app.config import settings

async def download_to_uploads(url: str) -> str:
    """Download an external media file and save it to the local uploads directory."""
    if not url or not url.startswith('http'):
        return url
        
    try:
        # Determine the project root and uploads directory
        # Current file: backend/app/utils/media.py
        # Project root: ../../../../uploads
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        uploads_dir = project_root / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        
        # Fetch the content
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=30.0)
            if response.status_code != 200:
                return url
            
            # Determine extension from content-type or URL
            content_type = response.headers.get("content-type", "")
            ext = ".png" # default
            if "image/jpeg" in content_type: ext = ".jpg"
            elif "image/webp" in content_type: ext = ".webp"
            elif "video/mp4" in content_type: ext = ".mp4"
            else:
                # Try to guess from URL
                path_ext = Path(url).suffix.split('?')[0]
                if path_ext: ext = path_ext

            # Save the file
            filename = f"cloud_{uuid.uuid4().hex}{ext}"
            filepath = uploads_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Return the local URL
            return f"/uploads/{filename}"
    except Exception as e:
        print(f"Error downloading media: {e}")
        return url
