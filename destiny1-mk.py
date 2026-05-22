#!/usr/bin/env python3
"""
destiny1-mk — Mouse & Keyboard to DualShock 4 bridge
Works alongside chiaki-ng to let you play Destiny 1 on PC with full M&K.
"""

import json
import math
import sys
import threading
import time
import ctypes
from collections import defaultdict
from pathlib import Path

# ── Dependency check ─────────────────────────────────────────────────────────

missing = []
try:
    import vgamepad as vg
except ImportError:
    missing.append("vgamepad")
try:
    from pynput import mouse as pm, keyboard as pk
except ImportError:
    missing.append("pynput")

if missing:
    print(f"[ERROR] Missing packages. Run:  pip install {' '.join(missing)}")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "sensitivity": {
        "x": 25.0,
        "y": 22.0,
        "acceleration": 1.0,
        "ads_multiplier": 0.4
    },
    "bindings": {
        "w":           "ls_up",
        "a":           "ls_left",
        "s":           "ls_down",
        "d":           "ls_right",
        "space":       "cross",
        "c":           "circle",
        "shift":       "l3",
        "r":           "square",
        "t":           "triangle",
        "q":           "r1",
        "e":           "r3",
        "g":           "l1",
        "f":           "r2",
        "left_click":  "r2",
        "right_click": "l2",
        "tab":         "touchpad",
        "esc":         "options",
        "1":           "dpad_up",
        "2":           "dpad_down",
        "3":           "dpad_left",
        "4":           "dpad_right"
    },
    "capture_toggle": "f3",
    "update_hz": 250
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            user = json.load(f)
        cfg = {
            "sensitivity": {**DEFAULT_CONFIG["sensitivity"], **user.get("sensitivity", {})},
            "bindings":    {**DEFAULT_CONFIG["bindings"],    **user.get("bindings", {})},
            "capture_toggle": user.get("capture_toggle", DEFAULT_CONFIG["capture_toggle"]),
            "update_hz":      user.get("update_hz",      DEFAULT_CONFIG["update_hz"]),
        }
        return cfg
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    print("[INFO] Created config.json with default bindings.")
    return DEFAULT_CONFIG.copy()


# ── DS4 action tables ─────────────────────────────────────────────────────────

BTN     = vg.DS4_BUTTONS
SPECIAL = vg.DS4_SPECIAL_BUTTONS
DPAD    = vg.DS4_DPAD_DIRECTIONS

ACTION_BTN = {
    "cross":    BTN.DS4_BUTTON_CROSS,
    "circle":   BTN.DS4_BUTTON_CIRCLE,
    "square":   BTN.DS4_BUTTON_SQUARE,
    "triangle": BTN.DS4_BUTTON_TRIANGLE,
    "l1":       BTN.DS4_BUTTON_SHOULDER_LEFT,
    "r1":       BTN.DS4_BUTTON_SHOULDER_RIGHT,
    "l3":       BTN.DS4_BUTTON_THUMB_LEFT,
    "r3":       BTN.DS4_BUTTON_THUMB_RIGHT,
    "options":  BTN.DS4_BUTTON_OPTIONS,
    "share":    BTN.DS4_BUTTON_SHARE,
}

DPAD_TABLE = {
    (True,  False, False, False): DPAD.DS4_BUTTON_DPAD_NORTH,
    (False, True,  False, False): DPAD.DS4_BUTTON_DPAD_SOUTH,
    (False, False, True,  False): DPAD.DS4_BUTTON_DPAD_WEST,
    (False, False, False, True):  DPAD.DS4_BUTTON_DPAD_EAST,
    (True,  False, False, True):  DPAD.DS4_BUTTON_DPAD_NORTHEAST,
    (True,  False, True,  False): DPAD.DS4_BUTTON_DPAD_NORTHWEST,
    (False, True,  False, True):  DPAD.DS4_BUTTON_DPAD_SOUTHEAST,
    (False, True,  True,  False): DPAD.DS4_BUTTON_DPAD_SOUTHWEST,
}

