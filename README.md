# destiny1-mk

Play Destiny 1 on PC with mouse and keyboard.

This tool creates a virtual DualShock 4 controller on your PC, translates your mouse and keyboard into DS4 input, and feeds it into **chiaki-ng** (an open-source PS4 Remote Play client). chiaki-ng streams video from your PS4 to your PC. Your PS4 stays connected to Bungie's live servers the whole time — nothing changes on the PS4 side.

For upscaling and frame generation (30fps → 60fps+), layer **Lossless Scaling** on top.

---

## How it works

```
Bungie Servers
      ↕
   Your PS4  ──── video stream ────▶  chiaki-ng window
      ↑                                      ↓
 fake DS4 input ◀──────────────  destiny1-mk.py
                                 (your mouse + keyboard)
                                             ↓
                                    Lossless Scaling
                                    (upscale + frame gen)
                                             ↓
                                    your monitor
```

---

## Requirements

- Windows 10 or 11
- Python 3.10+
- A PS4 with Destiny 1, connected to your local network
- Both PC and PS4 on **wired ethernet** (strongly recommended — WiFi adds latency)
- [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases/latest) — free, open source
- [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) — ~$7 on Steam (optional but recommended for frame gen)

---

## Installation

### Step 1 — Run setup

Double-click **setup.bat** (or run it in a terminal). This installs the Python dependencies including the virtual gamepad driver.

If you get a driver error when running the script later, manually install **ViGEmBus**:
- Download `ViGEmBus_Setup_x64.exe` from https://github.com/ViGEm/ViGEmBus/releases/latest
- Run it and restart your PC

### Step 2 — Install chiaki-ng

1. Download the latest Windows release from https://github.com/streetpea/chiaki-ng/releases/latest
2. Extract it anywhere on your PC
3. Run `chiaki-ng.exe` once to confirm it opens

### Step 3 — Enable Remote Play on your PS4

On your PS4:
- Settings → Remote Play Connection Settings → **Enable Remote Play** ✓
- Settings → Account Management → **Activate as Your Primary PS4** ✓
- Settings → Power Save Settings → Set Features Available in Rest Mode → check **Stay Connected to the Internet** and **Enable Turning On PS4 from Network**

### Step 4 — Register your PC with chiaki-ng

1. Open chiaki-ng
2. Your PS4 should appear automatically. If not, click **Add Console** and enter your PS4's IP address
3. Double-click your PS4 in the list — it will ask for a PIN
4. On your PS4: Settings → Remote Play → **Add Device** — note the 8-digit PIN
5. Enter the PIN in chiaki-ng
6. chiaki-ng will now remember your PS4. You only do this once.

### Step 5 — Disable chiaki-ng keyboard bindings (important)

destiny1-mk provides all controller input via a virtual DS4. If chiaki-ng also processes keyboard input, you'll get double input.

In chiaki-ng: **Settings → Controller → clear any keyboard bindings** (set them all to None/unbound).

---

## Running

**Every session:**

1. Turn on your PS4 and start Destiny 1
2. Open chiaki-ng and double-click your PS4 to start the stream
3. In a separate terminal window, run:
   ```
   python destiny1-mk.py
   ```
   Or double-click **run.bat**
