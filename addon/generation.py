"""
Generation pipeline: build the prompt, call the provider, parse the result, and
(optionally) render furigana.

Kept separate from the transport layer (`llm.py`) so new generation modes can be
added here without touching how we talk to the API. Everything here is plain
network/CPU work with no Qt — safe to run on a background thread.

Furigana readings come from the LLM we already call: a morphological analyzer
(MeCab/fugashi/pykakasi) would violate the no-heavy-deps constraint, and the model
disambiguates context-dependent readings (行った = いった / おこなった) better than a
naive dictionary lookup. When furigana is enabled the model returns each sentence
as tokens with readings + an `is_target` flag, and we render the wrapper locally.
"""

import json
import re

from . import config, llm

# Kanji (incl. CJK Ext-A) plus the iteration mark.
_KANJI = re.compile(r"[㐀-䶿一-鿿々]")

_SYSTEM_PLAIN = (
    "You generate natural, colloquial Japanese example sentences for a language "
    "learner. The sentences must sound like everyday spoken Japanese, not textbook "
    "prose, and must be appropriate for the learner's stated level.\n\n"
    "Respond with ONLY a JSON array — no prose, no markdown, no code fences. Each "
    'element is an object: {"jp": "<the Japanese sentence>", "en": "<a short '
    'English translation>"}. Every sentence must use the given vocabulary word.'
)

_SYSTEM_FURIGANA = (
    "You generate natural, colloquial Japanese example sentences for a language "
    "learner. The sentences must sound like everyday spoken Japanese, not textbook "
    "prose, and must be appropriate for the learner's stated level.\n\n"
    "Respond with ONLY a JSON array — no prose, no markdown, no code fences. Each "
    "element is an object with two keys:\n"
    '  "en": a short English translation,\n'
    '  "tokens": the sentence split into word-level tokens, in order. Each token is '
    '{"text": "<surface text>", "reading": "<full hiragana reading of text, or empty '
    'string if it contains no kanji>", "is_target": <true only for the token(s) that '
    "are the target vocabulary word, else false>}.\n"
    "Concatenating the token texts must reproduce the sentence exactly. Give a reading "
    "for every token that contains kanji. Every sentence must use the target word."
)


def build_prompt(vocab: str, level: str, n: int, furigana: bool) -> tuple[str, str]:
    system = _SYSTEM_FURIGANA if furigana else _SYSTEM_PLAIN
    user = (
        f"Target vocabulary word: {vocab}\n"
        f"Learner level: {level}\n"
        f"Generate {n} sentences."
    )
    return system, user


def generate_sentences(vocab: str, level: str, n: int) -> list[dict]:
    """Returns items shaped {jp, en, tokens}. `tokens` is None when furigana is off."""
    furigana = config.get_furigana_mode() != "off"
    system, user = build_prompt(vocab, level, n, furigana)
    # Tokenised output is larger; give it more room.
    max_tokens = 4096 if furigana else 2048
    raw = llm.get_provider().complete(system, user, max_tokens=max_tokens)
    data = _load_array(raw)
    return _parse_furigana(data) if furigana else _parse_plain(data)


# --- parsing ----------------------------------------------------------------


def _load_array(text: str) -> list:
    cleaned = _strip_code_fences(text.strip())
    try:
        data = json.loads(cleaned)
    except ValueError as err:
        raise llm.LLMError("The model returned an unexpected format.") from err
    if not isinstance(data, list):
        raise llm.LLMError("The model returned an unexpected format.")
    return data


def _parse_plain(data: list) -> list[dict]:
    items = [
        {"jp": str(e["jp"]), "en": str(e.get("en", "")), "tokens": None}
        for e in data
        if isinstance(e, dict) and e.get("jp")
    ]
    if not items:
        raise llm.LLMError("The model returned no usable sentences.")
    return items


