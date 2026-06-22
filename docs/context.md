Project Brief: Agentic Anki Japanese Tutor (Python Plugin)
Role & Goal
You are an expert Python developer specializing in Anki Add-on development (aqt library) and LLM integration. The goal is to build an Anki plugin that acts as a dynamic Japanese language tutor using RAG (Retrieval Augmented Generation).

Tech Stack
Language: Python 3.
Framework: Anki Add-on API (aqt, anki modules).
AI/LLM: OpenAI API (GPT-4o) for generation; ChromaDB or FAISS for local vector storage.
External Data: Tatoeba, Tanaka Corpus, and user-provided textbook data (PDF/Text).
Core Feature: "On-Demand Contextual Examples"
UX Flow: During Anki review, the user highlights a Japanese word/phrase and presses a hotkey (Ctrl+E).
The Trigger: A non-blocking pop-up window (styled like Anki's editor) appears.
Agentic RAG Pipeline:
Retrieval: Use the highlighted text to query a vector DB of Japanese sentences/grammar rules.
Augmentation: Construct a prompt containing: [Highlighted Word] + [Card Context] + [User Level (e.g., N3)] + [Retrieved Examples from DB].
Generation: LLM generates 3 unique, level-appropriate example sentences with English translations.
Action: The pop-up displays the results. Each result has a "Save" button.
Persistence: Clicking "Save" appends the formatted HTML (with custom CSS classes) to a configurable target field on the current note.
Initial Technical Requirements (Sprint 1)
Create the boilerplate for an Anki Add-on.
Register a global hotkey (Ctrl+E) active during the Reviewer state.
Implement a method to grab the currently selected text from the Reviewer's webview.
Create a basic Qt Dialog (pop-up) to display placeholder text.
Add a settings menu in Anki to configure the "Target Field Name" for saving sentences.
Design Pattern for Copilot
Use Async/Await or Threads for API calls to prevent UI freezing in Anki.
Wrap saved content in <div class="ai-generated-example"> tags for user-side CSS styling.