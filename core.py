"""Core System Engine for Axioma Lexis G2.

Integrates:
- 1-Tap Single-Word Hydration Engine (Zero manual authoring)
- Humane Step-Back Fibonacci Spaced Repetition (1-tier decay only)
- Capped Micro-Sessions (Strictly 3 to 5 words max per session)
- 10-Second Dwell Patience Window & Zuhandenheit Telemetry
- 3-Pass Ephemeral Deck Healing Enclave
- Zero-Trust Capability Scoping
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import time

from .enclave import DeckHealingEnclave
from .hydrator import WordHydrator
from .phenomenology import LexisPhenomenologyCircuit
from .srs_engine import HumaneSRSEngine
from .tokens import LexisCapabilityAuthority
from .types import (
    CardTier,
    CuriosityNotification,
    MicroSession,
    ReviewOutcome,
    WordCard,
)


class LexisCoreEngine:
    """The central unified runtime engine for Axioma Lexis G2."""

    def __init__(self, data_file: Optional[Path] = None, seed_default: bool = True):
        self.data_file = data_file
        self.cards: Dict[str, WordCard] = {}
        self.active_session: Optional[MicroSession] = None

        # Subsystem bindings
        self.hydrator = WordHydrator()
        self.srs_engine = HumaneSRSEngine(micro_batch_size=3)
        self.phenomenology = LexisPhenomenologyCircuit(dwell_patience_seconds=10.0)
        self.enclave = DeckHealingEnclave(max_passes=3)
        self.capabilities = LexisCapabilityAuthority()

        if seed_default:
            self._seed_curated_lexicon()

        if self.data_file and self.data_file.exists():
            self._load_from_disk()

    def _seed_curated_lexicon(self) -> None:
        """Seeds initial high-signal vocabulary (blank slate with only zuhandenheit)."""
        card = self.hydrator.hydrate_word("zuhandenheit")
        card.card_id = "seed-zuhandenheit"
        card.tier = CardTier.TIER_0_ACQUISITION.value
        card.due_timestamp = time.time() - 100
        self.cards[card.card_id] = card

    def add_word(self, word: str, custom_sentence: Optional[str] = None, token_id: Optional[str] = None) -> WordCard:
        """Captures and auto-hydrates a single word in <1.5s with zero typing friction."""
        if token_id and not self.capabilities.verify_action(token_id, "capture_word"):
            raise PermissionError("Token not authorized for capture_word action.")

        card = self.hydrator.hydrate_word(word, custom_sentence=custom_sentence)
        self.cards[card.card_id] = card
        self._persist_if_configured()
        return card

    def get_or_create_micro_session(self, allow_early_cram: bool = False) -> MicroSession:
        """Retrieves or creates a strictly capped 3-5 word micro-session."""
        if self.active_session and not self.active_session.completed:
            if self.active_session.current_index < len(self.active_session.cards):
                return self.active_session

        card_list = list(self.cards.values())
        session = self.srs_engine.create_micro_session(card_list, max_batch=3, allow_early_cram=allow_early_cram)
        self.active_session = session
        return session

    def answer_active_card(
        self,
        card_id: str,
        outcome: ReviewOutcome,
        dwell_seconds: float = 0.0,
        token_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Answers the active card, applies humane step-back decay, and records dwell telemetry."""
        if token_id and not self.capabilities.verify_action(token_id, "review_card"):
            raise PermissionError("Token not authorized for review_card action.")

        if card_id not in self.cards:
            raise KeyError(f"Card {card_id} not found in collection.")

        card = self.cards[card_id]

        # 1. Evaluate phenomenological flow & 10s dwell patience
        dwell_eval = self.phenomenology.evaluate_dwell(dwell_seconds, undo_tapped=(outcome == ReviewOutcome.UNDO))

        # 2. If user used hint after >10s dwell, adjust outcome to HINT_USED to preserve tier
        effective_outcome = outcome
        if outcome == ReviewOutcome.MASTERED and dwell_eval["should_reveal_hint"]:
            effective_outcome = ReviewOutcome.HINT_USED

        # 3. Schedule next due date via humane step-back Fibonacci
        updated_card = self.srs_engine.schedule_next_due(card, effective_outcome)

        # 4. Advance micro-session progression
        session = self.get_or_create_micro_session()
        session.current_index += 1
        session.session_outcomes.append({
            "card_id": card_id,
            "word": card.word,
            "outcome": effective_outcome.value,
            "dwell_seconds": dwell_seconds,
            "resulting_tier": updated_card.tier,
        })

        if session.current_index >= len(session.cards):
            session.completed = True
            session.end_timestamp = time.time()

        self._persist_if_configured()

        return {
            "success": True,
            "card": updated_card.to_dict(),
            "effective_outcome": effective_outcome.value,
            "dwell_evaluation": dwell_eval,
            "session_completed": session.completed,
            "session_progress": f"{session.current_index} / {len(session.cards)}",
        }

    def undo_last_review(self, token_id: Optional[str] = None) -> Optional[WordCard]:
        """Executes a 1-tap Functorial Rollback (Cmd+Z) for accidental swipe mis-taps."""
        if token_id and not self.capabilities.verify_action(token_id, "undo_review"):
            raise PermissionError("Token not authorized for undo_review action.")

        restored_card = self.srs_engine.rollback_last_action(self.cards)
        if restored_card and self.active_session:
            if self.active_session.current_index > 0:
                self.active_session.current_index -= 1
                if self.active_session.session_outcomes:
                    self.active_session.session_outcomes.pop()
            self.active_session.completed = False

        self._persist_if_configured()
        return restored_card

    def get_curiosity_notification(self) -> CuriosityNotification:
        """Synthesizes a non-intrusive curiosity snippet push notification."""
        now = time.time()
        due_cards = [c for c in self.cards.values() if c.due_timestamp <= now]
        prompt_card = due_cards[0] if due_cards else list(self.cards.values())[0]

        hour = time.localtime(now).tm_hour
        window = "MORNING_0830" if hour < 14 else "EVENING_1930"

        return CuriosityNotification(
            notification_id=f"notif_{int(now)}",
            prompt_word=prompt_card.word,
            context_snippet=f"Do you recall: '{prompt_card.word}'? Tap for a 30s micro-review.",
            cards_due_count=min(len(due_cards), 5),
            scheduled_window=window,
            direct_route="/#direct-review",
            sent_timestamp=now,
        )

    def import_and_heal_deck(self, raw_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Imports cards through the 3-pass self-healing enclave."""
        healed_count = 0
        imported_cards: List[WordCard] = []

        for item in raw_cards:
            success, card, passes = self.enclave.heal_raw_card(item)
            if passes:
                healed_count += 1
            self.cards[card.card_id] = card
            imported_cards.append(card)

        self._persist_if_configured()
        return {
            "total_imported": len(imported_cards),
            "healed_count": healed_count,
            "cards": [c.to_dict() for c in imported_cards],
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """Returns comprehensive real-time system state."""
        now = time.time()
        due_count = sum(1 for c in self.cards.values() if c.due_timestamp <= now)
        session = self.get_or_create_micro_session()

        tier_counts = {t.value: 0 for t in CardTier}
        for c in self.cards.values():
            tier_counts[c.tier] += 1

        return {
            "total_cards": len(self.cards),
            "due_cards_total": due_count,
            "capped_session_slice": min(due_count, 3),
            "tier_distribution": tier_counts,
            "active_session": session.to_dict(),
            "phenomenology": self.phenomenology.get_summary(),
            "enclave_healed_incidents": self.enclave.total_incidents_healed,
        }

    def get_all_cards(self) -> List[WordCard]:
        """Returns all cards in the lexicon ordered by due date and creation."""
        cards = list(self.cards.values())
        cards.sort(key=lambda c: (c.tier, c.due_timestamp))
        return cards

    def update_card(
        self,
        card_id: str,
        updates: Dict[str, Any],
        token_id: Optional[str] = None,
    ) -> WordCard:
        """Updates a card with sanitization and validation through the enclave."""
        if token_id and not self.capabilities.verify_action(token_id, "update_card"):
            raise PermissionError("Token not authorized for update_card action.")

        if card_id not in self.cards:
            raise KeyError(f"Card {card_id} not found in collection.")

        existing = self.cards[card_id]
        raw_dict = existing.to_dict()

        # Apply updates
        for key in ("word", "ipa", "domain", "definition", "context_sentence", "etymology_hint", "tier"):
            if key in updates and updates[key] is not None:
                raw_dict[key] = updates[key]

        # Sanitize and heal through enclave
        success, healed_card, _ = self.enclave.heal_raw_card(raw_dict)
        if not success:
            raise ValueError(f"Failed to validate card updates: {raw_dict}")

        # Preserve card identity
        healed_card.card_id = card_id
        self.cards[card_id] = healed_card
        self._persist_if_configured()
        return healed_card

    def delete_card(self, card_id: str, token_id: Optional[str] = None) -> bool:
        """Deletes a card from the collection and updates active session if needed."""
        if token_id and not self.capabilities.verify_action(token_id, "delete_card"):
            raise PermissionError("Token not authorized for delete_card action.")

        if card_id not in self.cards:
            return False

        del self.cards[card_id]

        # Invalidate active session if it contained the deleted card
        if self.active_session and any(c.card_id == card_id for c in self.active_session.cards):
            self.active_session = None

        self._persist_if_configured()
        return True

    def _persist_if_configured(self) -> None:
        """Persists cards to JSON if path provided."""
        if self.data_file:
            payload = [c.to_dict() for c in self.cards.values()]
            self.data_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_from_disk(self) -> None:
        """Loads cards from JSON through healing enclave."""
        if not self.data_file or not self.data_file.exists():
            return
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self.import_and_heal_deck(raw)
        except Exception:
            pass
