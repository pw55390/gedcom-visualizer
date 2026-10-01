"""
Media & Document Manager.
Handles file storage, thumbnail generation (Pillow), and media attachments.
"""

import os
from typing import Optional, List
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.schema import MediaModel


class MediaManager:
    def __init__(self, storage_dir: str, session: Session):
        self.storage_dir = storage_dir
        self.session = session
        self.thumbnails_dir = os.path.join(storage_dir, "thumbnails")

        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def add_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        person_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> MediaModel:
        """Attaches a media file and creates thumbnail if image."""
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.storage_dir, filename)

        if file_path != dest_path and os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, dest_path)

        # Create thumbnail if image
        thumb_path = os.path.join(self.thumbnails_dir, f"thumb_{filename}")
        self._generate_thumbnail(dest_path, thumb_path)

        media = MediaModel(
            file_path=dest_path,
            title=title or filename,
            mime_type=mime_type or "image/jpeg",
            person_id=person_id
        )
        self.session.add(media)
        self.session.flush()
        return media

    def get_person_media(self, person_id: str) -> List[MediaModel]:
        """Returns all media attachments for a given person."""
        stmt = select(MediaModel).where(MediaModel.person_id == person_id)
        return list(self.session.scalars(stmt).all())

    def _generate_thumbnail(self, src_path: str, thumb_path: str, size=(120, 120)):
        """Generates square thumbnail image using Pillow."""
        try:
            with Image.open(src_path) as img:
                img.thumbnail(size)
                img.save(thumb_path)
        except Exception:
            pass
