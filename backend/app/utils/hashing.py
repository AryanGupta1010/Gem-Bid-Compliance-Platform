import hashlib
from typing import BinaryIO, Union

def compute_sha3_512(file_or_bytes: Union[bytes, BinaryIO]) -> str:
    """
    Computes SHA-3-512 hash string for an immutable document record.
    """
    hasher = hashlib.sha3_512()
    if isinstance(file_or_bytes, bytes):
        hasher.update(file_or_bytes)
    else:
        # Seek to beginning if seekable
        if hasattr(file_or_bytes, "seek"):
            file_or_bytes.seek(0)
        while chunk := file_or_bytes.read(65536):
            hasher.update(chunk)
        if hasattr(file_or_bytes, "seek"):
            file_or_bytes.seek(0)
    return hasher.hexdigest()
