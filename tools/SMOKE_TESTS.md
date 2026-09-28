# v1.0.0 smoke tests

Manual checks before tagging. Nothing here can be verified outside a running Anki.

## A. blockers — a failure here means do not ship

| # | check | why it matters |
|---|---|---|
| A1 | **Tools → ainki Settings opens** | `QKeySequenceEdit` is new and unverified outside Anki. If `aqt.qt` doesn't export it, the dialog raises on open and settings become unreachable |
| A2 | **Restore Defaults doesn't crash** | now indexes `d["key"]` strictly; a key present in the dialog but missing from config.json is a `KeyError` |
| A3 | **Generate → select → Add to Card writes the field** | the core loop |
| A4 | **Reviewer shows the new content** without leaving/re-entering the card | `_after_inject` calls private Anki APIs inside a try/except |
| A5 | **Fresh install works** — move `meta.json` aside, restart, open settings, generate | every default comes only from config.json now; a missing key returns `None` instead of a fallback |
| A6 | **Built .ankiaddon installs** — Tools → Add-ons → Install from file, using `dist/ainki-1.0.0.ankiaddon` | verifies zip layout; do this in a throwaway Anki profile, not your daily one |

## B. changed this session — regression risk

| # | check | why |
|---|---|---|
| B1 | Sentence length short / medium / long visibly differ | new setting |
| B2 | Cost in cents appears after each generation | new label |
| B3 | Settings shows lifetime sentences + spend, and it grows | new persisted counter |
| B4 | Per-sentence estimate updates when changing model / count / furigana / length | wired to four widgets |
| B5 | Hotkey change applies without restart, and the old key stops working | live rebind |
| B6 | Generate More produces different sentences from batch 1 | avoid list |
| B7 | Change the vocab word mid-dialog, then Generate — should not be constrained by the prior word's sentences | avoid list is dropped when the word changes |
| B8 | Your existing config still loads (old `meta.json` has stale keys) | new keys merge under Anki's config merge |

## C. error paths — should show a clear message, never a traceback

| # | check |
|---|---|
| C1 | Empty API key → "No API key set" |
| C2 | Wrong API key (edit to garbage) → "Invalid or expired API key" |
| C3 | Airplane mode / wifi off → network error message |
| C4 | Note type whose mapped field doesn't exist → field-not-found warning naming the fields |
| C5 | Click Generate with an empty vocab box → "Enter a vocab word" |
| C6 | Unknown model (type `claude-fake-9`) → API error surfaced, and no cost figures shown anywhere |

## D. settings matrix — each should visibly change output

| # | check |
|---|---|
| D1 | furigana ruby → readings render as ruby in the card |
| D2 | furigana custom, template `{kanji}[{reading}]` → bracket form in the field |
| D3 | furigana off → no readings, and no ruby markup in the field |
| D4 | write mode append → adds below existing content using the separator |
| D5 | write mode overwrite → replaces the field |
| D6 | separator `<br><br>` → visible blank line between sentences |
| D7 | n = 1 and n = 20 → both complete without truncation |
| D8 | style casual vs business → register visibly differs |
| D9 | language ja → whole UI in Japanese, incl. the new length/cost rows |
| D10 | font size 8 vs 48 → candidate list scales |

## E. per-sentence interactions

| # | check |
|---|---|
| E1 | Double-click a sentence, edit it, Add → the edited text lands verbatim (furigana intentionally skipped for edited rows) |
| E2 | Right-click → Revert restores the original |
| E3 | Select several, Add → all land in list order with separators |
| E4 | Select all button, then Add |
| E5 | Cancel closes without writing anything |

## F. cross-platform / packaging

| # | check |
|---|---|
| F1 | Window geometry persists across close/reopen |
| F2 | Windows, if you have access — `saveGeom`/`restoreGeom` and the hotkey widget are the platform-sensitive parts |
| F3 | Confirm the installed add-on folder has **no meta.json from the zip** (your key must not travel) |

## known non-blocking issues

- Japanese UI strings have never had a native-speaker pass
- Model prices are hardcoded and will drift; unknown models correctly show tokens only, no dollar figure
- Latin text is filtered out of generated sentences, so a legitimate `Tシャツ` or `PC` sentence would be dropped rather than shown
