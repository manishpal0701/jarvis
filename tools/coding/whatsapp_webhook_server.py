import os
import sys
import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from tools.coding.whatsapp_adapter import WhatsAppAdapter, MetaWhatsAppCloudAdapter
from tools.coding.client_brief_ingestion import ClientBriefParser, ClientBriefManager

class WhatsAppWebhookHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler for Meta WhatsApp Business Cloud API Webhooks.
    """
    def log_message(self, format, *args):
        # Silence default HTTP server logging output
        return

    def do_GET(self):
        """
        Meta Webhook Verification Endpoint.
        Validates hub.mode, hub.verify_token, and responds with hub.challenge.
        """
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        query_params = parse_qs(parsed_url.query)
        mode = query_params.get("hub.mode", [""])[0]
        token = query_params.get("hub.verify_token", [""])[0]
        challenge = query_params.get("hub.challenge", [""])[0]

        expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()

        print(f"[WHATSAPP_WEBHOOK] Verification request received (mode={mode})", flush=True)

        if mode == "subscribe" and expected_token and token == expected_token:
            print("[WHATSAPP_WEBHOOK] GET Verification PASS", flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(challenge.encode("utf-8"))
        else:
            print(f"[WHATSAPP_WEBHOOK] GET Verification FAIL (token_match={token == expected_token})", flush=True)
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")

    def do_POST(self):
        """
        Meta Webhook Event Listener.
        Validates X-Hub-Signature-256 and normalizes WhatsApp messages into ClientBrief objects.
        """
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
        signature_header = self.headers.get("X-Hub-Signature-256", "")

        # Verify HMAC-SHA256 signature if app_secret is configured
        if app_secret:
            if not signature_header.startswith("sha256="):
                print("[WHATSAPP_SIGNATURE] FAIL (Missing sha256 prefix)", flush=True)
                self.send_response(401)
                self.end_headers()
                return

            expected_sig = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            incoming_sig = signature_header[7:]

            if not hmac.compare_digest(expected_sig, incoming_sig):
                print("[WHATSAPP_SIGNATURE] FAIL (Signature mismatch)", flush=True)
                self.send_response(403)
                self.end_headers()
                return

            print("[WHATSAPP_SIGNATURE] PASS", flush=True)

        try:
            payload = json.loads(body.decode("utf-8"))
            adapter = WhatsAppAdapter.get_instance()

            if isinstance(adapter, MetaWhatsAppCloudAdapter):
                messages = adapter.process_webhook_payload(payload)

                # Update ClientBrief for senders
                for msg in messages:
                    client_msgs = adapter.fetch_messages(msg.sender_name)
                    brief = ClientBriefParser.parse_whatsapp_messages(msg.sender_name, client_msgs)
                    ClientBriefManager.get_instance().register_brief(brief)

            print("[WHATSAPP_WEBHOOK] POST Processed PASS", flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "EVENT_RECEIVED"}).encode("utf-8"))
        except Exception as e:
            print(f"[WHATSAPP_WEBHOOK_ERR] {e}", flush=True)
            self.send_response(500)
            self.end_headers()

def run_webhook_server(port: int = None) -> HTTPServer:
    if port is None:
        port = int(os.getenv("WHATSAPP_WEBHOOK_PORT", "8080"))

    server = HTTPServer(("0.0.0.0", port), WhatsAppWebhookHandler)
    print(f"[WHATSAPP_WEBHOOK_SERVER] Listening on port {port}", flush=True)
    return server
