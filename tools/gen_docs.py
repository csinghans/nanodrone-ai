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


def rewrite_links(text: str, lesson_dir: str) -> str:
    # Demo media (../../assets/x) -> raw.githubusercontent URL.
    text = re.sub(r"\]\(\.\./\.\./assets/([^)]+)\)", rf"]({RAW}/assets/\1)", text)

    # Remaining relative links are code files in the lesson folder -> blob URL.
    def repl(m):
        target = m.group(1)
        if target.startswith(("http", "#")):
            return m.group(0)
        return f"]({BLOB}/lessons/{lesson_dir}/{target})"

    return re.sub(r"\]\(([^)]+)\)", repl, text)


def _strip_lang_lines(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if "🌐" not in ln)


def main() -> None:
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
                f.write(rewrite_links(body, lesson_dir))
            print(f"  wrote docs/{sub}/{docs_name}")


if __name__ == "__main__":
    main()
