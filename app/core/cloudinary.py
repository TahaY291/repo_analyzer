import asyncio

import cloudinary
import cloudinary.uploader

from app.core.config import settings
from app.core.exceptions import ApiError

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


async def upload_image(data: bytes, folder: str = "uploads") -> dict:
    try:
        return await asyncio.to_thread(
            cloudinary.uploader.upload,
            data,
            folder=folder,
            resource_type="image",
            use_filename=False,
        )
    except Exception as e:
        print("Cloudinary upload error:", e)
        raise ApiError(502, "Image upload failed")


async def delete_image(public_id: str) -> None:
    try:
        await asyncio.to_thread(cloudinary.uploader.destroy, public_id)
    except Exception as e:
        print("Cloudinary delete error:", e)