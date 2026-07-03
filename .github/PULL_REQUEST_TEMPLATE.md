## What this changes

<!-- One or two sentences. Link the issue if there is one. -->

## Checklist

- [ ] **Both language halves updated together** (English + 繁體中文 — READMEs
      split on the `<a name="中文"></a>` anchor; docs live in `docs/en/` +
      `docs/zh-TW/`)
- [ ] `--selftest` still prints its `XXX OK` line for every touched script
- [ ] `black` + `ruff check` pass
- [ ] `python tools/gen_docs.py && mkdocs build --strict` passes (if docs/READMEs changed)
- [ ] Within the v1.0 freeze scope (bug fix / docs / CI — see COURSE_COMPLETE.md)
