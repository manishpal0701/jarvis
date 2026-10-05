import os
import sys
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set

@dataclass
class WhatsAppMedia:
    media_id: str
    filename: str
    mime_type: str
    local_path: str
    caption: str = ""
    role: str = "general"
    client_association: str = ""
    provenance: str = "CLIENT_PROVIDED"  # CLIENT_PROVIDED, OFFICIAL_SOURCE, GENERATED, SYSTEM

@dataclass
class WhatsAppMessage:
    message_id: str
    sender_id: str
    sender_name: str
    timestamp: str
    text: str
    media: List[WhatsAppMedia] = field(default_factory=list)

class BaseWhatsAppAdapter:
    """
    Base WhatsApp Adapter Interface supporting provider decoupling and message deduplication.
    """
    def __init__(self):
        self._processed_message_ids: Set[str] = set()

    def is_duplicate_message(self, message_id: str) -> bool:
        if not message_id:
            return False
        if message_id in self._processed_message_ids:
            return True
        self._processed_message_ids.add(message_id)
        return False

    def fetch_messages(self, client_identifier: str) -> List[WhatsAppMessage]:
        raise NotImplementedError

    def fetch_media(self, client_identifier: str) -> List[WhatsAppMedia]:
        raise NotImplementedError

class MockWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    In-memory / Mock WhatsApp Adapter for unit testing and offline development.
    """
    def __init__(self):
        super().__init__()
        self._message_feeds: Dict[str, List[WhatsAppMessage]] = {}

    def register_client_feed(self, client_identifier: str, messages: List[WhatsAppMessage]):
        clean_key = client_identifier.lower().strip()
        self._message_feeds[clean_key] = messages
        print(f"[WHATSAPP_CONNECTION] Provider=Mock active. Registered {len(messages)} messages for client '{client_identifier}'", flush=True)

    def fetch_messages(self, client_identifier: str) -> List[WhatsAppMessage]:
        clean_key = client_identifier.lower().strip()
        if clean_key in self._message_feeds:
            msgs = self._message_feeds[clean_key]
            print(f"[WHATSAPP_MESSAGES_FETCHED] count={len(msgs)} client={client_identifier}", flush=True)
            return msgs

        for k, msgs in self._message_feeds.items():
            if k in clean_key or clean_key in k:
                print(f"[WHATSAPP_MESSAGES_FETCHED] count={len(msgs)} client={client_identifier} (fuzzy '{k}')", flush=True)
                return msgs

        print(f"[WHATSAPP_MESSAGES_FETCHED] count=0 client={client_identifier}", flush=True)
        return []

    def fetch_media(self, client_identifier: str) -> List[WhatsAppMedia]:
        msgs = self.fetch_messages(client_identifier)
        media_list = []
        for msg in msgs:
            media_list.extend(msg.media)
        print(f"[WHATSAPP_MEDIA_FETCHED] count={len(media_list)} client={client_identifier}", flush=True)
        return media_list

class MetaWhatsAppCloudAdapter(BaseWhatsAppAdapter):
    """
    Production Meta WhatsApp Business Cloud API Adapter.
    Communicates with Meta Graph API endpoints to download binary media,
    normalize webhook payloads, and update client brief stores.
    """
    def __init__(self):
        super().__init__()
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v20.0").strip()
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
        self._client_messages: Dict[str, List[WhatsAppMessage]] = {}

    def fetch_messages(self, client_identifier: str) -> List[WhatsAppMessage]:
        clean_key = client_identifier.lower().strip()
        if clean_key in self._client_messages:
            return self._client_messages[clean_key]
        for k, msgs in self._client_messages.items():
            if k in clean_key or clean_key in k:
                return msgs
        return []

    def fetch_media(self, client_identifier: str) -> List[WhatsAppMedia]:
        msgs = self.fetch_messages(client_identifier)
        res = []
        for m in msgs:
            res.extend(m.media)
        return res

    def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Retrieves temporary media download URL from Meta Graph API.
        """
        if not self.access_token or not media_id:
            print("[WHATSAPP_MEDIA_METADATA] Missing credentials or media_id", flush=True)
            return None

        url = f"https://graph.facebook.com/{self.api_version}/{media_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.access_token}"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                media_url = data.get("url")
                print(f"[WHATSAPP_MEDIA_METADATA] Fetched media_id={media_id}", flush=True)
                return media_url
        except Exception as e:
            print(f"[WHATSAPP_MEDIA_ERR] Error fetching metadata for {media_id}: {e}", flush=True)
            return None

    def download_media(self, media_id: str, dest_dir: str, filename: str) -> Optional[str]:
        """
        Downloads binary media file securely to local dest_dir without logging access tokens.
        Sanitizes filename to prevent directory traversal attacks.
        """
        media_url = self.get_media_url(media_id)
        if not media_url:
            return None

        clean_filename = os.path.basename(filename).replace(" ", "_")
        os.makedirs(dest_dir, exist_ok=True)
        local_path = os.path.join(dest_dir, clean_filename)

        req = urllib.request.Request(media_url, headers={"Authorization": f"Bearer {self.access_token}"})
        try:
            with urllib.request.urlopen(req) as resp, open(local_path, "wb") as f:
                f.write(resp.read())
            print(f"[WHATSAPP_MEDIA_DOWNLOAD] PASS media_id={media_id} -> {local_path}", flush=True)
            return local_path
        except Exception as e:
            print(f"[WHATSAPP_MEDIA_DOWNLOAD_ERR] {e}", flush=True)
            return None

    def process_webhook_payload(self, payload: Dict[str, Any]) -> List[WhatsAppMessage]:
        """
        Parses Meta WhatsApp Business Cloud API webhook event JSON payload.
        Idempotency logic prevents duplicate processing of retried message events.
        """
        normalized_messages = []
        entries = payload.get("entry", [])

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                contacts = value.get("contacts", [])
                sender_name = contacts[0].get("profile", {}).get("name", "Client") if contacts else "Client"

                messages = value.get("messages", [])
                for msg in messages:
                    msg_id = msg.get("id", "")
                    if self.is_duplicate_message(msg_id):
                        print(f"[WHATSAPP_MESSAGE] Duplicate message_id={msg_id} ignored (IDEMPOTENT)", flush=True)
                        continue

                    sender_id = msg.get("from", "unknown_sender")
                    msg_type = msg.get("type", "text")
                    timestamp = str(msg.get("timestamp", ""))

                    text_content = ""
                    media_items = []

                    if msg_type == "text":
                        text_content = msg.get("text", {}).get("body", "")
                    elif msg_type in ["image", "document", "video", "audio"]:
                        media_obj = msg.get(msg_type, {})
                        m_id = media_obj.get("id", "")
                        caption = media_obj.get("caption", "")
                        mime_type = media_obj.get("mime_type", "image/jpeg")

                        filename = f"{msg_type}_{m_id[:8]}.jpg"
                        if msg_type == "document" and "filename" in media_obj:
                            filename = media_obj["filename"]

                        media_items.append(WhatsAppMedia(
                            media_id=m_id,
                            filename=filename,
                            mime_type=mime_type,
                            local_path="",
                            caption=caption,
                            role="general",
                            client_association=sender_name,
                            provenance="CLIENT_PROVIDED"
                        ))

                    wa_msg = WhatsAppMessage(
                        message_id=msg_id,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        timestamp=timestamp,
                        text=text_content,
                        media=media_items
                    )
                    normalized_messages.append(wa_msg)

                    # Store message thread
                    key = sender_name.lower().strip()
                    if key not in self._client_messages:
                        self._client_messages[key] = []
                    self._client_messages[key].append(wa_msg)
                    print(f"[WHATSAPP_MESSAGE] normalized id={msg_id} type={msg_type} sender={sender_name}", flush=True)

        return normalized_messages


class WhatsAppAdapter:
    """
    Adapter Factory providing transparent access to either MetaWhatsAppCloudAdapter or MockWhatsAppAdapter.
    """
    _instance = None

    @classmethod
    def get_instance(cls) -> BaseWhatsAppAdapter:
        if cls._instance is None:
            if os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip():
                cls._instance = MetaWhatsAppCloudAdapter()
                print("[WHATSAPP_CONNECTION] Active Provider: MetaWhatsAppCloudAdapter (LIVE API)", flush=True)
            else:
                cls._instance = MockWhatsAppAdapter()
                print("[WHATSAPP_CONNECTION] Active Provider: MockWhatsAppAdapter (TEST/LOCAL)", flush=True)
        return cls._instance

    @classmethod
    def set_instance(cls, instance: BaseWhatsAppAdapter):
        cls._instance = instance
