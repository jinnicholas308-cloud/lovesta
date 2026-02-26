"""
File upload utilities: validation, storage, and image processing.

Storage strategy:
- 환경변수 CLOUDINARY_URL 있음 → Cloudinary (Railway 등 프로덕션)
- 없음                         → 로컬 storage/uploads/ (개발환경)
"""
import os
import uuid
import io
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
        mask = img.split()[-1]
        background.paste(img.convert('RGB'), mask=mask)
        return background

    if img.mode != 'RGB':
        return img.convert('RGB')

    return img


def _process_image(file) -> Image.Image:
    """파일을 열어 RGB 변환 + 리사이즈."""
    try:
        img = Image.open(file)
    except UnidentifiedImageError:
        raise ValueError('지원하지 않는 이미지 형식입니다.')
    img = _to_rgb(img)
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    return img


def _get_cloudinary_url() -> str:
    """
    CLOUDINARY_URL 환경변수를 정제해서 반환.
    Railway에서 'CLOUDINARY_URL=cloudinary://...' 형태로 저장된 경우 자동 수정.
    """
    raw = os.getenv('CLOUDINARY_URL', '')
    # 변수명이 값에 포함된 경우 제거: "CLOUDINARY_URL=cloudinary://..." → "cloudinary://..."
    if '=' in raw and not raw.startswith('cloudinary://'):
        raw = raw.split('=', 1)[-1].strip()
    return raw


def _save_to_cloudinary(file) -> str:
    """Cloudinary에 업로드 후 secure URL 반환."""
    import cloudinary
    import cloudinary.uploader

    # 명시적으로 URL 파싱하여 설정 (환경변수 자동 파싱 오류 방지)
    cloudinary_url = _get_cloudinary_url()
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url)

    img = _process_image(file)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', optimize=True, quality=85)
    buf.seek(0)

    result = cloudinary.uploader.upload(
        buf,
        folder='lovesta',
        resource_type='image',
        format='jpg',
    )
    return result['secure_url']


def _save_to_local(file) -> str:
    """로컬 storage/uploads/ 에 저장 후 파일명 반환."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_folder, filename)

    img = _process_image(file)
    img.save(filepath, 'JPEG', optimize=True, quality=85)
    return filename


def save_image(file) -> str:
    """
    이미지 저장 (Cloudinary 또는 로컬 자동 선택).
    반환값:
      - Cloudinary: 'https://res.cloudinary.com/...' (전체 URL)
      - 로컬:       'abc123.jpg' (파일명만)
    """
    try:
        if _get_cloudinary_url():
            return _save_to_cloudinary(file)
        return _save_to_local(file)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f'이미지 저장 실패: {e}')


def delete_image(image_path: str) -> bool:
    """이미지 삭제 (Cloudinary 또는 로컬 자동 선택)."""
    if not image_path:
        return False

    if image_path.startswith('http'):
        if _get_cloudinary_url():
            try:
                import cloudinary, cloudinary.uploader
                cloudinary.config(cloudinary_url=_get_cloudinary_url())
                parts = image_path.split('/')
                public_id = 'lovesta/' + parts[-1].rsplit('.', 1)[0]
                cloudinary.uploader.destroy(public_id)
                return True
            except Exception:
                return False
    else:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], image_path)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True

    return False
