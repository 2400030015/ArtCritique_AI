import bcrypt
import re

def hash_password(password):
    """
    Hashes a plain text password using bcrypt with a random salt.
    Returns the hashed password decoded to a UTF-8 string for DB storage.
    
    Parameters:
    - password: str, plain text password
    
    Returns:
    - hashed: str, hashed password
    """
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def verify_password(password, hashed_password):
    """
    Checks if a plain text password matches a stored bcrypt hash.
    
    Parameters:
    - password: str, plain text password
    - hashed_password: str, bcrypt hash to compare against
    
    Returns:
    - matches: bool, True if match, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def validate_email(email):
    """
    Validates email syntax using standard RFC 5322 regex.
    
    Parameters:
    - email: str, email address
    
    Returns:
    - valid: bool
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email.strip()) is not None

def validate_password_strength(password):
    """
    Validates password strength according to standard security rules:
    - Minimum length of 8 characters
    - Contains at least 1 uppercase letter
    - Contains at least 1 lowercase letter
    - Contains at least 1 numeric digit
    - Contains at least 1 special character (e.g. @, $, !, %, *, ?, &, etc.)
    
    Parameters:
    - password: str, plain text password to check
    
    Returns:
    - is_strong: bool
    - message: str, explanation of failures if not strong
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
        
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
        
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
        
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one numeric digit."
        
    if not re.search(r"[@$!%*?&#^()_+\-=\[\]{};':\",./<>?`~|]", password):
        return False, "Password must contain at least one special character."
        
    return True, "Password is strong."
