"""
all generation logic
"""

import json
import random
import re

from . import config, llm
from .i18n import tr


_KANJI = re.compile(r"[㐀-䶿一-鿿々]")

_RULES = (
    "Rules:\n"
    "- Grammatically correct, natural Japanese that fits the requested register and level.\n"
    "- Conjugate the target word into whatever form the sentence needs — don't leave it "
    "in dictionary form when the grammar calls for an inflected form.\n"
    "- Every sentence must use the target word and depict a clearly different situation; "
    "no two may share a scenario or sentence pattern.\n\n"
)

_SYSTEM_PLAIN = (
    "You write natural Japanese example sentences for a language learner.\n\n"
    + _RULES
    + "Respond with ONLY a JSON array — no prose, no markdown, no code fences. Each "
    'element: {"jp": "<the sentence>", "en": "<short English translation>"}.'
)

_SYSTEM_FURIGANA = (
    "You write natural Japanese example sentences for a language learner, then "
    "tokenise each for furigana.\n\n"
    + _RULES
    + "Respond with ONLY a JSON array — no prose, no markdown, no code fences. Each "
    "element has three keys:\n"
    '  "jp": the finished sentence,\n'
    '  "en": a short English translation,\n'
    '  "tokens": jp split into word-level tokens in order. Each token is '
    '{"text", "reading", "is_target"}: reading is the FULL hiragana reading of text, '
    "including any kana already in it (e.g. 新しい → あたらしい; empty when text has no "
    "kanji); is_target is true for the token(s) carrying the target word, even when it "
    "appears in a conjugated form. Include punctuation as its own token. Concatenating "
    "the token texts must reproduce jp exactly."
)

_STYLE_PROMPTS = {
    "casual": "natural, colloquial, everyday spoken Japanese (casual register).",
    "polite": "polite spoken Japanese (です/ます), as used with acquaintances or in service settings.",
    "news": "formal written Japanese in a news / article style.",
    "business": "polite business Japanese (keigo where natural), as in workplace email and meetings.",
    "mixed": "a mix of registers — vary between casual, polite, and formal across the sentences.",
}

_TOPICS = [
    "weather", "work", "school", "food and cooking", "travel", "shopping",
    "money", "health", "family", "friends", "hobbies", "sports", "technology",
    "music", "movies", "daily routine", "weekend plans", "transportation",
    "the news", "nature", "pets", "housing", "feelings", "time and schedules",
]


def build_prompt(
    vocab: str, level: str, n: int, furigana: bool, style: str, topics: str
) -> tuple[str, str]:
    system = _SYSTEM_FURIGANA if furigana else _SYSTEM_PLAIN
    register = _STYLE_PROMPTS.get(style, _STYLE_PROMPTS["casual"])
    user = (
        f"Target vocabulary word: {vocab}\n"
        f"Learner level: {level}\n"
        f"Register: {register}\n"
        f"Draw on a range of everyday situations (e.g. {topics}); use a different one "
        f"for each sentence.\n"
        f"Generate {n} distinct sentences."
    )
    return system, user

def _sample_topics(n: int) -> list[str]:
    return random.sample(_TOPICS, min(max(n, 4), len(_TOPICS)))

def generate_sentences(vocab: str, level: str, n: int) -> list[dict]:
    furigana = config.get_furigana_mode() != "off"
    style = config.get_style()
    topics = ", ".join(_sample_topics(n))
    system, user = build_prompt(vocab, level, n, furigana, style, topics)
    per_item = 350 if furigana else 80
    max_tokens = max(1024, n * per_item + 256)
    raw = llm.get_provider().complete(system, user, max_tokens=max_tokens)
    data = _load_array(raw)
    return _parse_furigana(data) if furigana else _parse_plain(data)

def _load_array(text: str) -> list:
    cleaned = _strip_code_fences(text.strip())
    try:
        data = json.loads(cleaned)
    except ValueError as err:
        raise llm.LLMError(tr("err.bad_format")) from err
    if not isinstance(data, list):
        raise llm.LLMError(tr("err.bad_format"))
    return data

def _parse_plain(data: list) -> list[dict]:
    items = [
        {"jp": str(e["jp"]), "en": str(e.get("en", "")), "tokens": None}
        for e in data
        if isinstance(e, dict) and e.get("jp")
    ]
    if not items:
        raise llm.LLMError(tr("err.no_sentences"))
    return items

def _parse_furigana(data: list) -> list[dict]:
    items: list[dict] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        tokens = _clean_tokens(entry.get("tokens"))
        jp = str(entry.get("jp", "")).strip() or "".join(t["text"] for t in tokens)
        if not jp:
            continue
        if tokens and "".join(t["text"] for t in tokens) != jp:
            tokens = None
        items.append({"jp": jp, "en": str(entry.get("en", "")), "tokens": tokens})
    if not items:
        raise llm.LLMError(tr("err.no_sentences"))
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

def _split_runs(text: str) -> list[tuple[str, bool]]:
    runs: list[tuple[str, bool]] = []
    for ch in text:
        is_kanji = bool(_KANJI.match(ch))
        if runs and runs[-1][1] == is_kanji:
            runs[-1] = (runs[-1][0] + ch, is_kanji)
        else:
            runs.append((ch, is_kanji))
    return runs

def _align_furigana(text: str, reading: str):
    runs = _split_runs(text)
    out = []
    ri = 0
    for i, (sub, is_kanji) in enumerate(runs):
        if not is_kanji:
            if reading[ri:ri + len(sub)] != sub:
                return None
            out.append((sub, None))
            ri += len(sub)
        else:
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
                return None
            out.append((sub, kana))
    return out if ri == len(reading) else None

def _wrap(mode: str, template: str, kanji: str, reading: str) -> str:
    if mode == "ruby":
        return f"<ruby>{kanji}<rt>{reading}</rt></ruby>"
    return template.replace("{kanji}", kanji).replace("{reading}", reading)

def render(tokens: list[dict], target: str) -> str:
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
            parts.append(_wrap(mode, template, text, reading))
        else:
            parts.append(
                "".join(
                    sub if kana is None else _wrap(mode, template, sub, kana)
                    for sub, kana in segments
                )
            )
    return "".join(parts)
