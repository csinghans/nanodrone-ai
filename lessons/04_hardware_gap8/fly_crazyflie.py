"""
Lesson 4 (HARDWARE REQUIRED) — first flight on a real Crazyflie
===============================================================
Bring-up script for the real nano-drone: connect over the Crazyradio, check the
battery, take off, do a tiny safe move, and land -- with the failsafes you must
always have before flying hardware.

This is the "act" side of the loop on real hardware. The autonomous AI itself
runs ON the drone (the GAP8 AI-deck, flashed separately); this host-side script
is for bring-up, testing, and reading what the AI-deck reports.

!!! SAFETY (read before running) !!!
  * Fly in an open area, props clear of people. Keep an RC override ready.
  * First run with props OFF to confirm connection + telemetry.
  * Charged battery; check your local drone regulations.

Requires a real Crazyflie 2.x + Crazyradio and:  pip install cflib
It will NOT run without hardware (it cannot connect to a radio) -- that's
expected; develop the autonomy in simulation (Lessons 1-3) first.

Run:  python lessons/04_hardware_gap8/fly_crazyflie.py --uri radio://0/80/2M/E7E7E7E7E7
"""

import argparse
import sys
import time

try:
    import cflib.crtp
    from cflib.crazyflie.log import LogConfig
    from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
    from cflib.crazyflie.syncLogger import SyncLogger
    from cflib.positioning.motion_commander import MotionCommander
    from cflib.utils import uri_helper
except ImportError as exc:  # pragma: no cover
    print("cflib not installed:", exc)
    print("Install it (hardware only):  pip install cflib")
    sys.exit(1)

# Failsafe thresholds.
MIN_TAKEOFF_VOLTAGE = 3.7  # don't take off on a tired battery (per-cell volts)
TAKEOFF_HEIGHT_M = 0.4  # low and gentle for a first flight
GEOFENCE_M = 0.5  # never command a move bigger than this (a soft fence)


def read_battery(scf: SyncCrazyflie) -> float:
    """Read one battery-voltage sample via the logging framework."""
    cfg = LogConfig(name="bat", period_in_ms=100)
    cfg.add_variable("pm.vbat", "float")
    with SyncLogger(scf, cfg) as logger:
        for _, data, _ in logger:
            return float(data["pm.vbat"])
    return 0.0


def fly(uri: str) -> None:
    cflib.crtp.init_drivers()
    print(f"Connecting to {uri} ...")
    try:
        with SyncCrazyflie(uri) as scf:
            # --- Failsafe 1: battery gate ---------------------------------
            vbat = read_battery(scf)
            print(f"Battery: {vbat:.2f} V")
            if vbat < MIN_TAKEOFF_VOLTAGE:
                print("Battery too low -- refusing to take off. Charge it.")
                return

            # --- Take off, tiny move, land --------------------------------
            # MotionCommander takes off on enter and ALWAYS lands on exit,
            # including if an exception is raised -> a built-in failsafe.
            print("Taking off...")
            with MotionCommander(scf, default_height=TAKEOFF_HEIGHT_M) as mc:
                time.sleep(2.0)  # hover and stabilize
                # --- Failsafe 2: geofence the movement --------------------
                step = min(0.2, GEOFENCE_M)
                print(f"Nudging forward {step} m and back...")
                mc.forward(step)
                time.sleep(1.0)
                mc.back(step)
                time.sleep(1.0)
                print("Landing...")  # land happens on exiting the 'with'
            print("Done. Landed safely.")
    except Exception as exc:  # pragma: no cover - hardware/connection errors
        # --- Failsafe 3: any error -> we've already exited the commander,
        # so the drone has landed. Report and stop.
        print(f"Flight aborted ({type(exc).__name__}): {exc}")
        print("If this was a connection error, check the radio, URI, and that")
        print("the Crazyflie is on. Without hardware this script cannot run.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uri",
        default="radio://0/80/2M/E7E7E7E7E7",
        help="Crazyflie radio URI (find yours with the cfclient app)",
    )
    args = parser.parse_args()
    uri = uri_helper.uri_from_env(default=args.uri)
    fly(uri)


if __name__ == "__main__":
    main()
