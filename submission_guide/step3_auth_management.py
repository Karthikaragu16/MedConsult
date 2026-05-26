# STEP 3: AUTHENTICATION & SECURITY LAYER
# This module handles password hashing and verification.

from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Securely hashes a password for database storage."""
    return generate_password_hash(password)

def verify_password(hashed_password, plain_password):
    """Verifies a plain text password against a stored hash."""
    return check_password_hash(hashed_password, plain_password)

# Note: This protects user data and ensures privacy as per Feature 11.
