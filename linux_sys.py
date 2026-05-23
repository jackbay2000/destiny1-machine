"""
Linux system backend for destiny1-mk-linux.py.
Provides cursor control, window focus detection, and screen metrics
using pynput and python-xlib. Never imported by the Windows version.
"""

import threading
from pynput.mouse import Controller as MouseController

_mouse = MouseController()

# ── Screen metrics ────────────────────────────────────────────────────────────

def get_screen_center() -> tuple[int, int]:
    """Return (cx, cy) centre of the primary screen."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        return w // 2, h // 2
    except Exception:
        return 960, 540


# ── Cursor position ───────────────────────────────────────────────────────────

def get_cursor_pos() -> tuple[int, int]:
    x, y = _mouse.position
    return int(x), int(y)


def set_cursor_pos(x: int, y: int) -> None:
    _mouse.position = (x, y)


# ── X11 backend (cursor hide/show + window info) ──────────────────────────────

class _XBackend:
    def __init__(self):
        self._ok   = False
        self._lock = threading.Lock()
        try:
            from Xlib import display, X
            self._X      = X
            self._disp   = display.Display()
            self._screen = self._disp.screen()
            self._root   = self._screen.root
            self._atom_active = self._disp.intern_atom('_NET_ACTIVE_WINDOW')
            self._atom_name   = self._disp.intern_atom('_NET_WM_NAME')
            self._blank       = self._make_blank_cursor()
            self._arrow       = self._make_arrow_cursor()
            self._ok          = True
        except Exception:
            pass

    def _make_blank_cursor(self):
        pm = self._root.create_pixmap(1, 1, 1)
        # X11 pixmaps have undefined contents on allocation; fill before use as mask
        gc = pm.create_gc(foreground=0, background=0)
        pm.fill_rectangle(gc, 0, 0, 1, 1)
        gc.free()
        cursor = pm.create_cursor(pm, 0, 0, 0, 0, 0, 0, 0, 0)
        pm.free()
        return cursor

    def _make_arrow_cursor(self):
        try:
            import Xlib.Xcursorfont
            return self._disp.create_font_cursor(Xlib.Xcursorfont.left_ptr)
        except Exception:
            return self._X.NONE

    def _active_window(self):
        prop = self._root.get_full_property(
            self._atom_active, self._X.AnyPropertyType
        )
        if prop and prop.value:
            return self._disp.create_resource_object('window', prop.value[0])
        return None

    def get_focused_title(self) -> str:
        if not self._ok:
            return ""
        try:
            with self._lock:
                win = self._active_window()
                if not win:
                    return ""
                # Prefer _NET_WM_NAME (UTF-8), fall back to WM_NAME
                prop = win.get_full_property(self._atom_name, 0)
                if prop and prop.value:
                    v = prop.value
                    return v.decode('utf-8', errors='replace') if isinstance(v, (bytes, bytearray)) else str(v)
                name = win.get_wm_name()
                return name or ""
        except Exception:
            return ""

    def get_focused_center(self) -> tuple[int, int] | None:
        if not self._ok:
            return None
        try:
            with self._lock:
                win = self._active_window()
                if not win:
                    return None
                win_geom = win.get_geometry()
                # Walk up the window tree accumulating position offsets until we
                # reach a direct child of root. Avoids the ambiguous
                # translate_coords src/dst convention across python-xlib versions.
                abs_x, abs_y, cur = 0, 0, win
                while True:
                    g = cur.get_geometry()
                    abs_x += g.x
                    abs_y += g.y
                    parent = cur.query_tree().parent
                    if not parent or parent.id == self._root.id:
                        break
                    cur = parent
                return abs_x + win_geom.width // 2, abs_y + win_geom.height // 2
        except Exception:
            return None

    def show_cursor(self, visible: bool) -> None:
        if not self._ok:
            return
        try:
            with self._lock:
                cursor = self._arrow if visible else self._blank
                self._root.change_attributes(cursor=cursor)
                self._disp.flush()
        except Exception:
            pass


_xback = _XBackend()


# ── Public interface ──────────────────────────────────────────────────────────

def show_cursor(visible: bool) -> None:
    _xback.show_cursor(visible)


def get_focused_window_title() -> str:
    return _xback.get_focused_title()


def get_focused_window_center() -> tuple[int, int] | None:
    return _xback.get_focused_center()


def x11_available() -> bool:
    return _xback._ok
