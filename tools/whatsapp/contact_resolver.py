import os
import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from tools.whatsapp.whatsapp_models import WhatsAppContact, ContactResolutionStatus, mask_phone_number

logger = logging.getLogger("ContactResolver")

HONORIFICS = ["sir", "ji", "bhai", "bhaiya", "didi", "madam", "mam", "boss"]
ACTION_VERBS = ["ko", "pe", "par", "message", "msg", "text", "bhejo", "karo", "send", "de", "do", "ki", "ka", "whatsapp"]

def normalize_contact_name(raw_input: str) -> Tuple[str, str]:
    """
    Normalizes contact name queries by stripping honorifics ('sir', 'ji', 'bhai') and command words.
    Returns (original_query, normalized_query_token).
    Does NOT modify stored contact names.
    """
    if not raw_input or not raw_input.strip():
        return "", ""

    clean = raw_input.strip()
    q_lower = clean.lower()

    # Step 1: Remove lead-in conversational commands
    q_lower = re.sub(
        r"(?i)^(?:jarvis,?\s*)?(?:ek\s+kam\s+karo\s*)?(?:whatsapp\s*(?:open\s+karo|kholo|pe|par|me|app)?\s*(?:or|aur|and)?\s*)?",
        "",
        q_lower
    ).strip()

    # Step 2: Extract recipient portion before "ko", "par", "pe", "message", etc.
    match_ko = re.search(r"^(.+?)\s+\bko\b(?:\s+(?:message|msg|text|hello|bhejo|karo|send|de|do|ki|ka\s+message))?", q_lower)
    if match_ko:
        recipient_part = match_ko.group(1).strip()
    else:
        # Fallback: strip command verbs at end
        recipient_part = re.sub(r"\b(?:ko|message|msg|bhejo|karo|send|de|do|ki|ka\s+message)\b.*$", "", q_lower).strip()

    if not recipient_part:
        recipient_part = q_lower

    original_query = recipient_part

    # Step 3: Strip honorifics and prepositional words from recipient_part for normalized matching
    tokens = recipient_part.split()
    norm_tokens = []
    for t in tokens:
        t_clean = t.strip().lower()
        if t_clean not in HONORIFICS and t_clean not in ["ko", "pe", "par", "ko:"]:
            norm_tokens.append(t_clean)

    normalized_token = " ".join(norm_tokens) if norm_tokens else recipient_part.lower()

    return original_query, normalized_token


