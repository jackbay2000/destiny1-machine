#!/usr/bin/env python3
"""
destiny1-mk — Mouse & Keyboard to Xbox 360 virtual controller bridge
Works with PS4 Remote Play to let you play Destiny 1 on PC with full M&K.
PS4 Remote Play maps Xbox buttons to PS4 buttons automatically.
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

_SENS_BASE_X = 25.0  # pixels per full deflection at sensitivity 1.0
_SENS_BASE_Y = 22.0

DEFAULT_CONFIG = {
    "sensitivity": {
        "x": 1.0,
        "y": 1.0,
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


# ── DS4 action table ──────────────────────────────────────────────────────────

BTN      = vg.DS4_BUTTONS
DPAD     = vg.DS4_DPAD_DIRECTIONS
SPEC_BTN = vg.DS4_SPECIAL_BUTTONS

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

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

# ── Bridge ────────────────────────────────────────────────────────────────────

class InputBridge:
    def __init__(self, cfg: dict):
        self.cfg      = cfg
        self.bindings = cfg["bindings"]
        self.capture_toggle = cfg["capture_toggle"]

        sx = cfg["sensitivity"]
        self.sens_x   = _SENS_BASE_X / max(sx["x"], 0.001)
        self.sens_y   = _SENS_BASE_Y / max(sx["y"], 0.001)
        self.accel    = sx["acceleration"]
        self.ads_mult = sx["ads_multiplier"]
        self.dt       = 1.0 / cfg["update_hz"]

        self.pad      = vg.VDS4Gamepad()
        self.captured = False
        self.running  = False
        self._chiaki_focused = False

        self._lock         = threading.Lock()
        self._action_count: dict[str, int] = defaultdict(int)
        self._held_keys:    set[str]        = set()

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
        if btn == pm.Button.x1:    return "mouse4"
        if btn == pm.Button.x2:    return "mouse5"
        return ""

    # ── pynput callbacks ──────────────────────────────────────────────────

    def _on_key_press(self, key):
        name = self._norm_key(key)
        with self._lock:
            if name in self._held_keys:
                return  # suppress Windows key-repeat
            self._held_keys.add(name)
        if name == self.capture_toggle:
            self._toggle_capture()
            return
        if not self._chiaki_focused:
            return
        self._input_down(name)

    def _on_key_release(self, key):
        name = self._norm_key(key)
        with self._lock:
            self._held_keys.discard(name)
        self._input_up(name)

    def _on_mouse_click(self, x, y, btn, pressed):
        if not self._chiaki_focused:
            return
        name = self._norm_mouse_btn(btn)
        if pressed:
            self._input_down(name)
        else:
            self._input_up(name)

    # ── Action dispatch ───────────────────────────────────────────────────

    def _input_down(self, key_name: str):
        binding = self.bindings.get(key_name)
        if not binding:
            return
        actions = binding if isinstance(binding, list) else [binding]
        for action in actions:
            with self._lock:
                self._action_count[action] += 1
                first = self._action_count[action] == 1
            if first:
                self._press(action)

    def _input_up(self, key_name: str):
        binding = self.bindings.get(key_name)
        if not binding:
            return
        actions = binding if isinstance(binding, list) else [binding]
        for action in actions:
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
                self.pad.press_special_button(SPEC_BTN.DS4_SPECIAL_BUTTON_TOUCHPAD)
            elif action == "l2":
                self.pad.left_trigger(value=255)
            elif action == "r2":
                self.pad.right_trigger(value=255)
            else:
                return
            self.pad.update()
        except Exception:
            pass

    def _release(self, action: str):
        try:
            if action in ACTION_BTN:
                self.pad.release_button(ACTION_BTN[action])
            elif action == "touchpad":
                self.pad.release_special_button(SPEC_BTN.DS4_SPECIAL_BUTTON_TOUCHPAD)
            elif action == "l2":
                self.pad.left_trigger(value=0)
            elif action == "r2":
                self.pad.right_trigger(value=0)
            else:
                return
            self.pad.update()
        except Exception:
            pass

    # ── Analog update loop ────────────────────────────────────────────────

    def _update(self):
        focused = self._is_chiaki_focused()
        if not focused and self._chiaki_focused:
            self._on_focus_lost()
        self._chiaki_focused = focused

        with self._lock:
            ac = dict(self._action_count)

        # Left stick (WASD)
        lx = float(ac.get("ls_right", 0) > 0) - float(ac.get("ls_left",  0) > 0)
        ly = float(ac.get("ls_up",    0) > 0) - float(ac.get("ls_down",  0) > 0)
        mag = math.sqrt(lx * lx + ly * ly)
        if mag > 1.0:
            lx /= mag
            ly /= mag

        # Right stick — poll cursor position, reset to center each tick
        if self.captured:
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            dx = float(pt.x - self._cx)
            dy = float(pt.y - self._cy)
            ctypes.windll.user32.SetCursorPos(self._cx, self._cy)
            ads  = ac.get("l2", 0) > 0
            mult = self.ads_mult if ads else 1.0
            rx   = self._curve(dx, self.sens_x * mult)
            ry   = self._curve(dy, self.sens_y * mult)
        else:
            rx = ry = 0.0

        # D-pad
        up    = ac.get("dpad_up",    0) > 0
        down  = ac.get("dpad_down",  0) > 0
        left  = ac.get("dpad_left",  0) > 0
        right = ac.get("dpad_right", 0) > 0
        if   up and right: dpad = DPAD.DS4_BUTTON_DPAD_NORTHEAST
        elif down and right: dpad = DPAD.DS4_BUTTON_DPAD_SOUTHEAST
        elif down and left:  dpad = DPAD.DS4_BUTTON_DPAD_SOUTHWEST
        elif up and left:    dpad = DPAD.DS4_BUTTON_DPAD_NORTHWEST
        elif up:             dpad = DPAD.DS4_BUTTON_DPAD_NORTH
        elif right:          dpad = DPAD.DS4_BUTTON_DPAD_EAST
        elif down:           dpad = DPAD.DS4_BUTTON_DPAD_SOUTH
        elif left:           dpad = DPAD.DS4_BUTTON_DPAD_WEST
        else:                dpad = DPAD.DS4_BUTTON_DPAD_NONE

        try:
            self.pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
            self.pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
            self.pad.directional_pad(direction=dpad)
            self.pad.update()
        except Exception:
            pass

    def _curve(self, delta: float, sensitivity: float) -> float:
        """Pixel delta → [-1, 1]. acceleration > 1 = faster for large movements."""
        val  = delta / max(sensitivity, 0.001)
        sign = 1.0 if val >= 0.0 else -1.0
        return max(-1.0, min(1.0, sign * (abs(val) ** (1.0 / max(self.accel, 0.1)))))

    # ── Focus awareness ───────────────────────────────────────────────────

    def _is_chiaki_focused(self) -> bool:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        return "chiaki" in buf.value.lower()

    def _release_all(self):
        with self._lock:
            held = {a for a, c in self._action_count.items() if c > 0}
            self._action_count.clear()
            self._held_keys.clear()
        for action in held:
            self._release(action)

    def _on_focus_lost(self):
        if self.captured:
            self.captured = False
            self._set_cursor_visible(True)
            print(f"[-] Mouse released (chiaki lost focus) — {self.capture_toggle.upper()} to capture")
        self._release_all()

    # ── Cursor visibility ─────────────────────────────────────────────────

    @staticmethod
    def _set_cursor_visible(visible: bool):
        u32 = ctypes.windll.user32
        if visible:
            while u32.ShowCursor(True) < 0:
                pass
        else:
            while u32.ShowCursor(False) >= 0:
                pass

    # ── Capture toggle ────────────────────────────────────────────────────

    def _toggle_capture(self):
        self.captured = not self.captured
        self._set_cursor_visible(not self.captured)
        if self.captured:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            rect = RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            self._cx = (rect.left + rect.right) // 2
            self._cy = (rect.top + rect.bottom) // 2
            ctypes.windll.user32.SetCursorPos(self._cx, self._cy)
            print(f"[+] Mouse captured   — {self.capture_toggle.upper()} to release")
        else:
            print(f"[-] Mouse released   — {self.capture_toggle.upper()} to capture")

    # ── Entry point ───────────────────────────────────────────────────────

    def start(self):
        self.running = True
        print("=" * 50)
        print("  destiny1-mk  |  M&K → Xbox virtual controller")
        print("=" * 50)
        print(f"  Capture toggle : {self.capture_toggle.upper()}")
        sx = self.cfg["sensitivity"]
        print(f"  Sensitivity    : x={sx['x']}  y={sx['y']}")
        print(f"  Update rate    : {self.cfg['update_hz']} Hz")
        print("  Edit config.json to change bindings/sensitivity")
        print("=" * 50)
        print()
        print("Waiting — press F3 to capture mouse and start playing.")
        print("Ctrl+C to quit.\n")

        kb = pk.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        ms = pm.Listener(on_click=self._on_mouse_click)
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
            self._set_cursor_visible(True)
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
