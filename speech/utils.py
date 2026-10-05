import re
import os

# Devanagari to Roman mapping
DEVANAGARI_TO_ROMAN = {
    # Vowels
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah',
    # Matras (vowel signs)
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ः': 'h',
    # Consonants
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'n',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy',
    # Additional consonants / Nuqta characters
    'क़': 'q', 'ख़': 'kh', 'ग़': 'g', 'ज़': 'z', 'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f',
    # Halant
    '्': '',
}

CONSONANTS = {
    'क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ',
    'ट', 'ठ', 'ड', 'ढ', 'ण', 'त', 'थ', 'द', 'ध', 'न',
    'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व', 'श', 'ष', 'स', 'ह',
    'क्ष', 'त्र', 'ज्ञ', 'क़', 'ख़', 'ग़', 'ज़', 'ड़', 'ढ़', 'फ़'
}

MATRAS = {'ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', 'ं', 'ः', '्'}

def transliterate_word(word: str) -> str:
    if not re.search(r'[\u0900-\u097F]', word):
        return word
        
    result = []
    i = 0
    n = len(word)
    while i < n:
        char = word[i]
        
        # Handle Nuqta combinations (e.g. ड + ़ = ड़)
        if i + 1 < n and word[i+1] == '़':
            combined = char + '़'
            if combined in DEVANAGARI_TO_ROMAN:
                char = combined
                i += 1
        
        if char in DEVANAGARI_TO_ROMAN:
            val = DEVANAGARI_TO_ROMAN[char]
            
            if char in CONSONANTS:
                # Check next character
                next_char = word[i+1] if i + 1 < n else None
                # If next character is a matra or halant, do not add inherent 'a'
                if next_char and (next_char in MATRAS or next_char == '़'):
                    result.append(val)
                else:
                    # If it's the last character of the word, do not add inherent 'a'
                    if i + 1 == n and len(word) > 1:
                        result.append(val)
                    else:
                        result.append(val + 'a')
            else:
                result.append(val)
        else:
            result.append(char)
        i += 1
        
    return "".join(result)

def transliterate_text(text: str) -> str:
    """Converts Devanagari Hindi text to Roman Hindi (transliteration)."""
    words = re.split(r'(\s+)', text)
    transliterated_words = [transliterate_word(w) for w in words]
    return "".join(transliterated_words)

def is_valid_audio(file_path: str) -> bool:
    """
    Validates whether an audio file exists, has non-zero size, matches file extension,
    and can be decoded without errors.
    """
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        if os.path.getsize(file_path) <= 0:
            return False

        with open(file_path, "rb") as f:
            header = f.read(12)

        if len(header) < 4:
            return False

        # Disallow WAV (RIFF) header with .mp3 extension as pygame drmp3 decoder fails on it
        if header.startswith(b"RIFF") and file_path.lower().endswith(".mp3"):
            return False

        import pygame
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.unload()
            except Exception:
                return False

        return True
    except Exception:
        return False

