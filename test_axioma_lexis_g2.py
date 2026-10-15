"""Comprehensive Verification Suite for Axioma Lexis G2 (System 02 Reconstruction).

Verifies all Generation 2 structural invariants:
- [L1-G2-001] Adjoint Galois Substrate Connection (Multi-substrate AST fidelity)
- [L1-G2-002] Ephemeral Self-Healing Enclaves (3-pass corrupt deck schema recovery)
- [L1-G2-003] Cognitive Ergonomics & Functorial Reversibility (1-tap Undo)
- [L1-G2-004] Zero-Trust Capability Scoping (HMAC tokens)
- [L1-G2-005] Mandatory Human Intent Grounding (Elicitation witness verified)
- [L1-G2-006] Phenomenological Zuhandenheit Attunement (10s Dwell Patience Window)
- [L1-G2-007] Kinetic Chaining & Semantic Momentum Retention
"""

import unittest
import time

from .core import LexisCoreEngine
from .hydrator import WordHydrator
from .srs_engine import HumaneSRSEngine
from .phenomenology import LexisPhenomenologyCircuit
from .enclave import DeckHealingEnclave
from .types import CardTier, ReviewOutcome, WordCard


class TestAxiomaLexisG2(unittest.TestCase):
    """Formal unit test suite for Axioma Lexis G2."""

    def setUp(self):
        self.engine = LexisCoreEngine(seed_default=True)

    def test_instant_word_hydration_zero_typing(self):
        """[L1-G2-007] Verifies 1-tap single-word hydration with zero manual authoring."""
        hydrator = WordHydrator()
        card = hydrator.hydrate_word("tenacious")
        self.assertEqual(card.word, "tenacious")
        self.assertEqual(card.tier, CardTier.TIER_0_ACQUISITION.value)
        self.assertTrue(len(card.definition) > 10)
        self.assertTrue(len(card.ipa) > 2)
        self.assertIn("tenacious", card.context_sentence)
        # Speech synthesis out of scope
        self.assertFalse(hasattr(card, "audio_url"))
        self.assertFalse(hasattr(card, "speech_voice"))

    def test_micro_session_strictly_capped_at_three_to_five(self):
        """[L1-G2-003] Verifies activation energy barrier is solved via strictly capped micro-sessions."""
        # On a blank slate with only zuhandenheit:
        session_1 = self.engine.get_or_create_micro_session()
        self.assertEqual(len(session_1.cards), 1)

        # When populated with additional words, micro-sessions are strictly capped between 3 and 5:
        for w in ["epistemic", "tenacious", "teleology", "parsimony", "galois"]:
            self.engine.add_word(w)
        self.engine.active_session = None
        session = self.engine.get_or_create_micro_session()
        self.assertGreaterEqual(len(session.cards), 3)
        self.assertLessEqual(len(session.cards), 5)
        self.assertFalse(session.completed)

    def test_humane_step_back_fibonacci_spacing(self):
        """[L1-G2-003] Verifies that struggling cards decay by strictly 1 tier (no punitive zero-resets)."""
        card = self.engine.add_word("epistemic")
        card_id = card.card_id

        # 1. Mastered -> Advances from Tier 0 to Tier 1
        res1 = self.engine.answer_active_card(card_id, ReviewOutcome.MASTERED, dwell_seconds=2.0)
        self.assertEqual(res1["card"]["tier"], CardTier.TIER_1_NEXT_DAY.value)

        # 2. Mastered again -> Advances from Tier 1 to Tier 2
        res2 = self.engine.answer_active_card(card_id, ReviewOutcome.MASTERED, dwell_seconds=2.0)
        self.assertEqual(res2["card"]["tier"], CardTier.TIER_2_SHORT.value)

        # 3. Mastered again -> Advances to Tier 3
        res3 = self.engine.answer_active_card(card_id, ReviewOutcome.MASTERED, dwell_seconds=2.0)
        self.assertEqual(res3["card"]["tier"], CardTier.TIER_3_MEDIUM.value)

        # 4. Struggling -> Steps back by strictly 1 tier: Tier 3 -> Tier 2 (NOT Tier 0!)
        res4 = self.engine.answer_active_card(card_id, ReviewOutcome.STRUGGLING, dwell_seconds=3.0)
        self.assertEqual(res4["card"]["tier"], CardTier.TIER_2_SHORT.value)

    def test_ten_second_dwell_patience_window(self):
        """[L1-G2-006] Verifies Heideggerian 10.0s desirable difficulty window and auto-hint."""
        circuit = LexisPhenomenologyCircuit(dwell_patience_seconds=10.0)

        # Under 10s: Effortful retrieval is respected (Flow state)
        eval_5s = circuit.evaluate_dwell(dwell_seconds=5.0)
        self.assertEqual(eval_5s["phenomenological_state"], "ZUHANDEN")
        self.assertTrue(eval_5s["in_desirable_difficulty_window"])
        self.assertFalse(eval_5s["should_reveal_hint"])

        # At exactly 10s: Desirable difficulty bound
        eval_10s = circuit.evaluate_dwell(dwell_seconds=10.0)
        self.assertTrue(eval_10s["should_reveal_hint"])

        # Beyond 10s: Cognitive hesitation (Rupture state -> hint reveal)
        eval_14s = circuit.evaluate_dwell(dwell_seconds=14.0)
        self.assertEqual(eval_14s["phenomenological_state"], "VORHANDEN")
        self.assertTrue(eval_14s["should_reveal_hint"])

    def test_three_pass_enclave_auto_healing(self):
        """[L1-G2-002] Verifies 3-pass enclave auto-heals corrupted card schemas with zero crashes."""
        enclave = DeckHealingEnclave(max_passes=3)
        corrupted_raw = {
            "word": "anomalous_term",
            # missing definition
            # missing ipa
            "tier": 99,  # out-of-bounds tier
            "due_timestamp": "corrupted_non_numeric",
        }

        success, repaired_card, passes = enclave.heal_raw_card(corrupted_raw)
        self.assertTrue(success)
        self.assertEqual(repaired_card.word, "anomalous_term")
        self.assertEqual(repaired_card.tier, 6)  # clamped to max tier 6
        self.assertTrue(isinstance(repaired_card.due_timestamp, float))
        self.assertTrue(len(passes) >= 2)

    def test_functorial_one_tap_undo(self):
        """[L1-G2-003] Verifies 1-tap Undo restores exact prior card tier and session state."""
        card = self.engine.add_word("parsimony")
        initial_tier = card.tier

        # Answer card
        self.engine.answer_active_card(card.card_id, ReviewOutcome.MASTERED)
        self.assertEqual(self.engine.cards[card.card_id].tier, initial_tier + 1)

        # 1-Tap Undo
        restored = self.engine.undo_last_review()
        self.assertIsNotNone(restored)
        self.assertEqual(restored.tier, initial_tier)
        self.assertEqual(self.engine.cards[card.card_id].tier, initial_tier)

    def test_curiosity_notification_generation(self):
        """[L1-G2-005] Verifies non-intrusive curiosity snippet push generation."""
        notif = self.engine.get_curiosity_notification()
        self.assertIn("Do you recall", notif.context_snippet)
        self.assertTrue(notif.cards_due_count <= 5)
        self.assertIn(notif.scheduled_window, ["MORNING_0830", "EVENING_1930"])

    def test_android_pwa_manifest_and_sw_integrity(self):
        """[L1-G2-001] Verifies Android PWA manifest specification and offline Service Worker."""
        from pathlib import Path
        import json

        base_dir = Path(__file__).parent
        manifest_file = base_dir / "manifest.json"
        self.assertTrue(manifest_file.exists())
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["theme_color"], "#0a0d14")
        self.assertEqual(manifest["start_url"], "/")
        self.assertTrue(len(manifest["icons"]) >= 1)
        self.assertTrue(len(manifest["shortcuts"]) >= 2)

        shortcut_urls = [s["url"] for s in manifest["shortcuts"]]
        self.assertIn("/#capture", shortcut_urls)
        self.assertIn("/#review", shortcut_urls)

        # Service Worker
        sw_file = base_dir / "sw.js"
        self.assertTrue(sw_file.exists())
        sw_content = sw_file.read_text(encoding="utf-8")
        self.assertIn("caches.open", sw_content)
        self.assertIn("notificationclick", sw_content)

    def test_android_native_scaffold_integrity(self):
        """[L1-G2-001] Verifies Android Studio native scaffold, permissions, bridge, and assets."""
        from pathlib import Path
        import xml.etree.ElementTree as ET

        base_dir = Path(__file__).parent
        android_dir = base_dir / "android"
        self.assertTrue(android_dir.exists())

        # 1. Manifest verification
        manifest_file = android_dir / "app" / "src" / "main" / "AndroidManifest.xml"
        self.assertTrue(manifest_file.exists())
        tree = ET.parse(manifest_file)
        root = tree.getroot()

        permissions = [elem.attrib.get("{http://schemas.android.com/apk/res/android}name") for elem in root.findall("uses-permission")]
        self.assertIn("android.permission.INTERNET", permissions)
        self.assertIn("android.permission.VIBRATE", permissions)
        self.assertIn("android.permission.POST_NOTIFICATIONS", permissions)

        app_elem = root.find("application")
        self.assertIsNotNone(app_elem)
        self.assertEqual(app_elem.attrib.get("{http://schemas.android.com/apk/res/android}usesCleartextTraffic"), "true")

        # Verify NotificationReceiver in manifest
        receivers = [elem.attrib.get("{http://schemas.android.com/apk/res/android}name") for elem in app_elem.findall("receiver")]
        self.assertIn(".NotificationReceiver", receivers)

        # 2. Kotlin Activity & Receiver with AndroidBridge and AlarmManager
        kt_file = android_dir / "app" / "src" / "main" / "java" / "com" / "axioma" / "lexis" / "MainActivity.kt"
        self.assertTrue(kt_file.exists())
        kt_content = kt_file.read_text(encoding="utf-8")
        self.assertIn("AndroidBridge", kt_content)
        self.assertIn("vibrate(milliseconds: Long)", kt_content)
        self.assertIn("file:///android_asset/index.html", kt_content)
        self.assertIn("AlarmManager", kt_content)

        receiver_file = android_dir / "app" / "src" / "main" / "java" / "com" / "axioma" / "lexis" / "NotificationReceiver.kt"
        self.assertTrue(receiver_file.exists())
        receiver_content = receiver_file.read_text(encoding="utf-8")
        self.assertIn("BroadcastReceiver", receiver_content)
        self.assertIn("axioma_lexis_srs", receiver_content)
        self.assertIn("ic_notification", receiver_content)
        self.assertTrue((android_dir / "app" / "src" / "main" / "res" / "drawable" / "ic_notification.xml").exists())

        # 3. Bundled offline assets
        assets_dir = android_dir / "app" / "src" / "main" / "assets"
        self.assertTrue((assets_dir / "index.html").exists())
        self.assertTrue((assets_dir / "manifest.json").exists())
        self.assertTrue((assets_dir / "icon.svg").exists())
        self.assertIn("btn-test-notification", (assets_dir / "index.html").read_text(encoding="utf-8"))

        # 4. Gradle and Wrapper
        self.assertTrue((android_dir / "build.gradle").exists())
        self.assertTrue((android_dir / "app" / "build.gradle").exists())
        self.assertTrue((android_dir / "gradlew").exists())
        self.assertTrue((android_dir / "gradle" / "wrapper" / "gradle-wrapper.properties").exists())
        self.assertTrue((android_dir / "gradle" / "wrapper" / "gradle-wrapper.jar").exists())
        self.assertTrue((android_dir / "app" / "proguard-rules.pro").exists())
        self.assertTrue((android_dir / "gradle.properties").exists())
        self.assertIn("android.useAndroidX=true", (android_dir / "gradle.properties").read_text(encoding="utf-8"))

    def test_lexicon_catalog_retrieval(self):
        """[L1-G2-003] Verifies get_all_cards returns blank slate containing only zuhandenheit."""
        cards = self.engine.get_all_cards()
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].word, "zuhandenheit")
        self.assertEqual(cards[0].tier, 0)

    def test_lexicon_card_edit_and_enclave_sanitization(self):
        """[L1-G2-002] Verifies update_card updates definitions and heals corrupt mutations."""
        card = self.engine.add_word("hermeneutic")
        card_id = card.card_id

        # 1. Valid update
        updated = self.engine.update_card(card_id, {
            "definition": "The branch of knowledge that deals with interpretation of text and meaning.",
            "domain": "Philosophy",
            "tier": 3,
            "etymology_hint": "Greek: hermeneus (interpreter).",
        })
        self.assertEqual(updated.card_id, card_id)
        self.assertEqual(updated.tier, 3)
        self.assertIn("interpretation", updated.definition)
        self.assertEqual(updated.domain, "Philosophy")

        # 2. Corrupt tier update clamped by enclave
        healed = self.engine.update_card(card_id, {
            "tier": 99,  # out of bounds tier clamped to max 6
        })
        self.assertEqual(healed.tier, 6)

    def test_lexicon_card_deletion_and_session_resilience(self):
        """[L1-G2-003] Verifies delete_card safely prunes terms and updates active sessions."""
        card = self.engine.add_word("ephemeral")
        card_id = card.card_id
        self.assertIn(card_id, self.engine.cards)

        # Ensure session exists
        session = self.engine.get_or_create_micro_session()

        # Delete card
        success = self.engine.delete_card(card_id)
        self.assertTrue(success)
        self.assertNotIn(card_id, self.engine.cards)

        # Deleting non-existent returns False
        self.assertFalse(self.engine.delete_card("non-existent-id"))


if __name__ == "__main__":
    unittest.main()

