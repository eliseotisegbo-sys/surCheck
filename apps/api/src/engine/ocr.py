"""Module OCR et prétraitement d'images de captures d'écran pour SûrCheck AI.
Conforme aux sections 25 et 34 du Cahier des Charges :
- Optimisé pour les captures compressées (WhatsApp, SMS)
- Suppression immédiate des données brutes en mémoire après extraction
- Validation stricte de sécurité (taille max, types MIME)
- Correction des confusions OCR fréquentes
- Score de confiance basé sur les métriques Tesseract
"""

import io
import re
from typing import Tuple, Dict

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
    from pytesseract import Output
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 Mo max
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

# Mapping des confusions OCR fréquentes (captures compressées WhatsApp)
OCR_CONFUSION_CORRECTIONS = {
    "O": "0",  # Lettre O → chiffre 0 dans contexte numérique
    "l": "1",  # Lettre l minuscule → chiffre 1
    "I": "1",  # Lettre I majuscule → chiffre 1
    "S": "5",  # Lettre S → chiffre 5 dans contexte numérique
    "B": "8",  # Lettre B → chiffre 8
}

# Termes du lexique critique pour validation des corrections
CRITICAL_TERMS_FOR_CORRECTION = [
    "code", "secret", "pin", "frais", "urgent", "caution",
    "transfert", "momo", "moov", "mtn", "gagné", "tirage"
]


def preprocess_image(image_bytes: bytes):
    """Prétraite l'image pour optimiser la lisibilité du texte sur captures mobiles :
    - Conversion en niveaux de gris
    - Accentuation du contraste
    - Légère réduction du bruit
    - Augmentation de la netteté
    """
    if not HAS_OCR:
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Redimensionner si trop petite (améliore OCR)
        width, height = img.size
        if width < 800:
            scale_factor = 800 / width
            new_size = (int(width * scale_factor), int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Conversion niveaux de gris
        gray = img.convert("L")
        
        # Renforcement du contraste
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.0)
        
        # Augmentation de la netteté
        sharpener = ImageEnhance.Sharpness(enhanced)
        sharpened = sharpener.enhance(1.5)
        
        # Filtre médian doux pour réduire le bruit de compression JPEG
        cleaned = sharpened.filter(ImageFilter.MedianFilter(size=3))
        
        return cleaned
    except Exception:
        return None


def correct_ocr_confusions(text: str) -> str:
    """Corrige les confusions OCR fréquentes sur captures compressées.
    
    Applique les corrections uniquement si le résultat produit un terme
    du lexique critique connu.
    
    Args:
        text: Texte brut extrait par OCR
        
    Returns:
        Texte avec corrections appliquées
    """
    corrected_text = text
    words = text.split()
    
    for i, word in enumerate(words):
        # Tester des corrections potentielles
        for char_from, char_to in OCR_CONFUSION_CORRECTIONS.items():
            if char_from in word:
                # Essayer la correction
                corrected_word = word.replace(char_from, char_to)
                corrected_lower = corrected_word.lower()
                
                # Vérifier si la correction produit un terme critique
                for critical_term in CRITICAL_TERMS_FOR_CORRECTION:
                    if critical_term in corrected_lower:
                        # Appliquer la correction
                        words[i] = corrected_word
                        break
    
    return " ".join(words)


def reglue_spaced_text(text: str) -> str:
    """Recolle le texte OCR fragmenté (mots coupés).
    
    Tesseract peut produire "cod e secr et" au lieu de "code secret".
    Cette fonction applique la même logique que normalizer._rejoin_spaced_letters.
    
    Args:
        text: Texte OCR brut
        
    Returns:
        Texte avec mots recollés
    """
    # Recollement simple : supprimer espaces entre lettres isolées
    # Pattern: lettre + espace + lettre isolée répété
    pattern = r'\b([a-zA-Z])\s+([a-zA-Z])\b'
    
    previous = ""
    max_iterations = 5
    iteration = 0
    
    while previous != text and iteration < max_iterations:
        previous = text
        text = re.sub(pattern, r'\1\2', text)
        iteration += 1
    
    return text


def calculate_confidence_score(ocr_data: Dict) -> float:
    """Calcule un score de confiance basé sur les métriques Tesseract.
    
    Args:
        ocr_data: Données détaillées de pytesseract.image_to_data
        
    Returns:
        Score de confiance moyen (0.0 à 1.0)
    """
    confidences = []
    
    for i, conf in enumerate(ocr_data.get("conf", [])):
        # Ignorer les valeurs de confiance invalides (-1)
        if conf != -1:
            confidences.append(float(conf))
    
    if not confidences:
        return 0.5  # Confiance moyenne par défaut
    
    # Moyenne des confiances
    avg_confidence = sum(confidences) / len(confidences)
    
    # Normaliser entre 0 et 1 (Tesseract retourne 0-100)
    return min(max(avg_confidence / 100.0, 0.0), 1.0)


def extract_text_from_image(image_bytes: bytes, content_type: str) -> Tuple[str, bool, float]:
    """Extrait le texte d'une capture d'écran d'un message suspect.
    
    Améliorations:
    - Correction confusions OCR (0/O, 1/l/I, 5/S, 8/B)
    - Recollement texte fragmenté
    - Score de confiance basé sur métriques Tesseract
    
    Returns:
        Tuple (texte_extrait, succes, score_confiance)
        score_confiance entre 0.0 et 1.0
    """
    if content_type not in ALLOWED_MIME_TYPES:
        return "", False, 0.0

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return "", False, 0.0

    if not HAS_OCR:
        # Fallback informatif si le binaire natif Tesseract n'est pas configuré sur le système
        return "", False, 0.0

    try:
        processed_img = preprocess_image(image_bytes)
        if processed_img is None:
            return "", False, 0.0

        # Extraction OCR détaillée avec métriques de confiance
        try:
            # Essayer d'obtenir les données détaillées pour le score de confiance
            ocr_data = pytesseract.image_to_data(
                processed_img, 
                lang="fra+eng",
                output_type=Output.DICT
            )
            
            # Extraire le texte complet
            extracted = pytesseract.image_to_string(processed_img, lang="fra+eng")
            
            # Calculer le score de confiance
            confidence = calculate_confidence_score(ocr_data)
            
        except Exception:
            # Repli sur extraction simple sans métriques détaillées
            extracted = pytesseract.image_to_string(processed_img, lang="fra+eng")
            confidence = 0.7  # Confiance moyenne par défaut
        
        # Appliquer les corrections
        extracted = extracted.strip()
        extracted = reglue_spaced_text(extracted)
        extracted = correct_ocr_confusions(extracted)
        
        return extracted, True, confidence
        
    except Exception as e:
        # Si Tesseract binaire n'est pas dans le PATH système, dégradation gracieuse
        print(f"[OCR Notice] Tesseract non disponible : {e}")
        return "", False, 0.0
