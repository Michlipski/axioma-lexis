"""Humane Spaced Repetition Engine for Axioma Lexis G2.

Key Invariants:
1. Humane Step-Back Decay: Struggling cards decay by strictly 1 tier (never reset to 0).
2. Strictly Capped Micro-Sessions: Never shows more than 3-5 cards per session.
3. Functorial Reversibility: 1-tap Undo reverts accidental swipe mis-taps.
"""

from typing import Any, Dict, List, Optional
import copy
import time
import uuid

from .types import (
    CardTier,
    MicroSession,
    ReviewOutcome,
    TIER_INTERVALS_SECONDS,
    WordCard,
)


class HumaneSRSEngine:
    """Spaced repetition algorithm with 1-tier step-back decay and micro-dosing."""

    def __init__(self, micro_batch_size: int = 3):
        self.micro_batch_size = max(3, min(5, micro_batch_size))
        self._rollback_stack: List[Dict[str, Any]] = []

    def schedule_next_due(self, card: WordCard, outcome: ReviewOutcome, current_time: Optional[float] = None) -> WordCard:
        """Computes the next due date and tier based on humane spacing rules."""
        now = current_time or time.time()

        # Preserve snapshot for functorial rollback
        snapshot = {
            "card_id": card.card_id,
            "state": copy.deepcopy(card.to_dict()),
            "timestamp": now,
        }
        self._rollback_stack.append(snapshot)
        # Bounded rollback history (max 50)
        if len(self._rollback_stack) > 50:
            self._rollback_stack.pop(0)

        card.last_reviewed = now
        card.review_count += 1

        if outcome == ReviewOutcome.MASTERED:
            # Advance tier (up to Tier 6)
            card.tier = min(card.tier + 1, CardTier.TIER_6_RETAINED.value)
            card.consecutive_correct += 1
            card.due_timestamp = now + TIER_INTERVALS_SECONDS[card.tier]

        elif outcome == ReviewOutcome.STRUGGLING:
            # 1-Tier Step-Back (never resets mature cards to 0)
            card.tier = max(card.tier - 1, CardTier.TIER_0_ACQUISITION.value)
            card.consecutive_correct = 0
            card.due_timestamp = now + TIER_INTERVALS_SECONDS[card.tier]

        elif outcome == ReviewOutcome.HINT_USED:
            # Recalled after >10s hint: preserve current tier
            card.due_timestamp = now + TIER_INTERVALS_SECONDS[card.tier]
            # Does not increment consecutive_correct

        card.history.append({
            "timestamp": now,
            "outcome": outcome.value,
            "resulting_tier": card.tier,
            "due_timestamp": card.due_timestamp,
        })
        return card

    def rollback_last_action(self, all_cards_map: Dict[str, WordCard]) -> Optional[WordCard]:
        """Restores the prior card state via functorial 1-tap Undo."""
        if not self._rollback_stack:
            return None

        last_snapshot = self._rollback_stack.pop()
        card_id = last_snapshot["card_id"]
        original_state = last_snapshot["state"]

        if card_id in all_cards_map:
            restored = WordCard.from_dict(original_state)
            all_cards_map[card_id] = restored
            return restored
        return None

    def create_micro_session(
        self,
        cards: List[WordCard],
        current_time: Optional[float] = None,
        max_batch: Optional[int] = None,
        allow_early_cram: bool = False,
    ) -> MicroSession:
        """Assembles a bite-sized micro-session of strictly 3 to 5 cards that are due for review."""
        now = current_time or time.time()
        batch_limit = max_batch or self.micro_batch_size
        batch_limit = max(1, min(5, batch_limit))

        # Filter strictly due cards
        due_cards = [c for c in cards if c.due_timestamp <= now]

        # Sort by urgency: lowest tiers first (Tier 0 & Tier 1 most urgent), then oldest due date
        due_cards.sort(key=lambda c: (c.tier, c.due_timestamp))

        selected = due_cards[:batch_limit]

        # If user explicitly requests early practice/cram and no cards are due:
        if not selected and allow_early_cram and cards:
            sorted_cards = sorted(cards, key=lambda c: (c.due_timestamp, c.tier))
            selected = sorted_cards[:batch_limit]

        session = MicroSession(
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            cards=selected,
            start_timestamp=now,
            completed=(len(selected) == 0),
        )
        return session
