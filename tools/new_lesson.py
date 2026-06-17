#!/usr/bin/env python3
"""
Scaffold a new nanodrone-ai lesson in one command.

Creates the lesson folder (with a runnable hover skeleton), a bilingual
five-part README, and the two docs pages (en + zh-TW). It then prints the few
snippets you still paste by hand (mkdocs nav, the README learning-path rows,
and a CI smoke step) -- see CONTRIBUTING's "Adding a lesson" checklist.

Usage:
  python tools/new_lesson.py <NN> <slug> "<Title>"
  python tools/new_lesson.py 06 follow_me "Follow-me tracking"
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPT_TEMPLATE = '''\
"""
%%HEADING%%
%%UNDERLINE%%
TODO: one paragraph on what this lesson teaches and why.

This file is a scaffold: right now it just hovers. Replace the body with your
lesson. It already supports --headless so CI can smoke-test it.

Run:  python lessons/%%DIR%%/%%SLUG%%.py
"""

import sys
import time

import numpy as np
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

TARGET = np.array([0.0, 0.0, 1.0])
DURATION_SEC = 3


def main(gui: bool = True) -> None:
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0.0, 0.0, 0.1]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    action = np.zeros((1, 4))
    start = time.time()
    for i in range(DURATION_SEC * env.CTRL_FREQ):
        obs, _, _, _, _ = env.step(action)
        # TODO: your lesson's "decide" logic goes here.
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=TARGET
        )
        if gui:
            env.render()
            sync(i, start, env.CTRL_TIMESTEP)
    env.close()
    print("Lesson %%NN%% scaffold OK (replace me).")


if __name__ == "__main__":
    main(gui="--headless" not in sys.argv)
'''

README_TEMPLATE = """\
# Lesson %%NN%% — %%TITLE%%

🌐 **English** (below) · [跳到繁體中文](#中文)

![Lesson %%NN%% demo](../../assets/lesson%%NN%%.gif)

---

## Why

TODO: what problem this lesson solves and why it matters.

## Concept

TODO: the idea, explained for a first-timer.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/%%DIR%%/%%SLUG%%.py            # opens a window
python lessons/%%DIR%%/%%SLUG%%.py --headless # no window (CI)
```

TODO: point at the key function(s) in [`%%SLUG%%.py`](%%SLUG%%.py).

## Checkpoint ✅

TODO: a concrete, observable success condition.

## Going further

- TODO: an optional extension or challenge.

---

<a name="中文"></a>
# Lesson %%NN%% — %%TITLE%%

🌐 [English](#lesson-%%NN%%--%%ANCHOR%%) · **繁體中文**（以下）

## 為什麼

TODO：這一課解決什麼問題、為何重要。

## 概念

TODO：把觀念講給第一次接觸的人聽。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/%%DIR%%/%%SLUG%%.py            # 開視窗
python lessons/%%DIR%%/%%SLUG%%.py --headless # 不開視窗（CI 用）
```

TODO：指出 [`%%SLUG%%.py`](%%SLUG%%.py) 裡的核心函式。

## 驗收 ✅

TODO：具體、可觀察的成功條件。

## 延伸

- TODO：選讀延伸或挑戰。
"""

DOC_EN_TEMPLATE = """\
# Lesson %%NN%% — %%TITLE%%

**Goal:** TODO one-sentence goal.

TODO: a short paragraph summarizing the lesson.

**Run**

```bash
python lessons/%%DIR%%/%%SLUG%%.py
```

**Checkpoint ✅** TODO observable success condition.

➡️ Full lesson (code + walkthrough): [lessons/%%DIR%%](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/%%DIR%%)
"""

DOC_ZH_TEMPLATE = """\
# Lesson %%NN%% — %%TITLE%%

**目標：** TODO 一句話目標。

TODO：用一小段話總結這一課。

**執行**

```bash
python lessons/%%DIR%%/%%SLUG%%.py
```

**驗收 ✅** TODO 可觀察的成功條件。

➡️ 完整課程（程式碼 + 講解）：[lessons/%%DIR%%](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/%%DIR%%)
"""


def render(template: str, mapping: dict) -> str:
    out = template
    for key, val in mapping.items():
        out = out.replace(key, val)
    return out


def write_new(path: str, content: str) -> None:
    if os.path.exists(path):
        raise SystemExit(f"refusing to overwrite existing file: {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  created {os.path.relpath(path, ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("nn", help="two-digit lesson number, e.g. 06")
    ap.add_argument("slug", help="snake_case slug, e.g. follow_me")
    ap.add_argument("title", help='human title, e.g. "Follow-me tracking"')
    args = ap.parse_args()

    nn, slug, title = args.nn, args.slug, args.title
    if not re.fullmatch(r"\d{2}", nn):
        raise SystemExit("nn must be two digits, e.g. 06")
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise SystemExit("slug must be lowercase letters/digits/underscores")

    lesson_dir = f"{nn}_{slug}"
    docs_slug = slug.replace("_", "-")
    docs_name = f"{nn}-{docs_slug}.md"
    heading = f"Lesson {nn} — {title}"
    anchor = f"{slug.replace('_', '-')}"  # for the in-page zh->en language link

    mapping = {
        "%%NN%%": nn,
        "%%SLUG%%": slug,
        "%%TITLE%%": title,
        "%%DIR%%": lesson_dir,
        "%%HEADING%%": heading,
        "%%UNDERLINE%%": "=" * len(heading),
        "%%ANCHOR%%": anchor,
    }

    print(f"Scaffolding Lesson {nn}: {title}")
    write_new(
        os.path.join(ROOT, "lessons", lesson_dir, f"{slug}.py"),
        render(SCRIPT_TEMPLATE, mapping),
    )
    write_new(
        os.path.join(ROOT, "lessons", lesson_dir, "README.md"),
        render(README_TEMPLATE, mapping),
    )
    write_new(
        os.path.join(ROOT, "docs", "en", docs_name), render(DOC_EN_TEMPLATE, mapping)
    )
    write_new(
        os.path.join(ROOT, "docs", "zh-TW", docs_name), render(DOC_ZH_TEMPLATE, mapping)
    )

    print(
        "\nNow paste these 3 snippets by hand (see CONTRIBUTING > Adding a lesson):\n"
    )
    print(f'1) mkdocs.yml -> under `nav:`\n     - "{heading}": {docs_name}\n')
    print(
        "2) README.md AND README.zh-TW.md -> add a learning-path row, e.g.\n"
        f"     | **{nn}** | {title} | $0 | TODO |\n"
    )
    print(
        "3) .github/workflows/ci.yml -> in the `smoke` job (if headless-runnable):\n"
        f"      - name: Lesson {nn} — {slug} (headless)\n"
        f"        run: python lessons/{lesson_dir}/{slug}.py --headless\n"
    )
    print(
        f"4) tools/render_media.py -> add a render function that saves\n"
        f"     assets/lesson{nn}.gif (the README already embeds it).\n"
    )
    print("Then: fill the TODOs, `ruff check . && black . && mkdocs build --strict`.")


if __name__ == "__main__":
    main()
    sys.exit(0)
