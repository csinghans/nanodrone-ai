#!/usr/bin/env python3
"""Generate the bilingual docs-site pages from each lesson's README.

The lesson README (lessons/NN_slug/README.md) is the SINGLE source of truth: it
holds the English and 繁體中文 sections in one file, split by the `中文` anchor.
This script writes docs/en/NN-slug.md and docs/zh-TW/NN-slug.md from it (build
artifacts, git-ignored), dropping the in-page language switch and rewriting
repo-relative links (demo media, code files) to absolute GitHub URLs so they
resolve on the published site.

Run:  python tools/gen_docs.py        (the docs deploy workflow runs this too)
"""

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "https://raw.githubusercontent.com/csinghans/nanodrone-ai/main"
BLOB = "https://github.com/csinghans/nanodrone-ai/blob/main"
ANCHOR = '<a name="中文"></a>'


def rewrite_links(text: str, base: str) -> str:
    """Rewrite repo-relative links to absolute GitHub URLs. `base` is the page's
    source dir relative to the repo root (e.g. 'lessons/11_mission')."""
    # Demo media (../../assets/x) -> raw.githubusercontent URL.
    text = re.sub(r"\]\(\.\./\.\./assets/([^)]+)\)", rf"]({RAW}/assets/\1)", text)

    # Remaining relative links resolve against `base` (handles ../.. up to the
    # repo root, e.g. ../../nanodrone/mission.py -> blob/main/nanodrone/...).
    def repl(m):
        target = m.group(1)
        if target.startswith(("http", "#", "/")):
            return m.group(0)
        rel = os.path.normpath(os.path.join(base, target)).replace(os.sep, "/")
        return f"]({BLOB}/{rel})"

    return re.sub(r"\]\(([^)]+)\)", repl, text)


# Bilingual pages outside lessons/ (same README structure): (source, out, base).
EXTRA_PAGES = [
    ("apple/DroneVoice/README.md", "31-dronevoice.md", "apple/DroneVoice"),
]


def _gen_extra() -> None:
    for src, docs_name, base in EXTRA_PAGES:
        with open(os.path.join(ROOT, src), encoding="utf-8") as f:
            text = f.read()
        if ANCHOR not in text:
            continue
        en_raw, zh_raw = text.split(ANCHOR, 1)
        for sub, raw in (("en", en_raw), ("zh-TW", zh_raw)):
            body = _strip_lang_lines(raw).strip() + "\n"
            out = os.path.join(ROOT, "docs", sub, docs_name)
            with open(out, "w", encoding="utf-8") as f:
                f.write(rewrite_links(body, base))
            print(f"  wrote docs/{sub}/{docs_name}")


def _strip_lang_lines(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if "🌐" not in ln)


# Lesson 0 is "setup" (no lesson folder); cost overrides keyed by number.
SETUP = {"en": "Setup & project skeleton", "zh-TW": "環境建置與專案骨架"}
COST = {"04": {"en": "~US$545", "zh-TW": "約 US$545"}}
HEADER = {
    "en": "| Lesson | Topic | Cost |\n|--------|-------|------|",
    "zh-TW": "| 課程 | 主題 | 成本 |\n|------|------|------|",
}
BONUS = {"en": " *(bonus)*", "zh-TW": " *(加成)*"}


def _title(section: str) -> str:
    """Topic from an H1 like '# Lesson 6 — Follow-me tracking' -> after the dash."""
    h1 = next((ln for ln in section.splitlines() if ln.startswith("# Lesson")), "")
    return h1.split("—")[-1].strip() if "—" in h1 else h1.lstrip("# ").strip()


def _inject_table(lang: str, rows: list) -> None:
    body = [HEADER[lang]]
    body.append(f"| 0 | [{SETUP[lang]}](00-overview.md) | $0 |")
    for nn, docs_name, title, bonus in rows:
        cost = COST.get(nn, {}).get(lang, "$0")
        num = nn.lstrip("0") + (BONUS[lang] if bonus else "")
        body.append(f"| {num} | [{title}]({docs_name}) | {cost} |")
    table = "\n".join(body)
    path = os.path.join(ROOT, "docs", lang, "index.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(
        r"<!-- LESSON-TABLE:START -->.*?<!-- LESSON-TABLE:END -->",
        f"<!-- LESSON-TABLE:START -->\n{table}\n<!-- LESSON-TABLE:END -->",
        text,
        flags=re.DOTALL,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"  updated docs/{lang}/index.md table")


def main() -> None:
    rows_by_lang = {"en": [], "zh-TW": []}
    for readme in sorted(glob.glob(os.path.join(ROOT, "lessons", "*", "README.md"))):
        lesson_dir = os.path.basename(os.path.dirname(readme))  # e.g. 01_hover
        nn, slug = lesson_dir.split("_", 1)
        docs_name = f"{nn}-{slug.replace('_', '-')}.md"
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        if ANCHOR not in text:
            continue
        en_raw, zh_raw = text.split(ANCHOR, 1)

        # The demo media line lives in the English part; show it on both pages.
        media = next((ln for ln in en_raw.splitlines() if ln.startswith("![")), "")
        en = _strip_lang_lines(en_raw).strip() + "\n"
        zh = _strip_lang_lines(zh_raw).strip()
        if media and media not in zh:  # inject media after the zh H1
            head, _, rest = zh.partition("\n")
            zh = f"{head}\n\n{media}\n{rest}"
        zh = zh.strip() + "\n"

        for sub, body in (("en", en), ("zh-TW", zh)):
            out = os.path.join(ROOT, "docs", sub, docs_name)
            with open(out, "w", encoding="utf-8") as f:
                f.write(rewrite_links(body, f"lessons/{lesson_dir}"))
            print(f"  wrote docs/{sub}/{docs_name}")

        # Only the H1 marks a bonus lesson (the word may appear in the body too).
        en_h1 = next((x for x in en_raw.splitlines() if x.startswith("# Lesson")), "")
        zh_h1 = next((x for x in zh_raw.splitlines() if x.startswith("# Lesson")), "")
        bonus = "(bonus)" in en_h1.lower() or "加成" in zh_h1
        rows_by_lang["en"].append((nn, docs_name, _title(en_raw), bonus))
        rows_by_lang["zh-TW"].append((nn, docs_name, _title(zh_raw), bonus))

    _gen_extra()
    for lang in ("en", "zh-TW"):
        _inject_table(lang, rows_by_lang[lang])


if __name__ == "__main__":
    main()
