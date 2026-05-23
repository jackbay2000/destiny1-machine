# destiny1-mk

Play Destiny 1 on PC with mouse and keyboard.

This tool creates a virtual Xbox 360 controller on your PC and translates your mouse and keyboard into controller input. **chiaki-ng** (an open-source PS4 Remote Play client) streams the game from your PS4 to your PC and forwards the virtual controller inputs. Your PS4 stays connected to Bungie's live servers the whole time — nothing changes on the PS4 side.

For upscaling and frame generation (30fps → 60fps+), layer **Lossless Scaling** on top.

---

## How it works

```
Bungie Servers
      ↕
   Your PS4  ──── video stream ────▶  chiaki-ng window
      ↑                                      ↓
 fake controller ◀─────────────  destiny1-mk.py
                                 (your mouse + keyboard)
                                             ↓
                                    Lossless Scaling
                                    (upscale + frame gen)
                                             ↓
                                    your monitor
```

---

## Requirements

- Windows 10 or 11 (or Linux — see the Linux section below)
- Python 3.10+
- A **dedicated GPU (Nvidia or AMD)** — Intel integrated graphics has driver compatibility issues with chiaki-ng
- A PS4 with Destiny 1, connected to your local network
- Both PC and PS4 on **wired ethernet** (strongly recommended — WiFi adds latency)
- [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) — ~$7 on Steam (optional but recommended for frame gen)

chiaki-ng and the ViGEmBus driver are downloaded and installed automatically by setup.bat.

---

## Installation

### Step 1 — Run setup

Double-click **setup.bat**. It will automatically:
- Install Python dependencies
- Download and install the **ViGEmBus** virtual gamepad driver (click through the installer when it opens)
- Download and install **chiaki-ng** (click through the installer when it opens)

This requires an internet connection and takes a couple of minutes.

---

## Linux Installation

For Linux users, use **setup-linux.sh** and **run-linux.sh** instead of the .bat files.

### Requirements (Linux)
- Python 3.10+ with pip3
- A dedicated GPU (Nvidia or AMD) — same requirement as Windows
- X11 display server (Wayland is partially supported but cursor hiding and focus detection may not work)

### Step 1 — Make scripts executable

After copying this folder to your Linux machine, run once in a terminal:

```bash
chmod +x setup-linux.sh run-linux.sh
```

If you copied from Windows and get errors like `bad interpreter` or `\r: command not found`, the files have Windows line endings. Fix with:

```bash
sed -i 's/\r//' setup-linux.sh run-linux.sh
```

### Step 2 — Run setup

```bash
./setup-linux.sh
```

This will install Python dependencies (including `python-xlib`), configure the `uinput` kernel module (the Linux equivalent of ViGEmBus — no separate driver install needed), and download the chiaki-ng Linux AppImage.

If pip fails with `externally-managed-environment`, add `--break-system-packages` to the pip3 commands, or run inside a virtualenv.

After setup, you may need to **log out and back in** for the `input` group change to take effect (required for the virtual controller to work).

### Step 3 — Register your PS4 with chiaki-ng

Same as Windows — run the downloaded chiaki-ng AppImage:

```bash
./downloads/chiaki-ng-*.AppImage
```

Register your PS4 as described in the Windows Steps 2–4 below.

### Step 4 — Run

```bash
./run-linux.sh
```

Then open chiaki-ng, start the stream, and press **F3** to capture the mouse.

### Linux notes
- Cursor hiding requires X11 XFixes extension (available on all major desktop distros). On Wayland, cursor hiding is skipped but everything else works.
- Focus detection (auto-release when you alt-tab) requires X11. On Wayland this is skipped and the bridge forwards input at all times while capture is active.
- Virtual controller uses the `uinput` kernel module. No reboot needed, but you must log out/in once after setup so the `input` group takes effect.

---

### Step 2 — Enable Remote Play on your PS4

On your PS4:
- Settings → Remote Play Connection Settings → **Enable Remote Play** ✓
- Settings → Account Management → **Activate as Your Primary PS4** ✓
- Settings → Power Save Settings → Set Features Available in Rest Mode → check **Stay Connected to the Internet** and **Enable Turning On PS4 from Network**

### Step 3 — Register your PC with chiaki-ng

1. Open chiaki-ng from the Start menu
2. Your PS4 should appear automatically. If not, click **Add Console** and enter your PS4's IP address
3. Double-click your PS4 — it will ask you to log in via PSN to get a registration code
4. Complete the PSN login in the browser window that opens, then paste the redirect URL back into chiaki-ng
5. chiaki-ng will remember your PS4. You only do this once.

### Step 4 — Disable chiaki-ng keyboard input (important)

destiny1-mk handles all input via the virtual controller. If chiaki-ng also maps keyboard input, you'll get conflicts.

In chiaki-ng: **Settings → Keys → uncheck "Use keyboard as controller"** (or any option that maps keyboard keys to controller input).

