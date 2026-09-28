"""drive the addon's real generation pipeline outside anki

usage: probe.py --word 編集 --model claude-haiku-4-5 [--n 5] [--avoid-from FILE]
"""
import argparse
import importlib.util
import json
import ssl
import sys
import types
import urllib.request
from pathlib import Path

# this python has no CA bundle wired up; anki ships its own so the addon is fine
import certifi

_ctx = ssl.create_default_context(cafile=certifi.where())
urllib.request.install_opener(
    urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx))
)

ADDON = Path("/Users/jyma/Projects/ainki/addon")

ap = argparse.ArgumentParser()
ap.add_argument("--word", required=True)
ap.add_argument("--model", default="claude-haiku-4-5")
ap.add_argument("--n", type=int, default=5)
ap.add_argument("--level", default="N3")
ap.add_argument("--style", default="casual")
ap.add_argument("--furigana", default="ruby")
ap.add_argument("--avoid", nargs="*", default=[])
ap.add_argument("--show-prompt", action="store_true")
ap.add_argument("--length", default="medium")
args = ap.parse_args()

key = json.loads((ADDON / "meta.json").read_text())["config"]["api_key"]
store = {
    "provider": "anthropic",
    "api_key": key,
    "model": args.model,
    "level": args.level,
    "style": args.style,
    "num_sentences": args.n,
    "furigana_mode": args.furigana,
    "sentence_length": args.length,
    "furigana_template": "{kanji}[{reading}]",
    "language": "en",
}

aqt = types.ModuleType("aqt")
aqt.mw = types.SimpleNamespace(
    addonManager=types.SimpleNamespace(
        getConfig=lambda p: store, writeConfig=lambda p, c: None
    )
)
sys.modules["aqt"] = aqt


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pkg = types.ModuleType("addon")
pkg.__path__ = [str(ADDON)]
sys.modules["addon"] = pkg
load("addon.config", ADDON / "config.py")
load("addon.i18n", ADDON / "i18n.py")
llm = load("addon.llm", ADDON / "llm.py")
gen = load("addon.generation", ADDON / "generation.py")

if args.show_prompt:
    s, u = gen.build_prompt(
        args.word, args.level, args.n, args.furigana != "off", args.style,
        ", ".join(gen._sample_topics(args.n)), ", ".join(gen._sample_frames(args.n)),
        args.avoid,
    )
    print("=== SYSTEM ===\n" + s + "\n\n=== USER ===\n" + u + "\n")

items, usage = gen.generate_sentences(args.word, args.level, args.n, args.avoid)

print(f"### {args.word}  |  {args.model}  |  {args.style} / {args.level} / n={args.n}"
      + (f"  |  avoiding {len(args.avoid)}" if args.avoid else ""))
print()
for i, it in enumerate(items, 1):
    print(f"{i}. {it['jp']}")
    print(f"   {it['en']}")
    if it.get("tokens"):
        print(f"   furigana: {gen.render(it['tokens'], args.word)}")
    print()

tin = usage.get("input_tokens", 0)
tout = usage.get("output_tokens", 0)
cost = llm.cost_usd(tin, tout, args.model)
print(f"tokens: {tin} in / {tout} out"
      + (f"  |  {cost*100:.2f}¢  ({cost/max(len(items),1)*100:.2f}¢ per sentence)"
         if cost is not None else ""))
