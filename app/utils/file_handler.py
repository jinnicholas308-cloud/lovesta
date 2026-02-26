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


def _configure_cloudinary() -> bool:
    """
    Cloudinary를 명시적으로 설정하고 성공 여부 반환.

    URL 파싱 순서:
    1. CLOUDINARY_URL 환경변수 파싱
       - 'CLOUDINARY_URL=cloudinary://...' 형태도 자동 정제
    2. 개별 변수 CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET

    cloudinary.config(cloudinary_url=...) 는 SDK에서 무시되므로
    urlparse로 직접 파싱 후 cloud_name / api_key / api_secret 각각 주입.
    """
    from urllib.parse import urlparse
    import cloudinary

    # --- 방법 1: CLOUDINARY_URL ---
    raw = os.getenv('CLOUDINARY_URL', '')
    # "CLOUDINARY_URL=cloudinary://..." 형태 자동 정제
    if raw and '=' in raw and not raw.startswith('cloudinary://'):
        raw = raw.split('=', 1)[-1].strip()

    if raw.startswith('cloudinary://'):
        try:
            p = urlparse(raw)
            cloudinary.config(
                cloud_name=p.hostname,
                api_key=p.username,
                api_secret=p.password,
                secure=True,
            )
            return True
        except Exception:
            pass

    # --- 방법 2: 개별 환경변수 ---
    cloud_name  = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key     = os.getenv('CLOUDINARY_API_KEY')
    api_secret  = os.getenv('CLOUDINARY_API_SECRET')
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        return True

    return False


def _save_to_cloudinary(file) -> str:
    """Cloudinary에 업로드 후 secure URL 반환."""
    import cloudinary
    import cloudinary.uploader

    if not _configure_cloudinary():
        raise ValueError('Cloudinary 설정 실패: CLOUDINARY_URL 또는 개별 키를 확인하세요.')

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
        if os.getenv('CLOUDINARY_URL') or os.getenv('CLOUDINARY_API_KEY'):
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
        if os.getenv('CLOUDINARY_URL') or os.getenv('CLOUDINARY_API_KEY'):
            try:
                import cloudinary.uploader
                _configure_cloudinary()
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
