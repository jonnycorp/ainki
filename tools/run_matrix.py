"""run the addon's real pipeline across words x models, emit a markdown report"""
import importlib.util
import json
import ssl
import sys
import types
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import certifi

_ctx = ssl.create_default_context(cafile=certifi.where())
urllib.request.install_opener(
    urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx))
)

ADDON = Path("/Users/jyma/Projects/ainki/addon")
key = json.loads((ADDON / "meta.json").read_text())["config"]["api_key"]
store = {
    "provider": "anthropic", "api_key": key, "model": "claude-haiku-4-5",
    "level": "N3", "style": "casual", "num_sentences": 5,
    "furigana_mode": "ruby", "sentence_length": "long", "furigana_template": "{kanji}[{reading}]", "language": "en",
}
aqt = types.ModuleType("aqt")
aqt.mw = types.SimpleNamespace(addonManager=types.SimpleNamespace(
    getConfig=lambda p: store, writeConfig=lambda p, c: None))
sys.modules["aqt"] = aqt


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


pkg = types.ModuleType("addon")
pkg.__path__ = [str(ADDON)]
sys.modules["addon"] = pkg
load("addon.config", ADDON / "config.py")
load("addon.i18n", ADDON / "i18n.py")
llm = load("addon.llm", ADDON / "llm.py")
gen = load("addon.generation", ADDON / "generation.py")

WORDS = ["編集", "頼る", "微妙", "影響", "きっかけ", "覚える"]
GLOSS = {
    "編集": "editing (suru-noun)", "頼る": "to rely on (godan verb)",
    "微妙": "subtle / iffy (na-adj)", "影響": "influence (abstract noun)",
    "きっかけ": "trigger, occasion (kana only)", "覚える": "to memorize / feel (ichidan verb)",
}
total = [0.0]
out = []


def run(word, model, avoid=None, label=""):
    try:
        items, usage = gen.generate_sentences(word, "N3", 5, avoid or [])
    except Exception as e:
        return f"\n**{word} — {model}{label}**\n\nFAILED: {e}\n"
    tin, tout = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    cost = llm.cost_usd(tin, tout, model)
    total[0] += cost or 0
    lines = [f"\n**{word} — {model}{label}**  ({tin} in / {tout} out"
             + (f" · {cost*100:.2f}¢)" if cost else ")")]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. {it['jp']}")
        lines.append(f"   _{it['en']}_")
    return "\n".join(lines) + "\n"


for model in ["claude-haiku-4-5", "claude-sonnet-5"]:
    store["model"] = model
    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(lambda w: run(w, model), WORDS))
    for w, r in zip(WORDS, results):
        out.append((w, r))

# opus control on the two words most prone to failure
store["model"] = "claude-opus-5"
with ThreadPoolExecutor(max_workers=2) as ex:
    ctrl = list(ex.map(lambda w: run(w, "claude-opus-5"), ["編集", "影響"]))
for w, r in zip(["編集", "影響"], ctrl):
    out.append((w, r))

report = ["# matrix — N3 / casual / n=5 / long\n"]
for w in WORDS:
    report.append(f"\n---\n\n## {w} — {GLOSS[w]}")
    for word, r in out:
        if word == w:
            report.append(r)

# generate-more check on the word that showed repetition
store["model"] = "claude-sonnet-5"
first, _ = gen.generate_sentences("誘導", "N3", 5, [])
avoid = [i["jp"] for i in first]
report.append("\n---\n\n## 誘導 — Generate More check (avoid list active)\n")
report.append("\n**batch 1**\n")
for i, it in enumerate(first, 1):
    report.append(f"{i}. {it['jp']}\n   _{it['en']}_")
report.append(run("誘導", "claude-sonnet-5", avoid, label=" · batch 2, avoiding batch 1"))

report.append(f"\n---\n\n**total spend: {total[0]*100:.1f}¢**")
(Path(__file__).parent / "last_matrix.md").write_text("\n".join(report))
print("\n".join(report))
