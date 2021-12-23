# The Cryptography and/or related tasks/functions come in here.
import hashlib
import bcrypt
import string
import random

def hash_md5(s: str) -> str:
    """Hashes a string in the MD5 hashing algorhythm.
    
    Args:
        s (str): The string to hash using the algorhythm.
    
    Returns:
        `str` hashed in md5.
    """

    return hashlib.md5(s.encode()).digest().hex()

def validate_md5(s: str) -> bool:
    """Checks if the provided string is a valid MD5 hash.
    
    Args:
        s (str): An MD5 hashed string.
    """

    # simple check for now.
    return len(s) == 32

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

AV_CHARS = string.ascii_letters + string.digits
def gen_rand_str(len: int) -> str:
    """Generates a string consisting of random alpha-numeric characters.
    
    Args:
        len (int): The lenght (in chars) of the string.
    """

    return "".join(random.choice(AV_CHARS) for _ in range(len))

def ts_to_utc_ticks(ts: int) -> int:
    """Convert's a UNIX timestamp to a UTC ticks. Equivalent to the reverse of
    C#'s `DateTime.ToUniversalTime().Ticks`.
    """

    return int(ts * 1e7) + 0x89F7FF5F7B58000
