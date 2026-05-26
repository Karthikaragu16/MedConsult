from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Returns a hashed version of the password.
    """
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """
    Verifies a password against a hash.
    """
    return check_password_hash(hashed_password, password)

def is_secure_password(password):
    """
    Basic security check for password length.
    """
    return len(password) >= 6
