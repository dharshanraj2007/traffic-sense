import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
from app.config import (
    STORAGE_BACKEND, EVIDENCE_DIR, UPLOAD_DIR,
    CLOUDINARY_URL, SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET
)

class StorageService(ABC):
    @abstractmethod
    def save_image(self, image_bytes: bytes, filename: str = None) -> str:
        """Saves image and returns accessible URL."""
        pass

    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str) -> str:
        """Saves a generic file and returns accessible URL or local path."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, upload_dir: Path = UPLOAD_DIR, evidence_dir: Path = EVIDENCE_DIR):
        self.upload_dir = upload_dir
        self.evidence_dir = evidence_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_bytes: bytes, filename: str = None) -> str:
        if not filename:
            filename = f"evidence_{uuid.uuid4().hex[:10]}.jpg"
        target_path = self.evidence_dir / filename
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        # Return path served by FastAPI static files mount: /uploads/evidence/{filename}
        return f"/uploads/evidence/{filename}"

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        target_path = self.upload_dir / filename
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return str(target_path)


class CloudinaryStorageService(StorageService):
    def __init__(self):
        # Fallback to local if cloudinary fails or is unconfigured
        self.fallback = LocalStorageService()
        self.configured = bool(CLOUDINARY_URL)

    def save_image(self, image_bytes: bytes, filename: str = None) -> str:
        if not self.configured:
            return self.fallback.save_image(image_bytes, filename)
        try:
            import cloudinary
            import cloudinary.uploader
            res = cloudinary.uploader.upload(image_bytes, folder="traffic_sense/evidence")
            return res.get("secure_url", res.get("url"))
        except Exception:
            return self.fallback.save_image(image_bytes, filename)

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        return self.fallback.save_file(file_bytes, filename)


class SupabaseStorageService(StorageService):
    def __init__(self):
        self.fallback = LocalStorageService()
        self.configured = bool(SUPABASE_URL and SUPABASE_KEY)

    def save_image(self, image_bytes: bytes, filename: str = None) -> str:
        if not self.configured:
            return self.fallback.save_image(image_bytes, filename)
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            if not filename:
                filename = f"evidence_{uuid.uuid4().hex[:10]}.jpg"
            path = f"{filename}"
            supabase.storage.from_(SUPABASE_BUCKET).upload(path, image_bytes)
            public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
            return public_url
        except Exception:
            return self.fallback.save_image(image_bytes, filename)

    def save_file(self, file_bytes: bytes, filename: str) -> str:
        return self.fallback.save_file(file_bytes, filename)


def get_storage_service() -> StorageService:
    backend = STORAGE_BACKEND.lower()
    if backend == "cloudinary":
        return CloudinaryStorageService()
    elif backend == "supabase":
        return SupabaseStorageService()
    return LocalStorageService()