def _parse_furigana(data: list) -> list[dict]:
    items: list[dict] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        tokens = _clean_tokens(entry.get("tokens"))
        if not tokens:
            continue
        items.append(
            {
                "jp": "".join(t["text"] for t in tokens),
                "en": str(entry.get("en", "")),
                "tokens": tokens,
            }
        )
    if not items:
        raise llm.LLMError("The model returned no usable sentences.")
    return items


def _clean_tokens(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    tokens = []
    for t in raw:
        if isinstance(t, dict) and t.get("text"):
            tokens.append(
                {
                    "text": str(t["text"]),
                    "reading": str(t.get("reading", "")),
                    "is_target": bool(t.get("is_target", False)),
                }
            )
    return tokens


def _strip_code_fences(text: str) -> str:
    """Tolerate a ```json ... ``` wrapper if the model adds one anyway."""
    text = text.strip()
    if not text.startswith("```"):
        return text
    newline = text.find("\n")
    text = text[newline + 1:] if newline != -1 else text[len("```"):]
    text = text.strip()
    if text.endswith("```"):
        text = text[: -len("```")].strip()
    if text.startswith("json"):
        text = text[len("json"):].strip()
    return text


# --- rendering --------------------------------------------------------------


def _split_runs(text: str) -> list[tuple[str, bool]]:
    """Split text into consecutive runs of (substring, is_kanji)."""
    runs: list[tuple[str, bool]] = []
    for ch in text:
        is_kanji = bool(_KANJI.match(ch))
        if runs and runs[-1][1] == is_kanji:
            runs[-1] = (runs[-1][0] + ch, is_kanji)
        else:
            runs.append((ch, is_kanji))
    return runs


def _align_furigana(text: str, reading: str):
    """Map the reading onto the kanji runs only, leaving okurigana/kana bare.

    Returns a list of (substring, reading_or_None) — None for kana runs — or None
    overall if the reading can't be cleanly aligned (caller falls back to wrapping
    the whole token). Peels matching kana off the reading so 新しい/あたらしい →
    [(新, あたら), (しい, None)].
    """
    runs = _split_runs(text)
    out = []
    ri = 0
    for i, (sub, is_kanji) in enumerate(runs):
        if not is_kanji:
            if reading[ri:ri + len(sub)] != sub:
                return None  # kana doesn't line up — bail
            out.append((sub, None))
            ri += len(sub)
        else:
            # This kanji run reads up to where the next (kana) run appears.
            if i + 1 < len(runs):
                pos = reading.find(runs[i + 1][0], ri)
                if pos == -1:
                    return None
                kana = reading[ri:pos]
                ri = pos
            else:
                kana = reading[ri:]
                ri = len(reading)
            if not kana:
                return None  # kanji with no reading — misaligned
            out.append((sub, kana))
    return out if ri == len(reading) else None


def _wrap(mode: str, template: str, kanji: str, reading: str) -> str:
    if mode == "ruby":
        return f"<ruby>{kanji}<rt>{reading}</rt></ruby>"
    # custom — literal replace so stray braces in the template are safe
    return template.replace("{kanji}", kanji).replace("{reading}", reading)


def render(tokens: list[dict], target: str) -> str:
    """Render tokens to field HTML, applying furigana per the configured mode.

    Furigana sits only on the kanji within a token, not its kana okurigana
    (新しい → あたら over 新, しい left bare), and never on the target word (kept
    bare so it stays the one unknown). Reads furigana config fresh so a settings
    change applies without regenerating.
    """
    mode = config.get_furigana_mode()
    template = config.get_furigana_template()
    parts = []
    for tok in tokens:
        text = tok["text"]
        reading = tok.get("reading", "")
        is_target = tok.get("is_target") or (target and target in text)
        if mode == "off" or is_target or not reading or not _KANJI.search(text):
            parts.append(text)
            continue
        segments = _align_furigana(text, reading)
        if segments is None:
            # Couldn't peel okurigana cleanly — wrap the whole token (old behaviour).
            parts.append(_wrap(mode, template, text, reading))
        else:
            parts.append(
                "".join(
                    sub if kana is None else _wrap(mode, template, sub, kana)
                    for sub, kana in segments
                )
            )
    return "".join(parts)
