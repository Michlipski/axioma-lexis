"""Phenomenological Flow & 10s Dwell Patience Circuit [L1-G2-006].

Attunes Lexis to cognitive flow:
- 0.0s to 10.0s: Silent 'Desirable Difficulty' window (Bjork). Effortful recall is respected.
- > 10.0s: Exposes subtle etymological/mnemonic hint affordance to preserve flow.
- Rapid Undo / Swipe Reversals: Detected as friction and logged for transgenerational learning.
"""

from typing import Any, Dict
import time


class LexisPhenomenologyCircuit:
    """Monitors cognitive flow disruption during flashcard interactions."""

    def __init__(self, dwell_patience_seconds: float = 10.0, rupture_threshold: float = 0.45):
        self.dwell_patience_seconds = dwell_patience_seconds
        self.rupture_threshold = rupture_threshold
        self.total_reviews_evaluated = 0
        self.flow_states_count = 0
        self.ruptures_healed_count = 0
        self.undo_reversals_count = 0

    def evaluate_dwell(self, dwell_seconds: float, undo_tapped: bool = False) -> Dict[str, Any]:
        """Evaluates whether card review is transparent flow or cognitive rupture."""
        self.total_reviews_evaluated += 1

        # Calculate Cognitive Rupture Index:
        # Dwell deviation beyond 10s indicates cognitive hesitation / friction
        if dwell_seconds > self.dwell_patience_seconds:
            excess = dwell_seconds - self.dwell_patience_seconds
            dwell_penalty = 0.75 + (0.25 * min(1.0, excess / 5.0))
        else:
            dwell_penalty = 0.0

        undo_penalty = 0.40 if undo_tapped else 0.0

        if undo_tapped:
            self.undo_reversals_count += 1

        r_rupture = min(1.0, (0.60 * dwell_penalty) + (0.40 * undo_penalty))

        # Check Heideggerian ontological state
        is_rupture = r_rupture >= self.rupture_threshold
        state = "VORHANDEN" if is_rupture else "ZUHANDEN"

        if not is_rupture:
            self.flow_states_count += 1
        else:
            self.ruptures_healed_count += 1

        # Suggest hint if user has dwelled past 10 seconds
        should_reveal_hint = dwell_seconds >= self.dwell_patience_seconds

        return {
            "dwell_seconds": dwell_seconds,
            "dwell_patience_threshold": self.dwell_patience_seconds,
            "rupture_index": round(r_rupture, 4),
            "phenomenological_state": state,
            "in_desirable_difficulty_window": (0.0 <= dwell_seconds <= self.dwell_patience_seconds),
            "should_reveal_hint": should_reveal_hint,
            "undo_reversals_count": self.undo_reversals_count,
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_reviews": self.total_reviews_evaluated,
            "flow_zuhanden_count": self.flow_states_count,
            "rupture_vorhanden_count": self.ruptures_healed_count,
            "undo_reversals_count": self.undo_reversals_count,
            "dwell_patience_seconds": self.dwell_patience_seconds,
        }
