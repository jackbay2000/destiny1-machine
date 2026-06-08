#!/usr/bin/env python3
"""
Standalone tests for FrameGenProcessor (no capture card, vgamepad, or pynput needed).
Run with:  python test_frame_gen.py
"""

import queue
import sys
import threading
import time
import types

# ── Stub out hardware deps so we can import the module headlessly ─────────────

# vgamepad stub
vg_mod = types.ModuleType("vgamepad")
class _FakeDS4Buttons: DS4_BUTTON_CROSS=0; DS4_BUTTON_CIRCLE=1; DS4_BUTTON_SQUARE=2; DS4_BUTTON_TRIANGLE=3; DS4_BUTTON_SHOULDER_LEFT=4; DS4_BUTTON_SHOULDER_RIGHT=5; DS4_BUTTON_THUMB_LEFT=6; DS4_BUTTON_THUMB_RIGHT=7; DS4_BUTTON_OPTIONS=8; DS4_BUTTON_SHARE=9
class _FakeDpad: DS4_BUTTON_DPAD_NONE=0; DS4_BUTTON_DPAD_NORTH=1; DS4_BUTTON_DPAD_NORTHEAST=2; DS4_BUTTON_DPAD_EAST=3; DS4_BUTTON_DPAD_SOUTHEAST=4; DS4_BUTTON_DPAD_SOUTH=5; DS4_BUTTON_DPAD_SOUTHWEST=6; DS4_BUTTON_DPAD_WEST=7; DS4_BUTTON_DPAD_NORTHWEST=8
class _FakeSpecial: DS4_SPECIAL_BUTTON_TOUCHPAD=0
class _FakeGamepad:
    def press_button(self, *a): pass
    def release_button(self, *a): pass
    def press_special_button(self, *a): pass
    def release_special_button(self, *a): pass
    def left_trigger(self, **kw): pass
    def right_trigger(self, **kw): pass
    def left_joystick_float(self, **kw): pass
    def right_joystick_float(self, **kw): pass
    def directional_pad(self, **kw): pass
    def update(self): pass
vg_mod.DS4_BUTTONS = _FakeDS4Buttons()
vg_mod.DS4_DPAD_DIRECTIONS = _FakeDpad()
vg_mod.DS4_SPECIAL_BUTTONS = _FakeSpecial()
vg_mod.VDS4Gamepad = _FakeGamepad
sys.modules["vgamepad"] = vg_mod

# pynput stub
pynput_mod = types.ModuleType("pynput")
kb_mod = types.ModuleType("pynput.keyboard")
class _FakeListener:
    def __init__(self, **kw): pass
    def start(self): pass
    def stop(self): pass
kb_mod.Listener = _FakeListener
pynput_mod.keyboard = kb_mod
sys.modules["pynput"] = pynput_mod
sys.modules["pynput.keyboard"] = kb_mod

import importlib.util, pathlib
_src = pathlib.Path(__file__).parent / "destiny1-mk-capture.py"
_spec = importlib.util.spec_from_file_location("mk", _src)
mk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mk)

try:
    import cv2
    import numpy as np
except ImportError:
    print("SKIP  cv2/numpy not installed — frame gen tests cannot run.")
    print("      Install with:  pip install opencv-python numpy")
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_failures = 0

def check(name: str, condition: bool, detail: str = ""):
    global _failures
    status = PASS if condition else FAIL
    print(f"  [{status}]  {name}" + (f"  ({detail})" if detail else ""))
    if not condition:
        _failures += 1


# ── Test 1 — _interpolate output shape and dtype ─────────────────────────────

def test_interpolate_shape():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 240, 320
    prev = np.zeros((h, w, 3), dtype=np.uint8)
    curr = np.full((h, w, 3), 128, dtype=np.uint8)
    out  = fg._interpolate(prev, curr)
    check("output shape matches input",    out.shape == (h, w, 3), f"got {out.shape}")
    check("output dtype is uint8",         out.dtype  == np.uint8,  f"got {out.dtype}")


# ── Test 2 — _interpolate pixel values are between prev and curr ─────────────

def test_interpolate_midpoint():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 240, 320
    prev = np.full((h, w, 3),   0, dtype=np.uint8)
    curr = np.full((h, w, 3), 200, dtype=np.uint8)
    out  = fg._interpolate(prev, curr)
    mn, mx = int(out.min()), int(out.max())
    check("interpolated pixels >= prev (0)",   mn >= 0,   f"min={mn}")
    check("interpolated pixels <= curr (200)", mx <= 200, f"max={mx}")
    check("interpolated pixels not all zero", mx > 0,    f"max={mx}")


# ── Test 3 — _interpolate handles non-square / odd-dimension frames ───────────

def test_interpolate_odd_dims():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 181, 311  # odd dimensions
    rng  = np.random.default_rng(42)
    prev = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
    curr = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
    try:
        out = fg._interpolate(prev, curr)
        check("odd-dim frame has correct shape", out.shape == (h, w, 3), f"got {out.shape}")
    except Exception as exc:
        check("odd-dim frame does not raise", False, str(exc))


# ── Test 4 — identical frames produce identical output ───────────────────────

