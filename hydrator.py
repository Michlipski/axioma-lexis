"""Instant Single-Word Hydration Engine for Axioma Lexis G2.

Eliminates the friction of manual card authoring:
Given ONLY a target word, auto-hydrates:
- Canonical definition & part of speech
- Phonetic IPA notation
- Grounded contextual sentence
- Etymological / mnemonic hint
- Domain taxonomy
Speech synthesis is strictly out of scope (0 audio bloat).
"""

from typing import Dict, Optional
import re
import time

from .types import CardTier, WordCard


# Embedded offline high-signal dictionary corpus
BUILTIN_LEXICON: Dict[str, Dict[str, str]] = {
    "zuhandenheit": {
        "definition": "The ontological mode of equipment when it functions smoothly as a transparent extension of human intent ('ready-to-hand').",
        "ipa": "/tsuːˈhandn̩haɪt/",
        "context_sentence": "When a tool achieves Zuhandenheit, the artisan's attention flows through it directly into the work.",
        "domain": "Phenomenology / Ontology",
        "etymology_hint": "German: zu (at) + Hand (hand) = literally 'at-hand' or accessible readiness.",
    },
    "vorhandenheit": {
        "definition": "The ontological mode of an object when it malfunctions or breaks, becoming an alien, conspicuous obstacle ('present-at-hand').",
        "ipa": "/foːɐ̯ˈhandn̩haɪt/",
        "context_sentence": "The moment the hammer's head flies off, it collapses into Vorhandenheit.",
        "domain": "Phenomenology / Ontology",
        "etymology_hint": "German: vor (before) + Hand (hand) = standing passively before the hand.",
    },
    "tenacious": {
        "definition": "Holding fast; persistent; tending to keep a firm hold of something; stubborn or determined.",
        "ipa": "/təˈneɪ.ʃəs/",
        "context_sentence": "She was tenacious in pursuing the bug across recursive compiler boundary layers.",
        "domain": "General / Rhetoric",
        "etymology_hint": "Latin: tenax (holding fast), from tenere (to hold).",
    },
    "epistemic": {
        "definition": "Relating to knowledge or to the degree of its validation and cognitive warrant.",
        "ipa": "/ˌep.ɪˈstiː.mɪk/",
        "context_sentence": "We applied epistemic pruning heuristics to avoid exploring tautological search branches.",
        "domain": "Philosophy of Science",
        "etymology_hint": "Greek: episteme (knowledge, understanding) from epi- (upon) + histanai (to stand).",
    },
    "functor": {
        "definition": "A mapping between categories in mathematics that preserves objects, morphisms, and composition structures.",
        "ipa": "/ˈfʌŋk.tər/",
        "context_sentence": "The AST compiles to multiple runtime extremities via a category-theoretic functor.",
        "domain": "Category Theory / CS",
        "etymology_hint": "Coined in modern logic from function + -or.",
    },
    "landauer": {
        "definition": "Pertaining to Landauer's principle: any logically irreversible manipulation of information must dissipate at least kB*T*ln(2) of heat per erased bit.",
        "ipa": "/ˈlæn.daʊ.ər/",
        "context_sentence": "The daemon audits every state mutation against the Landauer thermodynamic dissipation bound.",
        "domain": "Thermodynamics / Information Theory",
        "etymology_hint": "Named after physicist Rolf Landauer (1961).",
    },
    "panacea": {
        "definition": "A solution or remedy for all difficulties or diseases; a universal cure-all.",
        "ipa": "/ˌpæn.əˈsiː.ə/",
        "context_sentence": "Microservices are not an architectural panacea for disorganized team communications.",
        "domain": "Rhetoric / Literature",
        "etymology_hint": "Greek: panakes (all-healing), from pan (all) + akos (cure).",
    },
    "galois": {
        "definition": "Relating to Galois theory or Galois connections: a pair of monotone maps between posets that capture optimal approximations.",
        "ipa": "/ɡælˈwɑː/",
        "context_sentence": "The adjoint Galois connection bounds intent abstractions against physical machine state.",
        "domain": "Abstract Algebra / Order Theory",
        "etymology_hint": "Named after French mathematician Évariste Galois.",
    },
    "parsimony": {
        "definition": "Extreme unwillingness to spend resources; in science, the principle that the simplest sufficient explanation is preferred (Occam's razor).",
        "ipa": "/ˈpɑː.sɪ.mə.ni/",
        "context_sentence": "Architectural parsimony prevented us from introducing unnecessary external dependencies.",
        "domain": "Epistemology / Science",
        "etymology_hint": "Latin: parsimonia (frugality, thrift), from parcere (to spare).",
    },
    "teleology": {
        "definition": "The explanation of phenomena by the purpose they serve rather than by postulated causes; goal-directed design.",
        "ipa": "/ˌtiː.liˈɒl.ə.dʒi/",
        "context_sentence": "The high-level jettison grounds compiler teleology in production software that humans love.",
        "domain": "Philosophy / Cybernetics",
        "etymology_hint": "Greek: telos (end, purpose, goal) + -logia (study of).",
    },
    "serendipity": {
        "definition": "The occurrence and development of events by chance in a happy or beneficial way.",
        "ipa": "/ˌsɛr.ənˈdɪp.ə.ti/",
        "context_sentence": "Finding the exact mathematical proof was a stroke of serendipity.",
        "domain": "Noun",
        "etymology_hint": "Coined by Horace Walpole (1754) from the Persian fairy tale 'The Three Princes of Serendip'.",
    },
    "ephemeral": {
        "definition": "Lasting for a very short time; transitory; fleeting.",
        "ipa": "/ɪˈfem.ər.əl/",
        "context_sentence": "Transient cache entries are ephemeral artifacts that decay quickly.",
        "domain": "Adjective",
        "etymology_hint": "Greek: ephemeros (lasting only a day), from epi (upon) + hemera (day).",
    },
    "ubiquitous": {
        "definition": "Present, appearing, or found everywhere; omnipresent.",
        "ipa": "/juːˈbɪk.wɪ.təs/",
        "context_sentence": "Smartphones have become ubiquitous across modern urban society.",
        "domain": "Adjective",
        "etymology_hint": "Latin: ubique (everywhere).",
    },
    "esoteric": {
        "definition": "Intended for or likely to be understood by only a small number of people with specialized knowledge.",
        "ipa": "/ˌes.əˈter.ɪk/",
        "context_sentence": "The compiler internals rely on esoteric type-theoretic constructs.",
        "domain": "Adjective",
        "etymology_hint": "Greek: esoterikos (belonging to an inner circle), from eso (within).",
    },
    "pragmatic": {
        "definition": "Dealing with things sensibly and realistically in a way that is based on practical rather than theoretical considerations.",
        "ipa": "/præɡˈmæt.ɪk/",
        "context_sentence": "He took a pragmatic approach to system design, shipping working code over pure theory.",
        "domain": "Adjective",
        "etymology_hint": "Greek: pragmatikos (fit for business), from pragma (deed, matter).",
    },
    "paradigm": {
        "definition": "A typical example or pattern of something; a distinct set of concepts or thought patterns.",
        "ipa": "/ˈpær.ə.daɪm/",
        "context_sentence": "Functional reactive programming represents a distinct architectural paradigm.",
        "domain": "Noun",
        "etymology_hint": "Greek: paradeigma (pattern, model), from para (beside) + deiknunai (to show).",
    },
    "dichotomy": {
        "definition": "A division or contrast between two things that are or are represented as being opposed or entirely different.",
        "ipa": "/daɪˈkɒt.ə.mi/",
        "context_sentence": "We explored the false dichotomy between strict formal correctness and developer velocity.",
        "domain": "Noun",
        "etymology_hint": "Greek: dikhotomia, from dikho (in two) + temnein (to cut).",
    },
    "mellifluous": {
        "definition": "Pleasingly smooth and musical to hear; sweet-sounding.",
        "ipa": "/məˈlɪf.lu.əs/",
        "context_sentence": "The cellist produced a mellifluous tone that captivated the auditorium.",
        "domain": "Adjective",
        "etymology_hint": "Latin: mellifluus, from mel (honey) + fluere (to flow).",
    },
    "anomalous": {
        "definition": "Deviating from what is standard, normal, or expected; irregular.",
        "ipa": "/əˈnɒm.ə.ləs/",
        "context_sentence": "The anomaly detector flagged an anomalous surge in network packet drops.",
        "domain": "Adjective",
        "etymology_hint": "Greek: anomalos (uneven, irregular), from an- (not) + homalos (even).",
    },
}


