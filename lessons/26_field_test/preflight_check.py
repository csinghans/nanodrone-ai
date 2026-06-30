"""
Lesson 26 — pre-flight gate: turn "can fly" into "flies legally and safely"
===========================================================================
The last mile of real flight isn't code — it's procedure and compliance. This
automates the *programmable* part of a pre-flight checklist into one GO / NO-GO
gate, reusing the safety layer (Lesson 24) and the log format (Lesson 23). The
human SOP and the Taiwan CAA checklist live in the README; this enforces what a
machine can.

Run:
  python lessons/26_field_test/preflight_check.py            # GO / NO-GO report
  python lessons/26_field_test/preflight_check.py --selftest  # asserts (CI)
"""

import os
import sys

from nanodrone import protocol, safety


def run_checks(battery_pct: float, takeoff_height: float, logs_dir: str):
    """Return a list of (name, ok, detail) for the automatable pre-flight gates."""
    checks = []

    checks.append(
        (
            "battery",
            safety.battery_gate(battery_pct),
            f"{battery_pct:.0f}% (need >= {safety.MIN_BATTERY_PCT:.0f}%)",
        )
    )

    writable = os.path.isdir(logs_dir) and os.access(logs_dir, os.W_OK)
    if not writable:
        try:
            os.makedirs(logs_dir, exist_ok=True)
            writable = os.access(logs_dir, os.W_OK)
        except OSError:
            writable = False
    checks.append(("log-writable", writable, logs_dir))

    fence_ok = protocol.BOX_XY > 0 and protocol.BOX_Z[0] < protocol.BOX_Z[1]
    checks.append(
        ("geofence", fence_ok, f"xy +/-{protocol.BOX_XY} m, z {protocol.BOX_Z} m")
    )

    h_ok = protocol.BOX_Z[0] <= takeoff_height <= protocol.BOX_Z[1]
    checks.append(("takeoff-height", h_ok, f"{takeoff_height:.2f} m within fence"))

    fs_ok = callable(getattr(safety, "decide_failsafe", None))
    checks.append(("failsafe-importable", fs_ok, "nanodrone.safety.decide_failsafe"))

    return checks


def report(battery_pct=85.0, takeoff_height=1.0, logs_dir=None):
    logs_dir = logs_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "logs"
    )
    checks = run_checks(battery_pct, takeoff_height, logs_dir)
    n_pass = sum(1 for _, ok, _ in checks if ok)
    go = all(ok for _, ok, _ in checks)
    names = "/".join(name for name, _, _ in checks)
    verdict = "GO" if go else "NO-GO"
    print(
        f"PREFLIGHT {'OK' if go else 'NO-GO'}: {n_pass}/{len(checks)} "
        f"automated checks pass ({names}), {verdict}"
    )
    for name, ok, detail in checks:
        if not ok:
            print(f"  [FAIL] {name}: {detail}")
    return go, checks


def main() -> None:
    if "--selftest" in sys.argv:
        go, checks = report(battery_pct=85.0)  # healthy -> GO
        assert go, "healthy pre-flight should be GO"
        assert len(checks) == 5, f"expected 5 checks, got {len(checks)}"
        # a low battery must produce NO-GO and name the battery check
        go2, checks2 = report(battery_pct=10.0)
        assert not go2, "low battery should be NO-GO"
        assert any(name == "battery" and not ok for name, ok, _ in checks2)
        print("SELFTEST OK: GO when healthy, NO-GO on low battery")
    else:
        report()


if __name__ == "__main__":
    main()
    sys.exit(0)