def test_interpolate_identity():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 120, 160
    frame = np.full((h, w, 3), 77, dtype=np.uint8)
    out   = fg._interpolate(frame, frame.copy())
    diff  = int(np.abs(out.astype(np.int16) - frame.astype(np.int16)).max())
    check("identical frames -> no change (max diff <= 1)", diff <= 1, f"max diff={diff}")


# ── Test 5 — queue: full raw_q drops oldest, not newest ──────────────────────

def test_raw_queue_drop():
    fg = mk.FrameGenProcessor(device=0)
    sentinel = object()
    fg._raw_q.put_nowait(sentinel)   # fill it (maxsize=2)
    fg._raw_q.put_nowait(sentinel)
    # Simulate what _capture_loop does when full:
    dropped = False
    if fg._raw_q.full():
        try:
            fg._raw_q.get_nowait()
            dropped = True
        except queue.Empty:
            pass
    new_item = object()
    fg._raw_q.put_nowait(new_item)
    last = None
    while not fg._raw_q.empty():
        last = fg._raw_q.get_nowait()
    check("newest frame kept in full queue", last is new_item)
    check("oldest frame was dropped",        dropped)


# ── Test 6 — start/stop lifecycle (threads exit cleanly) ─────────────────────

def test_lifecycle():
    fg = mk.FrameGenProcessor(device=99)  # non-existent device → capture fails gracefully
    fg.start()
    time.sleep(0.15)
    fg.stop()
    time.sleep(0.1)
    check("_running is False after stop", not fg._running)


# ── Test 7 — interp_loop produces output from synthetic frames ────────────────

def test_interp_pipeline():
    fg = mk.FrameGenProcessor(device=0)
    fg._running = True
    threading.Thread(target=fg._interp_loop, daemon=True).start()

    h, w = 120, 160
    prev = np.zeros((h, w, 3), dtype=np.uint8)
    curr = np.full((h, w, 3), 100, dtype=np.uint8)
    fg._raw_q.put(prev)
    fg._raw_q.put(curr)

    try:
        interp, real = fg._disp_q.get(timeout=2.0)
        check("interp frame correct shape", interp.shape == (h, w, 3), f"got {interp.shape}")
        check("real frame correct shape",   real.shape   == (h, w, 3), f"got {real.shape}")
    except queue.Empty:
        check("disp_q received output within 2 s", False, "timed out")
    finally:
        fg._running = False


# ── Test 8 — _is_duplicate: identical frames are duplicates ──────────────────

def test_is_duplicate_identical():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 240, 320
    frame = np.full((h, w, 3), 128, dtype=np.uint8)
    check("identical frames flagged as duplicate", fg._is_duplicate(frame, frame.copy()))


# ── Test 9 — _is_duplicate: different frames are not duplicates ───────────────

def test_is_duplicate_different():
    fg = mk.FrameGenProcessor(device=0)
    h, w = 240, 320
    a = np.zeros((h, w, 3), dtype=np.uint8)
    b = np.full((h, w, 3), 50, dtype=np.uint8)
    check("different frames not flagged as duplicate", not fg._is_duplicate(a, b))


# ── Test 10 — _is_duplicate: minor compression noise is still a duplicate ─────

def test_is_duplicate_noise():
    fg = mk.FrameGenProcessor(device=0)
    rng = np.random.default_rng(7)
    h, w = 240, 320
    base  = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
    # Add ±1 noise to simulate capture card compression on a duplicate frame
    noise = rng.integers(-1, 2, (h, w, 3), dtype=np.int16)
    noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    check("compressed duplicate still flagged", fg._is_duplicate(base, noisy))


# ── Test 11 — interp_loop skips duplicate frames ──────────────────────────────

def test_interp_loop_skips_duplicates():
    fg = mk.FrameGenProcessor(device=0)
    fg._running = True
    threading.Thread(target=fg._interp_loop, daemon=True).start()

    h, w = 120, 160
    real_a = np.zeros((h, w, 3), dtype=np.uint8)
    dup_a  = real_a.copy()                            # capture card duplicate
    real_b = np.full((h, w, 3), 80, dtype=np.uint8)  # next genuine frame

    fg._raw_q.put(real_a)
    fg._raw_q.put(dup_a)   # should be skipped
    fg._raw_q.put(real_b)

    try:
        interp, real = fg._disp_q.get(timeout=2.0)
        # The interpolated frame should blend real_a and real_b, not real_a and dup_a
        mid_expected = 40  # halfway between 0 and 80
        actual_mid   = int(np.mean(interp))
        check("duplicate skipped — interp is between real_a and real_b",
              30 <= actual_mid <= 50, f"mean={actual_mid}, expected ~{mid_expected}")
    except queue.Empty:
        check("disp_q received output after duplicate skipped", False, "timed out")
    finally:
        fg._running = False


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\ndestiny1-mk  |  Frame Gen Tests\n" + "-" * 40)
    test_interpolate_shape()
    test_interpolate_midpoint()
    test_interpolate_odd_dims()
    test_interpolate_identity()
    test_raw_queue_drop()
    test_lifecycle()
    test_interp_pipeline()
    test_is_duplicate_identical()
    test_is_duplicate_different()
    test_is_duplicate_noise()
    test_interp_loop_skips_duplicates()
    print("-" * 40)
    if _failures == 0:
        print(f"All tests passed. Frame gen looks good.\n")
    else:
        print(f"{_failures} test(s) FAILED.\n")
        sys.exit(1)
