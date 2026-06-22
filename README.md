# ainki - Anki用AI日本語文章生成アドオン

> *Anki AI Japanese Sentence Generator Add-on*

<!-- TODO: add screenshot / GIF of plugin generating  -->

## 🏯 Core Function

Have you ever wanted to see another colloquial example sentence for a Japanese word or phrase you've been studying on **Anki**? This add-on, `ainki`, allows you to see as many new examples as you want, and add any that you like directly to the card, all mid-session.

## 🎍 Features

- **Reviewer Shortcut** — set whatever shortcut keybind you like to open the generator during review
- **Explicit Generation** — no API calls until you want to click *Generate*
- **Infinite Generation** — keep getting new sentences until you're satisfied
- **Selective Injection** — choose exactly which sentences get saved, or just save them all
- **Per-Note Mapping** — choose exactly where the target word and sentences should append to, per field, per note type
- **Model Agnostic** — use the best model that works to your learning benefit (works with OpenAI, Anthropic, and Google Gemini) <!-- TODO: update as providers are actually implemented -->

## 🍙 Requirements

- Anki <!-- TODO: confirm minimum supported version, e.g. 25.x --> (desktop)
- An API key from a supported provider

## 🏮 Installation

<!-- TODO: fill in AnkiWeb add-on code once published -->

**From AnkiWeb (recommended):**
1. In Anki: *Tools → Add-ons → Get Add-ons*
2. Paste the add-on code: `TEMP`

**Manual / development install:** see [Development](#development).

## 🗻 Configuration

<!-- TODO: Finish after dev -->

## 🗼 Usage

1. Start reviewing any deck
2. Input your shortcut
3. Confirm the detected vocab word or phrase
4. Click *Generate*; pick the sentences you want
5. Click *Add to Card*

## 🚅 Development

Local development uses a symlink so edits are picked up on Anki restart (no copy step).

```bash
# Clone
git clone https://github.com/TODO/ainki.git
cd ainki

# Symlink the add-on folder into Anki's addons directory (macOS path shown)
ln -s "$(pwd)/addon" ~/Library/Application\ Support/Anki2/addons21/ainki

# Launch Anki from the terminal to see stdout / tracebacks
# (newer Anki builds launch via 'launcher', not 'anki')
/Applications/Anki.app/Contents/MacOS/launcher
```

Anki must be fully restarted to reload add-on code — there is no hot reload.

```
ainki/                  # repo root
├── addon/              # the add-on itself
│   ├── __init__.py     # entry point for shortcut
│   ├── config.py       # Anki's addonManager config
│   ├── config.json     # default config
│   ├── meta.json       # manifest
│   └── ui/             # dialogs
└── ...                 # repo stuff
```

<!-- TODO: expand once the AI provider layer and settings UI land -->

## 🍜 License

Licensed under **AGPL-3.0-or-later**, what Anki wants.

<!-- Copyright (C) 2026 TODO: your name / handle -->