### Step 5 — Configure chiaki-ng for best performance

See the **chiaki-ng Settings** section below for the full recommended configuration.

---

## chiaki-ng Settings

Open chiaki-ng → **Settings**. The settings below are the confirmed working configuration.

### General (Settings → General)

| Setting | Value |
|---------|-------|
| Action On Disconnect | Ask |
| Action On Suspend | Do Nothing |
| Audio/Video | Audio and Video Enabled |
| Stream Menu Shortcut | Enabled — combo: **L1 + R1 + L3 + R3** |

### Stream (Settings → Stream)

| Setting | Value | Notes |
|---------|-------|-------|
| Settings for | **PS4** | Must match your console. PS4 mode locks to H.264 automatically, which is correct — the PS4 only supports H.264 for Remote Play. |
| Resolution | **1080p** | Use 720p if your PS4 is a base model and you see performance issues. |
| FPS | **60** | |
| Local Bitrate | **15 Mbps** | Good balance for wired ethernet. Go higher (up to 50 Mbps) if you want less compression on a strong local network. |
| Remote Bitrate | **100 Mbps** | Can be set high for local network — the PS4 will cap at what it can actually send. Reduce to 8–12 Mbps if playing over the internet. |

### Video (Settings → Video)

**Hardware Decoder** — pick based on your GPU:

| GPU | Hardware Decoder | Notes |
|-----|-----------------|-------|
| **Nvidia** | **CUDA** | Uses NVDEC hardware; most stable on Nvidia. If you see tearing or crashes, try D3D11VA instead. |
| **AMD** | **D3D11VA** | Most stable path on AMD. |
| Fallback (either) | D3D11VA | Universal fallback if other options cause issues. |

| Setting | Confirmed value | If you have problems |
|---------|----------------|----------------------|
| Zero-Copy | **On** | Turn off if you see visual glitches or crashes — adds a CPU round-trip but is more compatible. |
| Window Type | **Fullscreen** | Use a bordered window (Normal) if F3 capture behaves strangely or alt-tab is unreliable. |
| Hide Cursor during Stream | **On** | |
| Vertical Sync | **On** | Turn off only if you need the absolute minimum display latency and can tolerate screen tearing. |
| Render Preset | **Fast** | Fast reduces GPU post-processing overhead and lowers latency. Use High Quality if you notice a soft or blurry image — the GPU cost is small on modern hardware. |
| Placebo Queue Depth | **2 frames** | Reduce to 1 for lower latency; increase to 3 if you see stuttering on a congested network. |
| Renderer Backend | **Vulkan** | Switch to OpenGL if Vulkan causes crashes or a black screen on your system. |

### Audio/Wifi (Settings → Audio/Wifi)

Leave everything at defaults. The notable ones:

| Setting | Value | Notes |
|---------|-------|-------|
| Audio Buffer Size | **50 ms** | Increase to 100 ms if you hear audio crackling or dropouts. |
| Weak Wifi Notification | ≥ 3% dropped packets | Lower this if you want earlier warning of a bad connection. |

### Keys (Settings → Keys)

| Setting | Value | Why |
|---------|-------|-----|
| **Keyboard as controller** | **Unchecked** | **Critical.** If this is enabled, chiaki-ng will also map your keyboard directly to PS4 buttons, creating conflicts with destiny1-mk. Leave it off. |
| Enable Mouse Touchpad | **Checked** | Lets the mouse emulate the touchpad — used internally by the virtual controller bridge. |

### Controllers (Settings → Controllers)

| Setting | Value | Notes |
|---------|-------|-------|
| Background Controller Events | **Checked** | **Important.** Tells chiaki-ng to process virtual controller input even when it isn't the focused window. Without this, inputs may be dropped if you briefly alt-tab. |
| Dpad Touchpad Emulation | Checked | Allows d-pad combos to emulate touchpad swipes. Fine to leave on. |

### Network (biggest impact on latency and stability)

**Both PC and PS4 should be on wired ethernet.** This is the single largest improvement you can make — more impactful than any software setting.

| Connection | Typical latency | Stream resets |
|-----------|----------------|---------------|
| Both wired | Lowest, consistent | Rare to none |
| PC wired, PS4 WiFi | +20–40ms variable | Frequent |
| Both WiFi | High and unpredictable | Very frequent |

WiFi packet loss is the primary cause of stream resets (the brief freeze and image jump). Ethernet eliminates this almost entirely.

---

## Running

**Every session:**

1. Turn on your PS4 and start Destiny 1
2. Double-click **run.bat** and wait for it to show the waiting message
3. Open chiaki-ng and double-click your PS4 to start the stream
4. Once you can see the game, click the chiaki-ng window to give it focus
5. Press **F3** to capture the mouse — cursor disappears and you're in-game
6. *(Optional)* Alt-Tab to Lossless Scaling and enable it on the chiaki-ng window

