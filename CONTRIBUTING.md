# Contributing to nanodrone-ai

🌐 **English** · [繁體中文](CONTRIBUTING.zh-TW.md)

Thanks for helping make edge-AI drones approachable for beginners! This project is a *teaching* repo, so clarity matters as much as correctness.

## Ways to contribute

- **Fix or improve a lesson** — clearer explanations, better diagrams, working code.
- **Review translations** — flag anything in the Traditional Chinese version that drifted from the English source (or vice versa).
- **Report problems** — open an issue if a command, install step, or script doesn't work on your machine (tell us your macOS version and chip).
- **Add a lesson** — propose it in an issue first so we can agree on scope and ordering.

## Bilingual rule (important)

Every doc and lesson exists in **two languages**:

- **English is the source language.** Write or change the English version first.
- The **Traditional Chinese (`zh-TW`)** version follows. When you change an English file, either update its `zh-TW` counterpart in the same PR or add the label `needs-translation` so a reviewer can.
- File pairing convention:
  - `README.md` ↔ `README.zh-TW.md`
  - `docs/en/NN-topic.md` ↔ `docs/zh-TW/NN-topic.md` (same number + slug)
  - `lessons/<name>/README.md` contains both languages, English section first.

A CI check verifies that every `docs/en/*.md` has a matching `docs/zh-TW/*.md`.

## Lesson structure

Keep the five-part shape so the course stays predictable for beginners:

1. **Why** — what problem this lesson solves and why it matters.
2. **Concept** — the idea, explained for someone seeing it for the first time.
3. **Hands-on** — complete, runnable code (no "left as an exercise" gaps).
4. **Checkpoint** — a concrete, observable success condition.
5. **Going further** — optional links and challenges.

## Code style

- Python: format with `black`, lint with `ruff`. Prefer clear names over clever ones.
- Comments explain *why*, not *what*. Assume the reader is new to robotics.
- Keep scripts runnable on their own (a beginner should be able to `python lessons/<x>/<script>.py`).

## Pull requests

1. Fork and branch (`git checkout -b lesson-2-fix`).
2. Make the change in English first, then `zh-TW`.
3. Run `ruff check . && black --check .` locally.
4. Open the PR describing *what changed* and *why*, and whether translations are in sync.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be kind; many readers are learning.
