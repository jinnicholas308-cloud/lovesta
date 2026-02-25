"""
Reusable form/input validators.
"""
import re

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def is_allowed_image(filename: str) -> bool:
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def validate_password_strength(password: str) -> list[str]:
    """Return list of error messages; empty list means password is valid."""
    errors = []
    if len(password) < 6:
        errors.append('비밀번호는 6자 이상이어야 합니다.')
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
