"""
Reusable form/input validators.
보안: 이메일 검증 강화, 비밀번호 정책 강화, 파일 확장자 화이트리스트.
"""
import re

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv', 'm4v'}
# RFC 5322 간이 검증 + 길이 제한
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 254:  # RFC 5321 최대 길이
        return False
    return bool(EMAIL_REGEX.match(email))


def is_allowed_image(filename: str) -> bool:
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def is_allowed_video(filename: str) -> bool:
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    )


def validate_password_strength(password: str) -> list[str]:
    """Return list of error messages; empty list means password is valid."""
    errors = []
    if len(password) < 6:
        errors.append('비밀번호는 6자 이상이어야 합니다.')
    if len(password) > 128:
        errors.append('비밀번호는 128자 이하여야 합니다.')
    return errors


def validate_username(username: str) -> list[str]:
    errors = []
    if len(username) < 2:
        errors.append('사용자명은 2자 이상이어야 합니다.')
    if len(username) > 50:
        errors.append('사용자명은 50자 이하여야 합니다.')
    if not re.match(r'^[\w가-힣]+$', username):
        errors.append('사용자명은 한글, 영문, 숫자, 밑줄만 허용됩니다.')
    return errors
