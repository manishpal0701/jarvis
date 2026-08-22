import re

class ResponseFormatter:
    @staticmethod
    def format_for_speech(text: str) -> str:
        """Converts technical/console text into natural conversational spoken text."""
        if not text:
            return ""
            
        # 1. Handle structured key-value pairs (e.g., "Trend: Bullish\nConfidence: 74%")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        kv_pairs = []
        for line in lines:
            match = re.match(r'^([\w\s\-]+):\s*(.+)$', line)
            if match:
                key, val = match.groups()
                kv_pairs.append((key.strip(), val.strip()))
                
        if len(kv_pairs) >= 2:
            # Convert to a conversational sentence
            parts = []
            for k, v in kv_pairs:
                # Clean key and value
                k_clean = k.lower().replace('-', ' ').replace('_', ' ')
                parts.append(f"{k_clean} is {v}")
            spoken_text = "Boss, " + ", and ".join(parts) + "."
        else:
            spoken_text = text
            
        # 2. Replace technical symbols
        replacements = {
            "%": " percent",
            "$": " dollars",
            "&": " and",
            "@": " at",
            "=": " equals",
            "+": " plus",
            "approx.": "approximately",
            "approx": "approximately",
            "vs": "versus",
            "min": "minutes",
            "sec": "seconds",
            "hr": "hours",
            "temp": "temperature",
            "vol": "volume",
            "qty": "quantity",
            "info": "information",
            "config": "configuration",
            "err": "error",
            "msg": "message",
        }
        
        for sym, word in replacements.items():
            # Use regex to replace symbols with word boundaries where appropriate
            if sym.isalpha():
                spoken_text = re.sub(rf'\b{sym}\b', word, spoken_text, flags=re.IGNORECASE)
            else:
                spoken_text = spoken_text.replace(sym, word)
                
        # 3. Clean up multiple spaces
        spoken_text = re.sub(r'\s+', ' ', spoken_text).strip()
        
        return spoken_text