4. Press **F3** to capture the mouse (cursor disappears, you're now in-game)
5. *(Optional)* Alt-Tab to Lossless Scaling and enable it on the chiaki-ng window

To release the mouse at any time (e.g. to alt-tab), press **F3** again.

---

## Default Key Bindings

| Key | Action |
|-----|--------|
| W A S D | Move (left stick) |
| Mouse | Aim (right stick) |
| Left Click | Shoot (R2) |
| Right Click | Aim Down Sights (L2) |
| Space | Jump (Cross) |
| Shift | Sprint (L3 click) |
| C | Crouch (Circle) |
| R | Reload (Square) |
| T | Swap Weapon (Triangle) |
| Q | Grenade (R1) |
| E | Melee (R3 click) |
| G | Super Ability (L1) |
| F | Interact (R2) |
| Tab | Map (Touchpad) |
| Esc | Menu (Options) |
| 1 / 2 / 3 / 4 | D-Pad Up / Down / Left / Right |
| **F3** | **Toggle mouse capture** |

---

## Tuning Sensitivity

Edit **config.json** — changes take effect next time you run the script.

```json
"sensitivity": {
    "x": 25.0,
    "y": 22.0,
    "acceleration": 1.0,
    "ads_multiplier": 0.4
}
```

| Setting | What it does |
|---------|-------------|
| `x` / `y` | Pixels of mouse movement per update interval that equals full stick deflection. **Lower = more sensitive. Higher = less sensitive.** Start here when tuning. |
| `acceleration` | Power curve multiplier. `1.0` = linear (recommended to start). `1.2` = large movements feel faster relative to small ones. |
| `ads_multiplier` | Sensitivity multiplier when aiming down sights (right-click held). `0.4` = 40% of normal speed. |

**Mouse DPI guide:**
- 800 DPI mouse: start with `x: 20, y: 18`
- 1600 DPI mouse: start with `x: 40, y: 36`
- 3200 DPI mouse: start with `x: 80, y: 72`

Tune from there to taste.

---

## Changing Key Bindings

Edit the `"bindings"` section in **config.json**.

**Key name format:**
- Regular keys: `"w"`, `"a"`, `"r"`, `"1"`, `"space"`, `"esc"`, `"tab"`
- Modifier keys: `"shift"`, `"ctrl"`, `"alt"`
- Function keys: `"f1"` through `"f12"`
- Mouse buttons: `"left_click"`, `"right_click"`, `"middle_click"`

**Available actions:**

| Action | Description |
|--------|-------------|
| `ls_up` `ls_down` `ls_left` `ls_right` | Left stick directions (movement) |
| `cross` `circle` `square` `triangle` | Face buttons |
| `l1` `r1` | Shoulder buttons |
| `l2` `r2` | Triggers (analog — fully pressed) |
| `l3` `r3` | Stick clicks |
| `dpad_up` `dpad_down` `dpad_left` `dpad_right` | D-pad |
| `options` `share` `touchpad` | PS4 system buttons |

Multiple keys can share the same action — the action stays active until all keys for it are released. This is how both `f` and `left_click` can both trigger `r2`.

---

## Lossless Scaling (frame generation + upscaling)

1. Buy and install [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) from Steam
2. Launch it
3. Set **Scale Type** to `LS1` (best quality) or `FSR` (lighter GPU load)
4. Enable **Frame Generation** (LSFG) — this takes 30fps → 60fps+
5. Click **Scale** then click the chiaki-ng window

Note: frame generation adds ~33ms of display latency (one source frame must be buffered to interpolate). Input latency to the PS4 is unaffected. You can toggle frame generation off in Lossless Scaling if you prefer lower display lag.

---

## Troubleshooting

**Virtual controller not detected by chiaki-ng**
- Make sure ViGEmBus is installed (see Step 1)
- Restart chiaki-ng after starting destiny1-mk.py
- In chiaki-ng Settings → Controller, check that it detects a DS4

**Movement is inverted**
- If moving forward makes you go backward, change `ls_up` and `ls_down` bindings in config.json

**Aim feels wrong**
- Tune sensitivity — see the DPI guide above
- If left/right is mirrored, add `"x": -25.0` (negative value)
- If up/down is inverted, add `"y": -22.0` (negative value)

**Input lag**
- Use wired ethernet on both PC and PS4
- In chiaki-ng settings, set codec to H.264 (lower decode latency than H.265 on most PCs)
- Turn off frame generation in Lossless Scaling if latency bothers you

**chiaki-ng shows black screen or disconnects**
- Make sure Remote Play is enabled on PS4 (see Step 3)
- Try connecting PS4 and PC to the same router via ethernet
- Check PS4 Settings → Remote Play → Add Device to confirm PC is registered

---

## Sharing with friends

Give them this whole folder. They need to:
1. Have a PS4 with Destiny 1 and a PSN account in your fireteam/party
2. Follow the installation steps above with **their own PS4**
3. Run `setup.bat`, then `run.bat`

Each person streams from their own PS4. You all play on Bungie's servers together normally — this tool just changes how each person's input and display works on their end.
