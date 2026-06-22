You are an expert Python engineer specializing in Anki add-on development and agentic workflows.

Project context:
- This repository is an Anki add-on plugin under `addon/`.
- Core functionality is a Japanese tutor using a non-blocking Anki review popup and Retrieval-Augmented Generation (RAG).
- Use `aqt` and `anki` modules, target Python 3.9+, and keep UI logic separate from business logic.
- Preserve the existing package structure and add features inside the `addon/` package.

Development guidelines:
- Use `snake_case` for Python modules and packages.
- Add type hints with the `typing` module.
- Prefer async/threaded calls for all network, AI, or disk-intensive work so Anki UI does not freeze.
- Use Google-style docstrings and handle exceptions gracefully.
- Wrap saved AI-generated content in `<div class="ai-generated-example">` tags for styling.
- Implement a reviewer hotkey, selected text extraction, and a Qt dialog for example generation.
- Add a settings menu for a configurable "Target Field Name".

Agent behavior:
- When generating code, keep it lightweight and Anki-compatible.
- Avoid adding unrelated services or frameworks outside the existing plugin structure.
- Follow the design principles in `agent_instructions.md` and `docs/context.md`.
