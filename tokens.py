"""Zero-Trust Capability Token Scoping for Axioma Lexis G2 [L1-G2-004]."""

from typing import Dict, List, Optional
import hashlib
import hmac
import time
import uuid


class LexisCapabilityAuthority:
    """Manages scoped HMAC-signed capability tokens for deck mutations."""

    def __init__(self, secret_key: str = "axioma_lexis_g2_secret_key"):
        self.secret_key = secret_key.encode("utf-8")
        self.active_tokens: Dict[str, Dict] = {}
        self._bootstrap_default_tokens()

    def _bootstrap_default_tokens(self) -> None:
        """Issues default scoped tokens for mobile learner and daemon."""
        self.issue_token(
            persona="Mobile_Learner",
            allowed_actions=["review_card", "undo_review", "capture_word", "update_card", "delete_card", "read_deck"],
        )
        self.issue_token(
            persona="Lexis_Daemon",
            allowed_actions=["audit_schedule", "dispatch_curiosity_notification", "read_deck"],
        )
        self.issue_token(
            persona="System_Architect",
            allowed_actions=["import_deck", "export_deck", "repair_deck", "mutate_settings"],
        )

    def issue_token(self, persona: str, allowed_actions: List[str], ttl_seconds: int = 86400) -> str:
        """Issues an introspectable HMAC-signed capability token."""
        token_id = f"cap_lex_{uuid.uuid4().hex[:8]}"
        expires_at = time.time() + ttl_seconds
        payload = f"{token_id}:{persona}:{sorted(allowed_actions)}:{expires_at}"
        signature = hmac.new(self.secret_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        self.active_tokens[token_id] = {
            "token_id": token_id,
            "persona": persona,
            "allowed_actions": allowed_actions,
            "expires_at": expires_at,
            "signature": signature,
        }
        return token_id

    def verify_action(self, token_id: Optional[str], action: str) -> bool:
        """Verifies if token has permission to execute the requested action."""
        if not token_id or token_id not in self.active_tokens:
            return False

        token_record = self.active_tokens[token_id]
        if time.time() > token_record["expires_at"]:
            return False

        return action in token_record["allowed_actions"]
