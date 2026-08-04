"""Custom Ansible filters for qBittorrent configuration generation.

This module is loaded automatically by Ansible when the role is executed.
"""

import base64
import hashlib
import os


def qbittorrent_password_hash(password):
    """Compute qBittorrent's PBKDF2-HMAC-SHA512 WebUI password hash.

    qBittorrent stores the WebUI password as ``WebUI\\Password_PBKDF2`` with
    value ``@ByteArray(<base64>)``.  The base64 blob is
    ``salt (16 bytes) || derived key (64 bytes)`` where the key is
    PBKDF2-HMAC-SHA512 over the UTF-8 password with the 16-byte random salt,
    100000 iterations and a 64-byte output length (matches qBittorrent's
    ``Utils::Password::PBKDF2``).

    Args:
        password: Plain-text WebUI password.

    Returns:
        The base64 blob to embed inside ``@ByteArray(...)``, or ``""`` when the
        password is empty.
    """
    if not password:
        return ""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100000, dklen=64)
    return base64.b64encode(salt + dk).decode("ascii")


class FilterModule(object):
    """Expose this module's helper functions as Ansible filter plugins."""

    def filters(self):
        """Return the mapping from Jinja2 filter names to Python callables."""
        return {
            # Makes ``{{ qbittorrent_webui_password | qbittorrent_password_hash }}``
            # available in templates.
            'qbittorrent_password_hash': qbittorrent_password_hash
        }
