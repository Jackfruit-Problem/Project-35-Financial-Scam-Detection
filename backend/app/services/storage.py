"""Evidence file storage. SRS 3.3 and 6.3: size-limited, scanned, encrypted at rest.

Files are encrypted with AES-256-GCM before they touch the disk, so a stolen
copy of the evidence directory yields nothing readable. GCM is authenticated,
which means a tampered ciphertext fails to decrypt rather than quietly
returning corrupted bytes -- appropriate for material that may end up as legal
evidence.

The key is derived from SECRET_KEY here because this is a course project with
one deployment. A production system would use a managed KMS with per-file data
keys and rotation; that is a deliberate, documented simplification, not an
oversight.
"""
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

# REQ-10 calls for a configurable limit; 10 MB comfortably covers screenshots
# and chat-log exports without inviting uploads that fill the disk.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
    "text/plain",
}

_NONCE_BYTES = 12


class UploadRejected(Exception):
    """Raised when a file must not be stored. Carries a user-facing reason."""


def _key() -> bytes:
    """32-byte key derived from the configured secret."""
    return hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()


def sha256_of(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def evidence_root() -> Path:
    root = Path(settings.EVIDENCE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def scan(payload: bytes) -> None:
    """Malware scan. SRS 3.3 requires uploads be scanned before storage.

    This is a placeholder with a real interface, not a pretend one: it detects
    the EICAR test string, which is the industry-standard harmless file used to
    prove a scanner is wired in. Swapping in ClamAV means replacing this
    function body -- every caller and test stays as it is.
    """
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR"
    if eicar in payload:
        raise UploadRejected("File rejected by malware scan")


def validate(filename: str, content_type: str, payload: bytes) -> None:
    if not payload:
        raise UploadRejected("File is empty")
    if len(payload) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadRejected(f"File exceeds the {limit_mb} MB limit")
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadRejected(f"Unsupported file type: {content_type}")
    scan(payload)


def store(payload: bytes, *, case_ref: str, filename: str) -> tuple[str, str]:
    """Encrypt and write the file. Returns (stored_path, sha256_of_plaintext).

    The digest is of the *plaintext*, so it stays comparable to a hash the
    submitter or a court computes from the original file.
    """
    digest = hashlib.sha256(payload).hexdigest()

    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = AESGCM(_key()).encrypt(nonce, payload, None)

    case_dir = evidence_root() / case_ref
    case_dir.mkdir(parents=True, exist_ok=True)

    # Stored under the content digest rather than the uploaded filename: user
    # filenames are attacker-controlled and would otherwise be a path-traversal
    # hazard. The original name is kept in the database for display.
    target = case_dir / f"{digest}.enc"
    target.write_bytes(nonce + ciphertext)

    return str(target), digest


def load(stored_path: str) -> bytes:
    """Decrypt a stored file. Raises if the ciphertext was tampered with."""
    blob = Path(stored_path).read_bytes()
    nonce, ciphertext = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
    return AESGCM(_key()).decrypt(nonce, ciphertext, None)