To release the mouse at any time (e.g. to alt-tab), press **F3** again.

To disconnect, press LCTRL + Q

---

## Default Key Bindings

| Key | Action |
|-----|--------|
| W A S D | Move (left stick) |
| Mouse | Aim (right stick) |
| Left Click | Shoot (R2) |
| Right Click | Aim Down Sights (L2) |
| Mouse4 (back button) | Melee (R3 click) |
| Space | Jump (Cross) |
| Shift | Sprint (L3 click) |
| Left Ctrl | Crouch (Circle) |
| R | Reload (Square) |
| 1 | Swap Weapon (Triangle) |
| E | Grenade (R1) |
| G | Super Ability (L1) |
| Q | L1 + R1 simultaneously |
| F | Interact (R2) |
| Tab | Map (Touchpad) |
| Esc | Menu (Options) |
| 2 / 3 / 4 / 5 | D-Pad Up / Down / Left / Right |
| **F3** | **Toggle mouse capture** |

Edit these keybinds in config.json


---

## Tuning Sensitivity

Edit **config.json** — changes take effect next time you run the script.

```json
"sensitivity": {
    "x": 1.0,
    "y": 1.0,
    "acceleration": 1.0,
    "ads_multiplier": 0.4
}
```

| Setting | What it does |
|---------|-------------|
| `x` / `y` | Look sensitivity multiplier. `1.0` = default. **Higher = faster. Lower = slower.** Tune these first. |
| `acceleration` | Power curve on mouse movement. `1.0` = linear. `1.2` = small movements stay slow, large movements get faster. |
| `ads_multiplier` | Sensitivity multiplier while aiming down sights (right-click held). `0.4` = 40% of normal speed. |

**Suggested starting points by DPI:**
- 800 DPI → `x: 1.5, y: 1.5`
- 1600 DPI → `x: 1.0, y: 1.0`
- 3200 DPI → `x: 0.5, y: 0.5`

Tune from there to taste.

---

## Changing Key Bindings

Edit the `"bindings"` section in **config.json**.

**Key name format:**
- Regular keys: `"w"`, `"a"`, `"r"`, `"1"`, `"space"`, `"esc"`, `"tab"`
- Modifier keys: `"shift"`, `"ctrl"`, `"alt"`
- Function keys: `"f1"` through `"f12"`
- Mouse buttons: `"left_click"`, `"right_click"`, `"middle_click"`, `"mouse4"`, `"mouse5"`

**To bind a key to multiple actions at once**, use a list:
```json
"q": ["l1", "r1"]
```

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

Multiple keys can share the same action — the action stays active until all keys for it are released.

---

## Lossless Scaling (frame generation + upscaling)

1. Buy and install [Lossless Scaling](https://store.steampowered.com/app/993090/Lossless_Scaling/) from Steam
2. Launch it
3. Set **Scale Type** to `LS1` (best quality) or `FSR` (lighter GPU load)
4. Enable **Frame Generation** (LSFG) — this takes 30fps → 60fps+
5. Click **Scale** then click the chiaki-ng window

Note: frame generation adds ~33ms of display latency. Input latency to the PS4 is unaffected. You can toggle it off in Lossless Scaling if you prefer lower display lag.

---

## Troubleshooting

**chiaki-ng crashes on launch or when connecting**
- This is almost always a GPU driver issue. Make sure you have a dedicated Nvidia or AMD GPU and up-to-date drivers. Intel integrated graphics has known compatibility issues.

**Virtual controller not detected by chiaki-ng**
- Make sure run.bat is running **before** you open chiaki-ng
- Re-run setup.bat to ensure ViGEmBus installed correctly

**Movement is inverted**
- If moving forward makes you go backward, swap `ls_up` and `ls_down` in config.json

**Aim feels wrong**
- Tune sensitivity — see the DPI guide above
- If left/right is mirrored, use a negative value e.g. `"x": -25.0`
- If up/down is inverted, use a negative value e.g. `"y": -22.0`

**Input lag or screen tearing**
- Follow the chiaki-ng Settings section above — hardware decoder, renderer, and codec choices have the biggest impact
- Switch both PC and PS4 to wired ethernet — this is the single largest improvement
- Turn off frame generation in Lossless Scaling if latency bothers you

**chiaki-ng can't find your PS4**
- Make sure Remote Play is enabled on PS4 (see Step 2)
- Make sure both devices are on the same network
- Try restarting your PS4

---

## Sharing with friends

Give them this whole folder. They need to:
1. Have a PS4 with Destiny 1 and a PSN account in your fireteam/party
2. Follow the installation steps above with **their own PS4**
3. **Windows:** Run `setup.bat`, then `run.bat`
4. **Linux:** Run `./setup-linux.sh`, then `./run-linux.sh`

Each person streams from their own PS4. You all play on Bungie's servers together normally — this tool just changes how each person's input and display works on their end.
