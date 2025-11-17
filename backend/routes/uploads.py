from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from middleware import get_current_user
from utils import save_upload_file, get_file_url
import os
from pathlib import Path

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/backend/uploads")

@router.post("/proof")
async def upload_proof_of_delivery(
    file: UploadFile = File(...),
    order_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload proof of delivery (photo or signature)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images allowed."
        )
    
    try:
        # Save file
        file_path = await save_upload_file(file, subfolder="proof")
        file_url = get_file_url(file_path)
        
        # Update order if order_id provided
        if order_id:
            mongo_url = os.environ['MONGO_URL']
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ['DB_NAME']]
            
            await db.orders.update_one(
                {"id": order_id},
                {"$set": {"proof_photo_url": file_url}}
            )
        
        return {
            "success": True,
            "file_path": file_path,
            "file_url": file_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.post("/signature")
async def upload_signature(
    file: UploadFile = File(...),
    order_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload delivery signature
    """
    try:
        # Save file
        file_path = await save_upload_file(file, subfolder="signatures")
        file_url = get_file_url(file_path)
        
        # Update order if order_id provided
        if order_id:
            mongo_url = os.environ['MONGO_URL']
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ['DB_NAME']]
            
            await db.orders.update_one(
                {"id": order_id},
                {"$set": {"signature_url": file_url}}
            )
        
        return {
            "success": True,
            "file_path": file_path,
            "file_url": file_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading signature: {str(e)}"
        )

@router.get("/{file_path:path}")
async def get_uploaded_file(file_path: str):
    """
    Serve uploaded files
    """
    full_path = Path(UPLOAD_DIR) / file_path
    
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(full_path)