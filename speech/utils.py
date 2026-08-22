import re

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
