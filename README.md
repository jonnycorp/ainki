# ainki - Anki用AI日本語文章生成アドオン

> *Anki AI Japanese Sentence Generator Add-on*

<!-- TODO: add screenshot / GIF of plugin generating  -->

## 🏯 Core Function

Ever wanted more colloquial example sentences for a Japanese word while studying on **Anki**? This add-on, `ainki`, generates as many new examples as you want and lets you add them directly to your card—all mid-session, without leaving Anki or spending time mining yourself.


## 🎍 Features

- **Reviewer Shortcut** — set whatever hotkey you like to open the generator during review
- **Explicit Generation** — no API calls made until you want to and click *Generate*
- **Infinite Generation** — keep getting new sentences until you're satisfied
- **Selective Injection** — choose exactly which sentences get saved, or just save them all
- **Furigana Assistance** — generated sentences come with furigana on all other kanji, or you can turn it off if you're really good
- **Per-Note Mapping** — decide exactly where the target word is and where sentences should be added—per field, per note type
- **Model Agnostic** — use the best model that works to your learning benefit (currently only *Anthropic* but other providers coming soon) <!-- TODO: update when other providers are actually implemented -->

## 🍙 Requirements

- Anki 25.x+ (desktop)
- An API key from a supported provider below:
    - Anthropic (Claude)

## 🏮 Installation

<!-- TODO: fill in AnkiWeb add-on code once published -->

**From AnkiWeb (recommended):**
1. In Anki: *Tools → Add-ons → Get Add-ons*
2. Paste the add-on code: `whoops not there yet`

**Manual install into local Anki:**
1. Clone the repo locally
2. Copy just the `addon/` folder into your local Anki `addons21` directory
   - Mac: `~/Library/Application\ Support/Anki2/addons21/`
   - Windows: `%APPDATA%\Anki2\addons21\`
3. Restart Anki

> For full development setup and live edit support, see **Development** section below


## 🗻 Configuration

<!-- TODO: Finish after dev -->

## 🗼 Usage

It's super easy, just 3 steps:
1. Review your settings in *Tools → ainki Settings* (make sure to add your API Key)
2. Open a deck and input your hotkey when you want to see some sentences
3. Click *Generate* and start learning!

## 🚅 Development

Local development uses a symlink so edits are picked up on Anki restart (no need to constantly copy the folder). For Mac, it looks something like this:

```bash
# Clone
git clone https://github.com/jonnycorp/ainki.git
cd ainki

# Symlink the add-on folder into Anki's addons21 directory
ln -s "$(pwd)/addon" ~/Library/Application\ Support/Anki2/addons21/ainki

# Launch Anki from the terminal to see logs
/Applications/Anki.app/Contents/MacOS/launcher
```

Quick overview of project structure:

```
ainki/                            # repo root
├── addon/                        # the add-on
│   ├── __init__.py               # hotkey + menu entry
│   ├── config.py                 # addonManager wrapper
│   ├── config.json               # default config
│   ├── llm.py                    # BYOK provider layer
│   ├── generation.py             # where the magic is
│   └── ui/                       # Qt dialogs
│       ├── sentence_dialog.py    # generation popup
│       └── settings_dialog.py    # settings popup
└── ...                           # repo stuff
```

## 🍜 License

Licensed under **AGPL-3.0-or-later**, what Anki wants.

<!-- Copyright (C) 2026 TODO: your name / handle -->
