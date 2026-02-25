"""
File upload utilities: validation, storage, and image processing.
"""
import os
import uuid
from flask import current_app
from PIL import Image, UnidentifiedImageError

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_DIMENSION = 1200


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _to_rgb(img: Image.Image) -> Image.Image:
    """
    모든 이미지 모드를 RGB로 변환.
    투명도(RGBA, LA, PA)는 흰 배경에 합성.
    팔레트(P) 모드는 RGBA로 먼저 변환 후 처리.
    """
    if img.mode == 'P':
        img = img.convert('RGBA')

    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        mask = img.split()[-1]  # alpha channel
        background.paste(img.convert('RGB'), mask=mask)
        return background

    if img.mode != 'RGB':
        return img.convert('RGB')

    return img


def save_image(file) -> str:
    """
    업로드된 이미지를 UUID 파일명으로 저장.
    - 모든 포맷을 JPEG로 통일 (투명도 → 흰 배경 합성)
    - 최대 1200px 리사이즈 (비율 유지)
    - 반환값: 저장된 파일명 (예: 'abc123.jpg')
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_folder, filename)

    try:
        img = Image.open(file)
        img = _to_rgb(img)
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        img.save(filepath, 'JPEG', optimize=True, quality=85)
    except UnidentifiedImageError:
        raise ValueError('지원하지 않는 이미지 형식입니다.')
    except Exception as e:
        raise ValueError(f'이미지 저장 실패: {e}')

    return filename


def delete_image(filename: str) -> bool:
    """
    업로드 폴더에서 이미지 삭제.
    Returns True if deleted, False if not found.
    """
    if not filename:
        return False
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
