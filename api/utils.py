# api/utils.py
import string

BASE62_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

def shortcode_to_media_id(shortcode: str) -> int:
    """
    Decode Instagram shortcode (base62) to numeric media id.
    Example: 'DRZt1bbk8YG' -> 1234567890123456789
    """
    alphabet = BASE62_ALPHABET
    base = len(alphabet)
    num = 0
    for ch in shortcode:
        try:
            idx = alphabet.index(ch)
        except ValueError:
            # shortcode may include '-' or '_' for urlsafe base64 variants
            raise ValueError(f"Invalid character '{ch}' in shortcode")
        num = num * base + idx
    return num


def extract_shortcode_from_url(url: str) -> str:
    """
    Extract the shortcode from a variety of Instagram URLs.
    Examples:
      https://www.instagram.com/reel/DRZt1bbk8YG/?utm...
      https://www.instagram.com/p/DRZt1bbk8YG/
    Returns shortcode or raises ValueError.
    """
    if not url:
        raise ValueError("Empty URL")

    url = url.split("?")[0].rstrip("/")
    parts = url.split("/")
    # shortcode is usually the last non-empty part
    if not parts:
        raise ValueError("Cannot parse URL")
    shortcode = parts[-1] if parts[-1] else parts[-2]
    if not shortcode:
        raise ValueError("Shortcode not found in URL")
    return shortcode
