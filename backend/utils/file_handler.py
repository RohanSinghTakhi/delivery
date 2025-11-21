import os
import uuid
from pathlib import Path
from fastapi import UploadFile
import aiofiles
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/backend/uploads")
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10"))

# Ensure upload directory exists (lazy initialization)
_upload_dir_initialized = False

def _ensure_upload_dir():
    """Ensure upload directory exists (called lazily)"""
    global _upload_dir_initialized
    if not _upload_dir_initialized:
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        _upload_dir_initialized = True

async def save_upload_file(file: UploadFile, subfolder: str = "") -> str:
    """
    Save uploaded file to local storage
    Returns: relative file path
    
    Note: This is a local storage implementation. For production,
    replace with AWS S3, Cloudinary, or similar service.
    """
    try:
        # Ensure upload directory exists
        _ensure_upload_dir()
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create subfolder if specified
        save_dir = Path(UPLOAD_DIR) / subfolder
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            
            # Check file size
            if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise ValueError(f"File size exceeds {MAX_UPLOAD_SIZE_MB}MB limit")
            
            await out_file.write(content)
        
        # Return relative path
        relative_path = str(Path(subfolder) / unique_filename)
        logger.info(f"File saved: {relative_path}")
        return relative_path
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise

def get_file_url(file_path: str, base_url: str = "") -> str:
    """
    Generate URL for uploaded file
    
    For local storage: returns /uploads/{file_path}
    For cloud storage: would return full CDN URL
    """
    if not file_path:
        return ""
    
    # For local storage
    return f"/api/uploads/{file_path}"
    
    # For S3/Cloudinary (uncomment and modify as needed):
    # return f"https://your-cdn-domain.com/{file_path}"