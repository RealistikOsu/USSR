# The Cryptography and/or related tasks/functions come in here.
import hashlib
import bcrypt

def hash_md5(s: str) -> str:
    """Hashes a string in the MD5 hashing algorhythm.
    
    Args:
        s (str): The string to hash using the algorhythm.
    
    Returns:
        `str` hashed in md5.
    """

    return hashlibs.md5(s.encode()).digest().decode()

def verify_bcrypt(s: str, bcrypt_h: str) -> bool:
    """Compares a plaintext string to a bcrypt hash, returning a bool corresponding
    to whether the passwords match.
    
    Args:
        s (str): The plaintext string to compare to the hash.
        bcrypt_h (str): The BCrypt hash to compare the string to.
    
    Returns:
        `bool` corresponding to whether the passwords match.
    """

    return bcrypt.checkpw(s.encode(), bcrypt_h.encode())

def hash_bcrypt(s: str, difficulty: int = 10) -> str:
    """Hashes a string in the bcrypt hashing algorthythm.
    
    Args:
        s (str): The string to hash using BCrypt.
        difficulty (int): The hash rounds to do. The larger it is, the more
            secure but also time consuming.
    
    Returns:
        BCrypt hashed `str` featuring salt etc.
    """

    return bcrypt.hashpw(s, bcrypt.gensalt(difficulty)).decode()

def gen_osu_pw(s: str) -> str:
    """Generates an osu + ripple styled password.
    
    Note:
        This uses MD5 + BCrypt, meaning this func is slow.
    
    Args:
        s (str): The plaintext password to be hashed.
    """

    return hash_bcrypt(hash_md5(s))
