# CLAUDE.md — ainki

LLM-integrated Anki add-on (Python, BYOK). A hotkey mid-review reads the active
note's fields, generates level-appropriate **colloquial** Japanese, and injects a
chosen sentence back into a target field. Distributed as a zipped add-on on
AnkiWeb under **AGPL-3.0-or-later**.

## Hard platform constraints (do not violate — these override convenience)
1. **Anki ships its own bundled Python.** Do not add heavy or native deps.
   `torch`, `sentence-transformers`, `faiss`, full `chromadb` are non-starters
   (size, platform wheels, C extensions). Prefer stdlib + pure-Python. Justify any
   new dependency and confirm it ships cleanly inside the add-on zip.
2. **Never block Anki's Qt main thread.** A blocking network/LLM call mid-review
   freezes the whole app. Run LLM/network calls off the main thread via Anki's
   background-op API (e.g. `aqt.operations.QueryOp`) with a loading state in the
   popup. Never touch Qt widgets from the worker thread — marshal results back via
   the success callback.
3. **API key storage is plaintext** in add-on config on disk. Acceptable for
   BYOK/personal use, but never imply it's secured. Never log the key, never put
   it in a URL, never commit it.

## Architecture (keep these as separate modules)
- **UI / trigger** — hotkey (`Ctrl+Shift+E`; `Ctrl+E` collides with Anki export)
  opens a popup over the reviewer. Generation is an **explicit button press**, not
  auto-on-open.
- **Card reader** — reads the active note type's fields via **config-driven field
  mapping**. Note types vary wildly per user; never hardcode field names.
- **Generation pipeline** — builds the prompt (card content + level + exemplars)
  → calls the LLM → renders output in the popup.
- **LLM client (BYOK)** — thin provider-agnostic wrapper. Start with one provider;
  keep the interface swappable.
- **Retrieval (RAG)** — *Phase 1, not yet built.* Precomputed embedding index +
  query-time provider embeddings + NumPy cosine. No local model, no vector DB.
- **Config / secrets** — field mapping, level, provider, key. Access via Anki's
  `addonManager` config API.

## Error handling (the two failure-prone seams)
- **Network / LLM:** timeouts, rate limits, bad/expired keys. Fail visibly in the
  popup — never silently, never by freezing.
- **Note-type variability:** missing or renamed mapped fields. Detect and surface
  a clear message; don't crash mid-review.

## Coding standards
- Clean and readable over clever; comment intent, not the obvious.
- Strict separation of concerns (modules above) so new generation modes slot in
  without touching the trigger layer.
- Full working code over pseudocode. Justify library choices vs. alternatives.
- Revenue-grade where it counts (error handling, config-driven design); don't
  gold-plate what a single-user add-on never stresses.

## Project layout
- Repo root holds `README`, license, and this `CLAUDE.md` — these stay **outside**
  the package.
- `addon/` is the flat, droppable Anki package (`__init__.py`, `config.py`,
  `config.json`, `meta.json`, `ui/`). This is what gets zipped for AnkiWeb. **Work
  here.**
- `addon/` is symlinked into Anki's `addons21/` as `ainki` for local testing —
  that symlink lives outside this repo; don't touch it.

## Current state
Boilerplate done and confirmed working: hotkey fires, popup appears (stub dialog).
**Next: the BYOK LLM provider layer + wiring the stub dialog** — read the mapped
field → generate on button press → sentence-selection UI → inject into the target
field.

## Out of scope / parked (don't let these default-settle)
- **No hosted backend, no accounts** — BYOK to the user's own provider only. A
  server would trigger AGPL's network clause and reopen legal questions.
- **Corpus sourcing & legality** (Phase 1) and **donation/revenue legality** are
  parked by my call. Don't bake an assumption about either into a design; flag it
  if a choice forces the question.

## How to work with me
- Concise, answer-first, then explanation. Challenge the approach if there's a
  better one — don't just execute.
- Proactively correct best practice (engineering, security, packaging) even if I
  sound confident; this domain is newer to me than backend.
- Backend SWE, Java background, ~3 YOE; newer to Python and Anki. Flag meaningful
  Python↔Java differences; skip basics.
- One clarifying question only if it materially changes the approach.

## Anki specifics worth knowing
- Anki 25.x launches via `/Applications/Anki.app/Contents/MacOS/launcher`
  (uv-based runtime), not a binary named `anki`.
- Config is read/written through `addonManager`; runtime values land in
  `meta.json`.
