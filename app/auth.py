"""Admin password check. The plain password is never written or logged."""

from werkzeug.security import check_password_hash, generate_password_hash

USERNAME = "admin"


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    if not password or not password_hash:
        return False
    try:
        return check_password_hash(password_hash, password)
    except (TypeError, ValueError):
        return False


def password_matches(username, password, password_hash):
    if username != USERNAME:
        return False
    return verify_password(password, password_hash)
