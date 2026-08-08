"""
all generation logic
"""

import json
import random
import re
import unicodedata

from . import config, llm
from .i18n import tr


_KANJI = re.compile(r"[㐀-䶿一-鿿々]")

_RULES = (
    "Rules:\n"
    "- Natural, grammatically correct Japanese in the requested register, at or below "
    "the stated level; when unsure whether a grammar point sits above the level, choose "
    "the simpler construction.\n"
    "- Use the target word itself, inflected however the sentence needs (頼る → 頼って, "
    "頼らない, 頼れば). Never substitute a different word that merely shares a kanji — for "
    "頼る, 頼む is a separate verb. A する-noun counts as a noun or with する "
    "(編集が上手 / 編集した).\n"
    "- The target word must be what the sentence is about, not a bystander in it. A "
    "compound counts when the compound is the point (細かい編集作業は大変だ); it does not "
    "when the compound is incidental — typically a job title on someone doing something "
    "unrelated (編集長が値上げを発表した is about a price rise, not editing).\n"
    "- Japanese script only: kanji, hiragana, katakana. Foreign words and brand names "
    "go in katakana; never use the latin alphabet or any other writing system.\n"
    "- No two sentences may share a situation or a sentence pattern.\n\n"
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

_LENGTH_PROMPTS = {
    "short": "short and punchy — one clause, roughly 8-15 Japanese characters.",
    "medium": "everyday length — one or two clauses, roughly 15-30 Japanese characters.",
    "long": "fuller context — two or more clauses that set up a situation, roughly 30-50 "
    "Japanese characters, still one sentence.",
}

_LENGTH_TOKEN_SCALE = {"short": 0.6, "medium": 1.0, "long": 1.6}

_FRAMES = [
    "a plain statement",
    "a question",
    "a negative statement",
    "past tense",
    "a conditional (〜たら / 〜ば)",
    "an invitation or suggestion",
    "a line of quoted dialogue",
    "expressing intent or desire",
    "giving a reason (〜から / 〜ので)",
    "a passive or causative construction",
]


_EST_INPUT = 650
_EST_OUT_FURIGANA = 420
_EST_OUT_PLAIN = 70


def estimate_per_sentence(n: int, furigana: bool, model: str, length: str = "medium"):
    """rough usd for one sentence at these settings, None if the model has no price"""
    out = _EST_OUT_FURIGANA if furigana else _EST_OUT_PLAIN
    out *= _LENGTH_TOKEN_SCALE.get(length, 1.0)
    return llm.cost_usd(_EST_INPUT / max(n, 1), out, model)


def build_prompt(
    vocab: str,
    level: str,
    n: int,
    furigana: bool,
    style: str,
    topics: str,
    frames: str,
    avoid: list = None,
    length: str = "medium",
) -> tuple[str, str]:
    system = _SYSTEM_FURIGANA if furigana else _SYSTEM_PLAIN
    register = _STYLE_PROMPTS.get(style, _STYLE_PROMPTS["casual"])
    user = (
        f"Target vocabulary word: {vocab}\n"
        f"Learner level: {level}\n"
        f"Register: {register}\n"
        f"Length: {_LENGTH_PROMPTS.get(length, _LENGTH_PROMPTS['medium'])}\n"
        f"Draw on a range of everyday situations (e.g. {topics}); use a different one "
        f"for each sentence.\n"
        f"Vary the grammar too — across the set use forms such as: {frames}.\n"
    )
    if avoid:
        listed = "\n".join(f"- {s}" for s in avoid)
        user += (
            "\nThese sentences already exist for this word. Do not repeat them, and do "
            "not reuse their situations, sentence patterns, or phrasing — every new "
            "sentence must be clearly distinct from all of them:\n"
            f"{listed}\n"
        )
    user += f"\nGenerate {n} distinct sentences."
    return system, user

def _sample_topics(n: int) -> list[str]:
    return random.sample(_TOPICS, min(max(n, 4), len(_TOPICS)))

def _sample_frames(n: int) -> list[str]:
    return random.sample(_FRAMES, min(max(n, 3), len(_FRAMES)))

def generate_sentences(vocab: str, level: str, n: int, avoid: list = None) -> tuple:
    """returns (items, usage)

    avoid holds sentences already on screen so a regenerate can't repeat them
    """
    furigana = config.get_furigana_mode() != "off"
    style = config.get_style()
    length = config.get_sentence_length()
    topics = ", ".join(_sample_topics(n))
    frames = ", ".join(_sample_frames(n))
    system, user = build_prompt(
        vocab, level, n, furigana, style, topics, frames, avoid, length
    )
    # measured ~490 out per furigana sentence, cap generously: unused headroom is free
    per_item = 700 if furigana else 150
    per_item *= _LENGTH_TOKEN_SCALE.get(length, 1.0)
    max_tokens = int(max(2048, n * per_item + 512))
    raw, usage = llm.get_provider().complete(system, user, max_tokens=max_tokens)
    data = _load_array(raw)
    items = _parse_furigana(data) if furigana else _parse_plain(data)
    return items, usage

def _is_japanese(text: str) -> bool:
    """every letter must be kana or kanji

    the model samples from one multilingual vocabulary, so it rarely slips a latin
    or cyrillic word into an otherwise japanese sentence; a prompt rule cannot make
    that never happen, so drop those sentences here. digits and punctuation pass
    """
    for ch in text:
        if not ch.isalpha():
            continue
        name = unicodedata.name(ch, "")
        if not any(k in name for k in ("CJK", "HIRAGANA", "KATAKANA")):
            return False
    return True


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
        if isinstance(e, dict) and e.get("jp") and _is_japanese(str(e["jp"]))
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
        if not jp or not _is_japanese(jp):
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
