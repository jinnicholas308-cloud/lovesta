"""
File upload utilities: validation, storage, and image processing.
"""
import os
import uuid
from flask import current_app
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_DIMENSION = 1200


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file) -> str:
    """
    Save an uploaded image file with a UUID filename.
    Resizes to MAX_DIMENSION keeping aspect ratio, and optimizes quality.
    Returns the saved filename.
    """
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)

    img = Image.open(file)
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    img.save(filepath, optimize=True, quality=85)

    return filename


def delete_image(filename: str) -> bool:
    """
    Delete an image file from the upload folder.
    Returns True if deleted, False if not found.
    """
    if not filename:
        return False
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