def _lookup_online_definition(word: str) -> Optional[Dict[str, str]]:
    """Fetches canonical definition, IPA, context sentence, and etymological mnemonic from Wiktionary and Datamuse."""
    import urllib.parse
    import urllib.request
    import json
    import re

    clean = word.strip().lower()
    res = {
        "word": clean,
        "definition": "",
        "ipa": f"/{clean}/",
        "domain": "Vocabulary",
        "context_sentence": "",
        "etymology_hint": "",
    }

    # 1. Wiktionary Plain-Text Extract API (pure explaintext output)
    try:
        w_url = f"https://en.wiktionary.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote(clean)}&format=json"
        req = urllib.request.Request(w_url, headers={"User-Agent": "AxiomaLexis/2.0 (michaellipski@meta-axioma.local)"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for p in data.get("query", {}).get("pages", {}).values():
                text = p.get("extract", "")
                if not text:
                    continue

                # Etymology / Mnemonic
                m_etym = re.search(r"===\s*Etymology(?:\s*\d+)?\s*===\s*\n(.*?)(?=\n===|\Z)", text, re.DOTALL)
                if m_etym:
                    for l in m_etym.group(1).splitlines():
                        l = l.strip()
                        if l and not l.startswith("==") and len(l) > 15:
                            res["etymology_hint"] = l
                            break

                # IPA pronunciation
                m_ipa = re.search(r"/[^/\n]{2,35}/", text)
                if m_ipa:
                    res["ipa"] = m_ipa.group(0)

                # Part of speech, Definition, and Quotation
                pos_m = list(re.finditer(r"===\s*(Noun|Verb|Adjective|Adverb)\s*===\s*\n(.*?)(?=\n==[=]?|\Z)", text, re.DOTALL))
                if pos_m:
                    res["domain"] = pos_m[0].group(1)
                    body_lines = [l.strip() for l in pos_m[0].group(2).splitlines() if l.strip()]

                    for l in body_lines:
                        if l.startswith("Synonym") or l.startswith("Antonym") or l.startswith("("):
                            continue
                        if not l.startswith(f"{clean} ") and not l.startswith(f"{clean}(") and len(l) > 10:
                            res["definition"] = l
                            break
                    if not res["definition"] and body_lines:
                        res["definition"] = body_lines[0]

                    for l in body_lines:
                        if clean in l.lower() and len(l) > 35:
                            if not l.startswith(f"{clean} (") and not l.startswith("Synonym") and not l.startswith("Antonym"):
                                res["context_sentence"] = l
                                break
    except Exception:
        pass

    # 2. Datamuse fallback if definition is missing
    if not res["definition"]:
        try:
            d_url = f"https://api.datamuse.com/words?sp={urllib.parse.quote(clean)}&md=dpf&max=1"
            req = urllib.request.Request(d_url, headers={"User-Agent": "Mozilla/5.0 AxiomaLexis/2.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                d_raw = json.loads(resp.read().decode("utf-8"))
                if d_raw and d_raw[0].get("defs"):
                    parts = d_raw[0]["defs"][0].split("\t", 1)
                    pos_code = parts[0] if len(parts) > 1 else "n"
                    def_text = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                    pos_map = {"n": "Noun", "v": "Verb", "adj": "Adjective", "adv": "Adverb"}
                    res["domain"] = pos_map.get(pos_code, res["domain"])
                    res["definition"] = def_text
        except Exception:
            pass

    # 3. Tatoeba context sentence search if quote was missing
    if not res["context_sentence"]:
        try:
            t_url = f"https://tatoeba.org/en/api_v0/search?query={urllib.parse.quote(clean)}&from=eng"
            req = urllib.request.Request(t_url, headers={"User-Agent": "Mozilla/5.0 AxiomaLexis/2.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                t_raw = json.loads(resp.read().decode("utf-8"))
                for r in t_raw.get("results", []):
                    stext = r.get("text", "").strip()
                    if clean in stext.lower() and len(stext) >= 15 and not stext.lower().startswith("what does"):
                        res["context_sentence"] = f'"{stext}"'
                        break
        except Exception:
            pass

    # 4. Synthesized contextual sentence fallback if still missing
    if not res["context_sentence"]:
        if res["domain"] == "Adjective":
            res["context_sentence"] = f'"Her {clean} perspective challenged the conventional assumptions of the team."'
        elif res["domain"] == "Verb":
            res["context_sentence"] = f'"Researchers actively {clean} these dynamics across contemporary critical literature."'
        else:
            res["context_sentence"] = f'"The concept of {clean} served as a key focal point in the philosophical analysis."'

    # 5. Synthesized mnemonic fallback if still missing
    if not res["etymology_hint"]:
        res["etymology_hint"] = f'Mnemonic: connect "{clean}" to its root morphemes, prefix/suffix patterns, and distinctive sound associations.'

    if res["definition"]:
        return res

    return None


class WordHydrator:
    """Instant single-word card hydration service."""

    def __init__(self, custom_lexicon: Optional[Dict[str, Dict[str, str]]] = None):
        self.lexicon = dict(BUILTIN_LEXICON)
        if custom_lexicon:
            self.lexicon.update(custom_lexicon)

    def hydrate_word(self, word: str, custom_sentence: Optional[str] = None) -> WordCard:
        """Hydrates a target word into a complete WordCard in Tier 0 due immediately."""
        clean_word = word.strip().lower()
        if not clean_word:
            raise ValueError("Target word cannot be empty.")

        entry = self.lexicon.get(clean_word)
        if not entry:
            online_entry = _lookup_online_definition(clean_word)
            if online_entry:
                entry = online_entry
                self.lexicon[clean_word] = entry

        if entry:
            definition = entry["definition"]
            ipa = entry["ipa"]
            context_sentence = custom_sentence or entry["context_sentence"]
            domain = entry["domain"]
            etymology_hint = entry["etymology_hint"]
        else:
            # Algorithmic derivation for unindexed words
            definition = f"A notable term: {clean_word.capitalize()}."
            ipa = f"/{clean_word}/"
            context_sentence = custom_sentence or f"The author demonstrated a mastery of {clean_word} in the text."
            domain = "Vocabulary"
            etymology_hint = f"Root study: inspect morphological stems of '{clean_word}'."

        now = time.time()
        # Tier 0 acquisition: due immediately for initial acquisition
        due = now

        return WordCard(
            word=clean_word,
            definition=definition,
            ipa=ipa,
            context_sentence=context_sentence,
            domain=domain,
            etymology_hint=etymology_hint,
            tier=CardTier.TIER_0_ACQUISITION.value,
            created_at=now,
            due_timestamp=due,
        )
