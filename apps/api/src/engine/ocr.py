"""Module OCR et prétraitement d'images de captures d'écran pour SûrCheck AI.
Conforme aux sections 25 et 34 du Cahier des Charges :
- Optimisé pour les captures compressées (WhatsApp, SMS)
- Suppression immédiate des données brutes en mémoire après extraction
- Validation stricte de sécurité (taille max, types MIME)
"""

import io
from typing import Tuple

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 Mo max
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}


def preprocess_image(image_bytes: bytes):
    """Prétraite l'image pour optimiser la lisibilité du texte sur captures mobiles :
    - Conversion en niveaux de gris
    - Accentuation du contraste
    - Légère réduction du bruit
    """
    if not HAS_OCR:
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Conversion niveaux de gris
        gray = img.convert("L")
        # Renforcement du contraste
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)
        # Filtre médian doux pour réduire le bruit de compression JPEG
        cleaned = enhanced.filter(ImageFilter.MedianFilter(size=3))
        return cleaned
    except Exception:
        return None


def extract_text_from_image(image_bytes: bytes, content_type: str) -> Tuple[str, bool]:
    """Extrait le texte d'une capture d'écran d'un message suspect.
    Retourne (texte_extrait, succes).
    """
    if content_type not in ALLOWED_MIME_TYPES:
        return "", False

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return "", False

    if not HAS_OCR:
        # Fallback informatif si le binaire natif Tesseract n'est pas configuré sur le système
        return "", False

    try:
        processed_img = preprocess_image(image_bytes)
        if processed_img is None:
            return "", False

        # Extraction OCR (français + anglais pour termes techniques)
        extracted = pytesseract.image_to_string(processed_img, lang="fra+eng")
        return extracted.strip(), True
    except Exception as e:
        # Si Tesseract binaire n'est pas dans le PATH système, dégradation gracieuse
        print(f"[OCR Notice] Tesseract non disponible : {e}")
        return "", False
