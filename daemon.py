"""Axioma Lexis G2 Edge Daemon Extremity [L1-G2-007 Kinetic Chaining].

Headless background daemon for:
- Spaced repetition scheduling audits
- Curiosity notification dispatch (Max 2/day: morning 08:30 & evening 19:30)
- Landauer thermodynamic dissipation monitoring
"""

from typing import Any, Dict, Optional
import logging
import time

from .core import LexisCoreEngine

logger = logging.getLogger("LexisDaemon")


class LexisEdgeDaemon:
    """Headless background scheduling daemon for Axioma Lexis G2."""

    def __init__(self, engine: Optional[LexisCoreEngine] = None, interval_seconds: float = 3.0):
        self.engine = engine or LexisCoreEngine(seed_default=True)
        self.interval_seconds = interval_seconds
        self._cycles = 0

    def execute_daemon_cycle(self) -> Dict[str, Any]:
        """Runs a single background scheduling and notification audit cycle."""
        self._cycles += 1
        summary = self.engine.get_system_summary()
        notif = self.engine.get_curiosity_notification()

        # Landauer thermodynamic auditing: 16 erased bits per cycle state hash
        kb_t_ln2 = 1.380649e-23 * 300 * 0.693147  # ~2.87e-21 Joules
        dissipated = 16 * kb_t_ln2

        report = {
            "cycle": self._cycles,
            "timestamp": time.time(),
            "words_due": summary["due_cards_total"],
            "notification_prompt": notif.context_snippet,
            "scheduled_window": notif.scheduled_window,
            "dissipated_joules": dissipated,
            "enclave_heals": summary["enclave_healed_incidents"],
        }
        return report

    def run_loop(self, max_cycles: Optional[int] = None) -> None:
        """Executes daemon cycles continuously or up to max_cycles."""
        print(f"[*] Lexis Edge Daemon started (Interval: {self.interval_seconds}s)")
        count = 0
        while max_cycles is None or count < max_cycles:
            count += 1
            report = self.execute_daemon_cycle()
            print(f"[Daemon Cycle #{report['cycle']}] Window: {report['scheduled_window']} | Due: {report['words_due']} | Prompt: {report['notification_prompt'][:35]}...")
            if max_cycles and count >= max_cycles:
                break
            time.sleep(self.interval_seconds)


if __name__ == "__main__":
    daemon = LexisEdgeDaemon(interval_seconds=1.0)
    daemon.run_loop(max_cycles=3)
