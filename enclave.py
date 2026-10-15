"""Ephemeral Self-Healing Enclave for Flashcard Decks [L1-G2-002].

Provides bounded multi-pass auto-repair (k <= 3) for corrupted card schemas:
- Pass 1: Type coercion and missing essential field synthesis
- Pass 2: Interval normalization and tier range bounds clamping
- Pass 3: Formal invariant validation and blast containment
"""

from typing import Any, Dict, List, Tuple
import time

from .types import CardTier, WordCard


class DeckHealingEnclave:
    """Ephemeral auto-repair enclave for resilient deck persistence."""

    def __init__(self, max_passes: int = 3):
        self.max_passes = max_passes
        self.total_incidents_healed = 0
        self.quarantine_log: List[Dict[str, Any]] = []

    def heal_raw_card(self, raw_data: Dict[str, Any]) -> Tuple[bool, WordCard, List[str]]:
        """Repairs a single malformed card dict in up to 3 passes."""
        passes_taken: List[str] = []
        data = dict(raw_data)

        # PASS 1: Essential Field Coercion
        if not data.get("word") or not isinstance(data.get("word"), str):
            data["word"] = "unnamed_term"
            passes_taken.append("Pass 1: Coerced invalid word identifier to fallback string.")

        if "definition" not in data or not data["definition"]:
            data["definition"] = f"Meaning of {data['word']}."
            passes_taken.append("Pass 1: Synthesized missing definition.")

        if "ipa" not in data or not data["ipa"]:
            data["ipa"] = f"/{data['word']}/"
            passes_taken.append("Pass 1: Generated fallback phonetic IPA.")

        if "context_sentence" not in data or not data["context_sentence"]:
            data["context_sentence"] = f"Sample usage of {data['word']}."
            passes_taken.append("Pass 1: Synthesized missing context sentence.")

        # PASS 2: Numeric Bounds & Tier Clamping
        try:
            tier_val = int(data.get("tier", 0))
            if tier_val < 0 or tier_val > 6:
                data["tier"] = max(0, min(6, tier_val))
                passes_taken.append(f"Pass 2: Clamped out-of-bounds tier {tier_val} into [0..6].")
        except (ValueError, TypeError):
            data["tier"] = CardTier.TIER_0_ACQUISITION.value
            passes_taken.append("Pass 2: Coerced non-integer tier to TIER_0.")

        now = time.time()
        try:
            due_val = float(data.get("due_timestamp", now))
            data["due_timestamp"] = due_val
        except (ValueError, TypeError):
            data["due_timestamp"] = now
            passes_taken.append("Pass 2: Re-anchored corrupted timestamp to current epoch.")

        # PASS 3: Invariant Closure & WordCard Materialization
        try:
            repaired_card = WordCard.from_dict(data)
            passes_taken.append("Pass 3: Successfully certified invariant schema.")
            if passes_taken:
                self.total_incidents_healed += 1
            return True, repaired_card, passes_taken
        except Exception as e:
            self.quarantine_log.append({"raw": raw_data, "error": str(e), "timestamp": now})
            # Fallback to pristine minimal card
            fallback = WordCard(
                word=str(raw_data.get("word", "recovered_term")),
                definition="Recovered from corrupted state.",
                ipa="/recovered/",
                context_sentence="Card recovered via enclave.",
            )
            return False, fallback, passes_taken + [f"Pass 3 Exception: {e}"]
