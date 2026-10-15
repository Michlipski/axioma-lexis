"""Axioma Lexis G2 Terminal CLI Extremity [L1-G2-007 Kinetic Chaining].

Provides rapid, keyboard-first vocabulary capture and micro-reviews:
- 'lexis add <word>' -> Zero-friction instant capture from terminal reading
- 'lexis review'     -> 30-second 3-card micro-session in stdout
- 'lexis status'     -> Real-time tier counts and flow metrics
"""

from typing import List, Optional
import argparse
import sys
import time

from .core import LexisCoreEngine
from .types import ReviewOutcome


def run_cli(args: Optional[List[str]] = None) -> int:
    """Executes Lexis G2 CLI commands."""
    parser = argparse.ArgumentParser(description="Axioma Lexis G2 Terminal Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 1. add
    add_p = subparsers.add_parser("add", help="Capture and auto-hydrate a single word")
    add_p.add_argument("word", type=str, help="Target word to capture")
    add_p.add_argument("--sentence", type=str, default=None, help="Optional context sentence")

    # 2. review
    subparsers.add_parser("review", help="Run a 30s micro-review session (3 words)")

    # 3. status
    subparsers.add_parser("status", help="Show system status, tier distribution, and due counts")

    # 4. list
    subparsers.add_parser("list", help="List active vocabulary items")

    # 5. notif
    subparsers.add_parser("notif", help="Show current curiosity notification prompt")

    parsed = parser.parse_args(args)
    if not parsed.command:
        parser.print_help()
        return 0

    engine = LexisCoreEngine(seed_default=True)

    if parsed.command == "add":
        t0 = time.time()
        card = engine.add_word(parsed.word, custom_sentence=parsed.sentence)
        elapsed = time.time() - t0
        print(f"\n[+] Instant Hydration Complete ({elapsed:.2f}s) [Zero-Typing Capture]")
        print(f"    Word:       {card.word.upper()}")
        print(f"    IPA:        {card.ipa}")
        print(f"    Domain:     {card.domain}")
        print(f"    Definition: {card.definition}")
        print(f"    Sentence:   \"{card.context_sentence}\"")
        print(f"    Initial:    Tier 0 (Due in 4h)\n")
        return 0

    elif parsed.command == "status":
        summary = engine.get_system_summary()
        print("\n=================== AXIOMA LEXIS G2 STATUS ===================")
        print(f"Total Words:        {summary['total_cards']}")
        print(f"Words Due Now:      {summary['due_cards_total']}")
        print(f"Capped Slice:       {summary['capped_session_slice']} cards (Micro-Dosed)")
        print(f"Tier Breakdown:     {summary['tier_distribution']}")
        print(f"Enclave Auto-Heals: {summary['enclave_healed_incidents']}")
        print(f"Flow State:         {summary['phenomenology']['flow_zuhanden_count']} Flow / {summary['phenomenology']['rupture_vorhanden_count']} Ruptures")
        print("==============================================================\n")
        return 0

    elif parsed.command == "list":
        print("\n================== ACTIVE VOCABULARY ==================")
        for c in engine.cards.values():
            print(f"[{c.word.ljust(15)}] Tier {c.tier} | {c.domain.ljust(22)} | {c.definition[:45]}...")
        print("=======================================================\n")
        return 0

    elif parsed.command == "notif":
        notif = engine.get_curiosity_notification()
        print(f"\n[🔔 Curiosity Snippet Push: {notif.scheduled_window}]")
        print(f"    Title: Axioma Lexis · Micro-review ready ({notif.cards_due_count} words)")
        print(f"    Body:  {notif.context_snippet}")
        print(f"    Route: {notif.direct_route}\n")
        return 0

    elif parsed.command == "review":
        session = engine.get_or_create_micro_session()
        print(f"\n[*] Starting Micro-Review ({len(session.cards)} words max)")
        for idx, card in enumerate(session.cards):
            print(f"\n================ Card {idx + 1} of {len(session.cards)} ================")
            print(f"Word:   {card.word.upper()} ({card.ipa})")
            print(f"Domain: {card.domain}")
            print(f"Tier:   Tier {card.tier}")
            print("--------------------------------------------------")
            print("  [Active Recall Mode: Definition Concealed]")
            if sys.stdin.isatty():
                try:
                    input("  [👆 Press Enter to reveal definition & context...]")
                except (EOFError, KeyboardInterrupt):
                    pass
            print(f"\nDefinition: {card.definition}")
            print(f"Context:    \"{card.context_sentence}\"")
            res = engine.answer_active_card(card.card_id, ReviewOutcome.MASTERED, dwell_seconds=1.5)
            print(f"Result:     {res['effective_outcome']} -> Advanced to Tier {res['card']['tier']}")

        print("\n[✓] Micro-Session Complete! 0 Backlog Dread. Have a great day!\n")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