class ContactResolutionResult:
    def __init__(
        self,
        status: ContactResolutionStatus = ContactResolutionStatus.SUCCESS,
        query: str = "",
        normalized_query: str = "",
        resolved_name: str = "",
        phone_number: str = "",
        confidence: float = 0.0,
        contact: Optional[WhatsAppContact] = None,
        matching_contacts: Optional[List[WhatsAppContact]] = None,
        message: str = "",
        source: str = "actual_whatsapp_provider",
        resolution_method: str = "EXACT",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.status = status if isinstance(status, ContactResolutionStatus) else ContactResolutionStatus(status)
        self.success = (self.status == ContactResolutionStatus.SUCCESS)
        self.query = query
        self.normalized_query = normalized_query
        self.contact = contact
        self.resolved_name = resolved_name or (contact.display_name if contact else "")
        self.phone_number = phone_number or (contact.phone_number_masked if contact else "")
        self.confidence = confidence
        self.is_ambiguous = (self.status == ContactResolutionStatus.AMBIGUOUS)
        self.matching_contacts = matching_contacts or []
        self.message = message
        self.source = source
        self.resolution_method = resolution_method
        self.error_code = error_code or (self.status.value if not self.success else None)
        self.error_message = error_message or (message if not self.success else None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "query": self.query,
            "normalized_query": self.normalized_query,
            "resolved_name": self.resolved_name,
            "phone_number": self.phone_number,
            "confidence": self.confidence,
            "contact": self.contact.to_dict() if self.contact else None,
            "is_ambiguous": self.is_ambiguous,
            "message": self.message,
            "source": self.source,
            "resolution_method": self.resolution_method,
            "error_code": self.error_code,
            "error_message": self.error_message
        }


class ContactResolver:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ContactResolver()
        return cls._instance

    def __init__(self):
        self._contacts: Dict[str, WhatsAppContact] = {}
        self._storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "whatsapp_contacts.json")
        self._load_contacts()

    def _load_contacts(self):
        """Loads contacts from persistent storage or initializes default initial contacts."""
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        c = WhatsAppContact(
                            contact_id=item["contact_id"],
                            display_name=item["display_name"],
                            phone_number_masked=item["phone_number_masked"],
                            raw_phone_unmasked=item.get("raw_phone_unmasked", "")
                        )
                        self._contacts[c.contact_id] = c
                    if self._contacts:
                        return
        except Exception as e:
            logger.warning(f"Failed to load WhatsApp contacts file: {e}")

        self._init_default_contacts()

    def _init_default_contacts(self):
        defaults = [
            WhatsAppContact(contact_id="cnt_000", display_name="Rishabh", phone_number_masked=mask_phone_number("+919899887766"), raw_phone_unmasked="+919899887766"),
            WhatsAppContact(contact_id="cnt_001", display_name="Rahul Sharma", phone_number_masked=mask_phone_number("+919876543210"), raw_phone_unmasked="+919876543210"),
            WhatsAppContact(contact_id="cnt_002", display_name="Rahul Verma", phone_number_masked=mask_phone_number("+919812345678"), raw_phone_unmasked="+919812345678"),
            WhatsAppContact(contact_id="cnt_003", display_name="Mom", phone_number_masked=mask_phone_number("+919988776655"), raw_phone_unmasked="+919988776655"),
            WhatsAppContact(contact_id="cnt_004", display_name="John Doe", phone_number_masked=mask_phone_number("+14155552671"), raw_phone_unmasked="+14155552671"),
            WhatsAppContact(contact_id="cnt_005", display_name="Alex", phone_number_masked=mask_phone_number("+14155559988"), raw_phone_unmasked="+14155559988"),
            WhatsAppContact(contact_id="cnt_006", display_name="Vanshu", phone_number_masked=mask_phone_number("+919876500112"), raw_phone_unmasked="+919876500112"),
            WhatsAppContact(contact_id="cnt_007", display_name="Mittar", phone_number_masked=mask_phone_number("+919876500113"), raw_phone_unmasked="+919876500113"),
        ]
        for c in defaults:
            self._contacts[c.contact_id] = c
        self._save_contacts()

    def _save_contacts(self):
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = [
                {
                    "contact_id": c.contact_id,
                    "display_name": c.display_name,
                    "phone_number_masked": c.phone_number_masked,
                    "raw_phone_unmasked": c.raw_phone_unmasked
                } for c in self._contacts.values()
            ]
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save WhatsApp contacts file: {e}")

    def register_contact(self, contact: WhatsAppContact):
        self._contacts[contact.contact_id] = contact
        self._save_contacts()

    def resolve_contact(self, query_name: str, computer_control_fallback: bool = True) -> ContactResolutionResult:
        if not query_name or not query_name.strip():
            return ContactResolutionResult(
                status=ContactResolutionStatus.CONTACT_NOT_FOUND,
                query=query_name,
                message="Boss, contact name identify nahi ho paaya."
            )

        orig_query, norm_token = normalize_contact_name(query_name)

        if not norm_token:
            return ContactResolutionResult(
                status=ContactResolutionStatus.CONTACT_NOT_FOUND,
                query=query_name,
                normalized_query="",
                message="Boss, contact name identify nahi ho paaya."
            )

        # ─── Stage 1: Exact Match ─────────────────────────────────────────────
        exact_matches = []
        for c in self._contacts.values():
            disp_lower = c.display_name.lower()
            if disp_lower == orig_query.lower() or disp_lower == norm_token:
                exact_matches.append(c)

        if len(exact_matches) == 1:
            return ContactResolutionResult(
                status=ContactResolutionStatus.SUCCESS,
                query=orig_query,
                normalized_query=norm_token,
                resolved_name=exact_matches[0].display_name,
                phone_number=exact_matches[0].phone_number_masked,
                confidence=1.0,
                contact=exact_matches[0],
                source="actual_whatsapp_provider",
                resolution_method="EXACT",
                message=f"Resolved contact: {exact_matches[0].display_name}"
            )

        if len(exact_matches) > 1:
            names = [f"'{c.display_name}' ({c.phone_number_masked})" for c in exact_matches]
            return ContactResolutionResult(
                status=ContactResolutionStatus.AMBIGUOUS,
                query=orig_query,
                normalized_query=norm_token,
                confidence=0.50,
                matching_contacts=exact_matches,
                source="actual_whatsapp_provider",
                resolution_method="EXACT_AMBIGUOUS",
                message=f"Boss, '{query_name}' ke {len(exact_matches)} contacts mile hain: {', '.join(names)}. Kaunsa contact confirm karu?"
            )

        # ─── Stage 2: Normalized / Honorific Match ───────────────────────────
        normalized_matches = []
        for c in self._contacts.values():
            _, c_norm = normalize_contact_name(c.display_name)
            disp_lower = c.display_name.lower()
            if norm_token == c_norm or norm_token in c_norm or c_norm in norm_token:
                normalized_matches.append(c)
            elif any(part == norm_token for part in disp_lower.split()):
                normalized_matches.append(c)

        unique_matches = list({c.contact_id: c for c in normalized_matches}.values())

        if len(unique_matches) == 1:
            return ContactResolutionResult(
                status=ContactResolutionStatus.SUCCESS,
                query=orig_query,
                normalized_query=norm_token,
                resolved_name=unique_matches[0].display_name,
                phone_number=unique_matches[0].phone_number_masked,
                confidence=0.94,
                contact=unique_matches[0],
                source="actual_whatsapp_provider",
                resolution_method="NORMALIZED",
                message=f"Resolved contact: {unique_matches[0].display_name}"
            )

        if len(unique_matches) > 1:
            names = [f"'{c.display_name}' ({c.phone_number_masked})" for c in unique_matches]
            return ContactResolutionResult(
                status=ContactResolutionStatus.AMBIGUOUS,
                query=orig_query,
                normalized_query=norm_token,
                confidence=0.50,
                matching_contacts=unique_matches,
                source="actual_whatsapp_provider",
                resolution_method="NORMALIZED_AMBIGUOUS",
                message=f"Boss, '{query_name}' ke {len(unique_matches)} contacts mile hain: {', '.join(names)}. Kaunsa contact confirm karu?"
            )

        # ─── Stage 3: Computer Control / Vision OCR Resolution ───────────────
        if computer_control_fallback:
            try:
                from tools.whatsapp.whatsapp_provider import WhatsAppWebComputerControlProvider
                vision_res = WhatsAppWebComputerControlProvider.resolve_contact_via_ui(norm_token)
                if vision_res and vision_res.status not in [ContactResolutionStatus.CONTACT_NOT_FOUND, ContactResolutionStatus.NOT_FOUND]:
                    if vision_res.success and vision_res.contact:
                        self.register_contact(vision_res.contact)
                    return vision_res
            except Exception as e:
                logger.warning(f"Computer control contact resolution fallback error: {e}")

        return ContactResolutionResult(
            status=ContactResolutionStatus.CONTACT_NOT_FOUND,
            query=orig_query,
            normalized_query=norm_token,
            confidence=0.0,
            source="actual_whatsapp_provider",
            resolution_method="NONE",
            error_code="CONTACT_NOT_FOUND",
            error_message=f"Boss, mujhe '{orig_query}' naam ka WhatsApp contact nahi mila.",
            message=f"Boss, mujhe '{orig_query}' naam ka WhatsApp contact nahi mila."
        )

    def get_all_contacts(self) -> List[WhatsAppContact]:
        return list(self._contacts.values())
