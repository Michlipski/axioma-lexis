"""Type definitions and data models for Axioma Lexis G2."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid


class CardTier(int, Enum):
    """Humane Step-Back Fibonacci Spacing Tiers."""
    TIER_0_ACQUISITION = 0   # +4-6 hours
    TIER_1_NEXT_DAY = 1      # +1 day
    TIER_2_SHORT = 2         # +3 days
    TIER_3_MEDIUM = 3        # +7 days
    TIER_4_LONG = 4          # +16 days
    TIER_5_MASTERY = 5       # +35 days
    TIER_6_RETAINED = 6      # +90 days (Mastered Anchor)


# Canonical interval offsets in seconds
TIER_INTERVALS_SECONDS: Dict[int, float] = {
    0: 4 * 3600,            # 4 hours
    1: 24 * 3600,           # 1 day
    2: 3 * 24 * 3600,       # 3 days
    3: 7 * 24 * 3600,       # 7 days
    4: 16 * 24 * 3600,      # 16 days
    5: 35 * 24 * 3600,      # 35 days
    6: 90 * 24 * 3600,      # 90 days
}


class ReviewOutcome(str, Enum):
    """Tactile review outcomes."""
    MASTERED = "MASTERED"          # Swipe Right / Know (Advance Tier)
    STRUGGLING = "STRUGGLING"      # Swipe Left / Review (Step-Back 1 Tier)
    HINT_USED = "HINT_USED"        # Recalled after >10s Hint (Preserve Tier)
    UNDO = "UNDO"                  # 1-Tap Functorial Rollback


@dataclass
class WordCard:
    """Core flashcard AST model with zero audio bloat."""
    word: str
    definition: str
    ipa: str
    context_sentence: str
    domain: str = "General"
    etymology_hint: str = ""
    card_id: str = field(default_factory=lambda: f"card_{uuid.uuid4().hex[:8]}")
    tier: int = CardTier.TIER_0_ACQUISITION.value
    created_at: float = field(default_factory=time.time)
    due_timestamp: float = field(default_factory=time.time)
    last_reviewed: Optional[float] = None
    review_count: int = 0
    consecutive_correct: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WordCard":
        return cls(
            word=data.get("word", "untitled"),
            definition=data.get("definition", ""),
            ipa=data.get("ipa", ""),
            context_sentence=data.get("context_sentence", ""),
            domain=data.get("domain", "General"),
            etymology_hint=data.get("etymology_hint", ""),
            card_id=data.get("card_id", f"card_{uuid.uuid4().hex[:8]}"),
            tier=int(data.get("tier", 0)),
            created_at=float(data.get("created_at", time.time())),
            due_timestamp=float(data.get("due_timestamp", time.time())),
            last_reviewed=float(data["last_reviewed"]) if data.get("last_reviewed") else None,
            review_count=int(data.get("review_count", 0)),
            consecutive_correct=int(data.get("consecutive_correct", 0)),
            history=data.get("history", []),
        )


@dataclass
class MicroSession:
    """Strictly capped bite-sized review batch (3 to 5 words max)."""
    session_id: str
    cards: List[WordCard]
    current_index: int = 0
    completed: bool = False
    start_timestamp: float = field(default_factory=time.time)
    end_timestamp: Optional[float] = None
    session_outcomes: List[Dict[str, Any]] = field(default_factory=list)

    def get_active_card(self) -> Optional[WordCard]:
        if self.completed or self.current_index >= len(self.cards):
            return None
        return self.cards[self.current_index]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "cards": [c.to_dict() for c in self.cards],
            "current_index": self.current_index,
            "total_cards": len(self.cards),
            "completed": self.completed,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "session_outcomes": self.session_outcomes,
        }


@dataclass
class CuriosityNotification:
    """Non-intrusive curiosity snippet push notification."""
    notification_id: str
    prompt_word: str
    context_snippet: str
    cards_due_count: int
    scheduled_window: str   # "MORNING_0830" or "EVENING_1930"
    direct_route: str = "/#direct-review"
    sent_timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
