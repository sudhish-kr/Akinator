"""Character image upload storage — paths only; no engine involvement."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
DEFAULT_CHARACTER_IMAGE_PATH = "/media/characters/default.svg"


class MediaError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def media_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "media"
    root.mkdir(parents=True, exist_ok=True)
    (root / "characters").mkdir(parents=True, exist_ok=True)
    return root


def public_media_path(relative: str) -> str:
    return f"/media/{relative.lstrip('/')}"


async def save_character_image(upload: UploadFile, character_id: uuid.UUID) -> str:
    """Persist uploaded image under media/characters and return public path."""
    content_type = (upload.content_type or "").lower()
    ext = ALLOWED_CONTENT_TYPES.get(content_type)
    if not ext:
        raise MediaError("Unsupported image type. Use JPEG, PNG, WebP, or GIF.", 400)

    data = await upload.read()
    if not data:
        raise MediaError("Empty image file.", 400)
    if len(data) > MAX_UPLOAD_BYTES:
        raise MediaError("Image exceeds 2MB limit.", 400)

    characters_dir = media_root() / "characters"
    # Remove prior files for this character id (any extension)
    for old in characters_dir.glob(f"{character_id}.*"):
        if old.name != "default.svg":
            old.unlink(missing_ok=True)

    filename = f"{character_id}{ext}"
    dest = characters_dir / filename
    dest.write_bytes(data)
    return public_media_path(f"characters/{filename}")