# ── Bridge ────────────────────────────────────────────────────────────────────

class InputBridge:
    def __init__(self, cfg: dict):
        self.cfg      = cfg
        self.bindings = cfg["bindings"]
        self.capture_toggle = cfg["capture_toggle"]

        sx = cfg["sensitivity"]
        self.sens_x   = sx["x"]
        self.sens_y   = sx["y"]
        self.accel    = sx["acceleration"]
        self.ads_mult = sx["ads_multiplier"]
        self.dt       = 1.0 / cfg["update_hz"]

        self.pad      = vg.VDS4Gamepad()
        self.captured = False
        self.running  = False

        self._lock         = threading.Lock()
        self._mouse_dx     = 0.0
        self._mouse_dy     = 0.0
        self._resetting    = False
        self._action_count: dict[str, int] = defaultdict(int)

        u32        = ctypes.windll.user32
        self._cx   = u32.GetSystemMetrics(0) // 2
        self._cy   = u32.GetSystemMetrics(1) // 2

    # ── Input normalisation ───────────────────────────────────────────────

    @staticmethod
    def _norm_key(key) -> str:
        try:
            if key.char:
                return key.char.lower()
        except AttributeError:
            pass
        try:
            n = key.name.lower()
            for suffix in ("_l", "_r"):
                if n.endswith(suffix):
                    return n[:-2]
            return n
        except AttributeError:
            return ""

    @staticmethod
    def _norm_mouse_btn(btn) -> str:
        if btn == pm.Button.left:   return "left_click"
        if btn == pm.Button.right:  return "right_click"
        if btn == pm.Button.middle: return "middle_click"
        return ""

    # ── pynput callbacks ──────────────────────────────────────────────────

    def _on_key_press(self, key):
        name = self._norm_key(key)
        if name == self.capture_toggle:
            self._toggle_capture()
            return
        self._input_down(name)

    def _on_key_release(self, key):
        self._input_up(self._norm_key(key))

    def _on_mouse_move(self, x, y):
        if self._resetting:
            self._resetting = False
            return
        if not self.captured:
            return
        dx, dy = x - self._cx, y - self._cy
        if dx or dy:
            with self._lock:
                self._mouse_dx += dx
                self._mouse_dy += dy
            self._resetting = True
            ctypes.windll.user32.SetCursorPos(self._cx, self._cy)

    def _on_mouse_click(self, x, y, btn, pressed):
        name = self._norm_mouse_btn(btn)
        if pressed:
            self._input_down(name)
        else:
            self._input_up(name)

    # ── Action dispatch ───────────────────────────────────────────────────

    def _input_down(self, key_name: str):
        action = self.bindings.get(key_name)
        if not action:
            return
        with self._lock:
            self._action_count[action] += 1
            first = self._action_count[action] == 1
        if first:
            self._press(action)

    def _input_up(self, key_name: str):
        action = self.bindings.get(key_name)
        if not action:
            return
        with self._lock:
            self._action_count[action] = max(0, self._action_count[action] - 1)
            last = self._action_count[action] == 0
        if last:
            self._release(action)

    def _press(self, action: str):
        try:
            if action in ACTION_BTN:
                self.pad.press_button(ACTION_BTN[action])
            elif action == "touchpad":
                self.pad.press_special_button(SPECIAL.DS4_SPECIAL_BUTTON_TOUCHPAD)
            elif action == "l2":
                self.pad.left_trigger(value=255)
            elif action == "r2":
                self.pad.right_trigger(value=255)
            elif action.startswith("dpad_"):
                self._send_dpad()
                return
            self.pad.update()
        except Exception:
            pass

    def _release(self, action: str):
        try:
            if action in ACTION_BTN:
                self.pad.release_button(ACTION_BTN[action])
            elif action == "touchpad":
                self.pad.release_special_button(SPECIAL.DS4_SPECIAL_BUTTON_TOUCHPAD)
            elif action == "l2":
                self.pad.left_trigger(value=0)
            elif action == "r2":
                self.pad.right_trigger(value=0)
            elif action.startswith("dpad_"):
                self._send_dpad()
                return
            self.pad.update()
        except Exception:
            pass

    def _send_dpad(self):
        with self._lock:
            ac = self._action_count
            key = (ac["dpad_up"] > 0, ac["dpad_down"] > 0,
                   ac["dpad_left"] > 0, ac["dpad_right"] > 0)
        direction = DPAD_TABLE.get(key, DPAD.DS4_BUTTON_DPAD_NONE)
        try:
            self.pad.directional_pad(direction=direction)
            self.pad.update()
        except Exception:
            pass

    # ── Analog update loop ────────────────────────────────────────────────

    def _update(self):
        with self._lock:
            dx, dy = self._mouse_dx, self._mouse_dy
            self._mouse_dx = self._mouse_dy = 0.0
            ac = dict(self._action_count)

        # Left stick (WASD)
        lx = float(ac.get("ls_right", 0) > 0) - float(ac.get("ls_left", 0) > 0)
        ly = float(ac.get("ls_down",  0) > 0) - float(ac.get("ls_up",   0) > 0)
        mag = math.sqrt(lx * lx + ly * ly)
        if mag > 1.0:
            lx /= mag
            ly /= mag

        # Right stick (mouse)
        if self.captured:
            ads   = ac.get("l2", 0) > 0
            mult  = self.ads_mult if ads else 1.0
            rx    = self._curve(dx, self.sens_x * mult)
            ry    = self._curve(dy, self.sens_y * mult)
        else:
            rx = ry = 0.0

        try:
            self.pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
            self.pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
            self.pad.update()
        except Exception:
            pass

    def _curve(self, delta: float, sensitivity: float) -> float:
        """Pixel delta → [-1, 1]. acceleration > 1 = faster for large movements."""
        val  = delta / max(sensitivity, 0.001)
        sign = 1.0 if val >= 0.0 else -1.0
        return max(-1.0, min(1.0, sign * (abs(val) ** (1.0 / max(self.accel, 0.1)))))

    # ── Capture toggle ────────────────────────────────────────────────────

    def _toggle_capture(self):
        self.captured = not self.captured
        ctypes.windll.user32.ShowCursor(not self.captured)
        if self.captured:
            ctypes.windll.user32.SetCursorPos(self._cx, self._cy)
            print(f"[+] Mouse captured   — {self.capture_toggle.upper()} to release")
        else:
            print(f"[-] Mouse released   — {self.capture_toggle.upper()} to capture")

    # ── Entry point ───────────────────────────────────────────────────────

    def start(self):
        self.running = True
        print("=" * 50)
        print("  destiny1-mk  |  M&K → DS4 bridge")
        print("=" * 50)
        print(f"  Capture toggle : {self.capture_toggle.upper()}")
        print(f"  Sensitivity    : x={self.sens_x}  y={self.sens_y}")
        print(f"  Update rate    : {self.cfg['update_hz']} Hz")
        print("  Edit config.json to change bindings/sensitivity")
        print("=" * 50)
        print()
        print("Waiting — press F3 to capture mouse and start playing.")
        print("Ctrl+C to quit.\n")

        kb = pk.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        ms = pm.Listener(on_move=self._on_mouse_move, on_click=self._on_mouse_click)
        kb.start()
        ms.start()

        try:
            while self.running:
                t0    = time.monotonic()
                self._update()
                sleep = self.dt - (time.monotonic() - t0)
                if sleep > 0:
                    time.sleep(sleep)
        finally:
            self.running = False
            ctypes.windll.user32.ShowCursor(True)
            kb.stop()
            ms.stop()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    cfg = load_config()
    InputBridge(cfg).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Exited.")
